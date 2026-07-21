from collections import Counter
from datetime import datetime, timezone
from typing import Protocol

from supabase import Client, create_client

from backend.config import get_settings


class Repository(Protocol):
    def list_ros(self) -> list[str]: ...
    def list_pius(self, ro: str) -> list[str]: ...
    def list_projects(self, ro: str, piu: str) -> list[dict]: ...
    def list_project_hierarchy(self) -> list[dict]: ...
    def get_project_detail(self, upc: str) -> dict | None: ...
    def set_certification(self, upc: str, status: str) -> bool: ...
    def list_rob_rubs(self, page: int, page_size: int, search: str, state: str,
                      category: str, division: str,
                      mapping_status: str) -> dict: ...
    def get_rob_rub_filters(self) -> dict: ...
    def get_dashboard(self, ro: str = "", piu: str = "") -> dict: ...
    def get_project(self, upc: str) -> dict | None: ...
    def get_master_records(self, proposal_ids: list[str]) -> dict[str, dict]: ...
    def get_existing_mappings(self, proposal_ids: list[str]) -> set[str]: ...
    def insert_mappings(self, rows: list[dict]) -> None: ...


class SupabaseRepository:
    PAGE_SIZE = 1000

    def __init__(self, client: Client):
        self.client = client

    def _fetch_all(self, query) -> list[dict]:
        rows: list[dict] = []
        start = 0
        while True:
            page = (
                query.range(start, start + self.PAGE_SIZE - 1)
                .execute()
                .data
            )
            rows.extend(page)
            if len(page) < self.PAGE_SIZE:
                return rows
            start += self.PAGE_SIZE

    def list_ros(self) -> list[str]:
        rows = self._fetch_all(self.client.table("projects").select("ro"))
        return sorted({row["ro"] for row in rows if row.get("ro")})

    def list_pius(self, ro: str) -> list[str]:
        rows = self._fetch_all(
            self.client.table("projects").select("piu").eq("ro", ro)
        )
        return sorted({row["piu"] for row in rows if row.get("piu")})

    def list_projects(self, ro: str, piu: str) -> list[dict]:
        projects = self._fetch_all(
            self.client.table("projects")
            .select("ro,piu,project_name,upc,certification_status,certified_at")
            .eq("ro", ro)
            .eq("piu", piu)
            .order("project_name")
        )
        upcs = [project["upc"] for project in projects]
        mappings = [] if not upcs else self._fetch_all(
            self.client.table("rob_rub_project_mapping").select("upc").in_("upc", upcs)
        )
        counts = {upc: sum(row["upc"] == upc for row in mappings) for upc in upcs}
        return [{**project, "mapped_rob_rub_count": counts.get(project["upc"], 0)} for project in projects]

    def list_project_hierarchy(self) -> list[dict]:
        projects = self._fetch_all(
            self.client.table("projects")
            .select("ro,piu,project_name,upc,certification_status,certified_at")
            .order("project_name")
        )
        mappings = self._fetch_all(
            self.client.table("rob_rub_project_mapping").select("upc")
        )
        counts = Counter(row["upc"] for row in mappings if row.get("upc"))
        return [{**project, "mapped_rob_rub_count": counts[project["upc"]]}
                for project in projects]

    def get_project_detail(self, upc: str) -> dict | None:
        rows = (self.client.table("projects")
                .select("ro,piu,project_name,upc,certification_status,certified_at")
                .eq("upc", upc).limit(1).execute().data)
        if not rows:
            return None
        mappings = self._fetch_all(
            self.client.table("rob_rub_project_mapping")
            .select("proposal_id,date_mapped")
            .eq("upc", upc)
        )
        proposal_ids = [row["proposal_id"] for row in mappings]
        master_rows = [] if not proposal_ids else self._fetch_all(
            self.client.table("rob_rub_master").select("*").in_("proposal_id", proposal_ids)
        )
        master_by_id = {row["proposal_id"]: row for row in master_rows}
        cleaned = [{**row, **master_by_id.get(row["proposal_id"], {})} for row in mappings]
        return {**rows[0], "mapped_rob_rub_count": len(cleaned), "mappings": cleaned}

    def set_certification(self, upc: str, status: str) -> bool:
        values = {"certification_status": status,
                  "certified_at": datetime.now(timezone.utc).isoformat() if status == "certified" else None}
        return bool(self.client.table("projects").update(values).eq("upc", upc).execute().data)

    def _master_and_mappings(self):
        master = self._fetch_all(self.client.table("rob_rub_master").select("*"))
        mappings = self._fetch_all(
            self.client.table("rob_rub_project_mapping")
            .select("proposal_id,upc,project_name,regional_office,piu")
        )
        return master, mappings

    def list_rob_rubs(self, page, page_size, search, state, category,
                      division, mapping_status):
        master, mappings = self._master_and_mappings()
        by_proposal = {row["proposal_id"]: row for row in mappings}
        rows = []
        for record in master:
            mapping = by_proposal.get(record["proposal_id"])
            row = {**record,
                   "mapping_status": "mapped" if mapping else "pending",
                   "mapped_upc": mapping.get("upc") if mapping else None,
                   "mapped_project_name": mapping.get("project_name") if mapping else None}
            rows.append(row)
        if search:
            needle = search.casefold()
            rows = [row for row in rows if any(needle in str(value).casefold()
                    for value in row.values() if value is not None)]
        exact = (("state", state), ("category_of_road", category),
                 ("division_railway", division))
        for field, value in exact:
            if value:
                rows = [row for row in rows if row.get(field) == value]
        if mapping_status != "all":
            rows = [row for row in rows if row["mapping_status"] == mapping_status]
        rows.sort(key=lambda row: row["proposal_id"])
        start = (page - 1) * page_size
        return {"items": rows[start:start + page_size], "page": page,
                "page_size": page_size, "total": len(rows)}

    def get_rob_rub_filters(self):
        master, _ = self._master_and_mappings()
        def distinct(field):
            return sorted({row[field] for row in master if row.get(field)})
        return {"states": distinct("state"), "categories": distinct("category_of_road"),
                "divisions": distinct("division_railway")}

    @staticmethod
    def _dashboard_totals(projects, master_count, mapped_count):
        certified = sum(p.get("certification_status", "pending") == "certified" for p in projects)
        return {"projects_total": len(projects), "projects_certified": certified,
                "projects_pending": len(projects) - certified,
                "rob_rubs_total": master_count, "rob_rubs_mapped": mapped_count,
                "rob_rubs_pending": max(master_count - mapped_count, 0)}

    def get_dashboard(self, ro="", piu=""):
        projects = self._fetch_all(
            self.client.table("projects").select("upc,ro,piu,certification_status")
        )
        master, mappings = self._master_and_mappings()
        if ro:
            projects = [p for p in projects if p["ro"] == ro]
        if piu:
            projects = [p for p in projects if p["piu"] == piu]
        scoped_upcs = {p["upc"] for p in projects}
        scoped_mappings = [m for m in mappings if m["upc"] in scoped_upcs]
        overall_scope = not ro and not piu
        totals = self._dashboard_totals(
            projects, len(master) if overall_scope else len(scoped_mappings), len(scoped_mappings)
        )
        def grouped(key_fields):
            keys = sorted({tuple(p[field] for field in key_fields) for p in projects})
            result = []
            for key in keys:
                group_projects = [p for p in projects if tuple(p[field] for field in key_fields) == key]
                upcs = {p["upc"] for p in group_projects}
                mapped = sum(m["upc"] in upcs for m in mappings)
                row = self._dashboard_totals(group_projects, mapped, mapped)
                row.update({field: value for field, value in zip(key_fields, key)})
                if "piu" not in row:
                    row["piu"] = None
                result.append(row)
            return result
        return {"totals": totals, "ro_summary": grouped(("ro",)),
                "piu_summary": grouped(("ro", "piu"))}

    def get_project(self, upc: str) -> dict | None:
        rows = (
            self.client.table("projects")
            .select("ro,piu,project_name,upc")
            .eq("upc", upc)
            .limit(1)
            .execute()
            .data
        )
        return rows[0] if rows else None

    def get_master_records(self, proposal_ids: list[str]) -> dict[str, dict]:
        if not proposal_ids:
            return {}
        rows = (
            self.client.table("rob_rub_master")
            .select("proposal_id,proposal_date,name_of_work,division_railway,state,associated_road_authority,category_of_road,name_of_road")
            .in_("proposal_id", proposal_ids)
            .execute()
            .data
        )
        return {row["proposal_id"]: row for row in rows}

    def get_existing_mappings(self, proposal_ids: list[str]) -> set[str]:
        if not proposal_ids:
            return set()
        rows = (
            self.client.table("rob_rub_project_mapping")
            .select("proposal_id")
            .in_("proposal_id", proposal_ids)
            .execute()
            .data
        )
        return {row["proposal_id"] for row in rows}

    def insert_mappings(self, rows: list[dict]) -> None:
        if rows:
            self.client.table("rob_rub_project_mapping").insert(rows).execute()


def create_repository() -> SupabaseRepository:
    settings = get_settings()
    return SupabaseRepository(
        create_client(settings.supabase_url, settings.supabase_service_role_key)
    )
