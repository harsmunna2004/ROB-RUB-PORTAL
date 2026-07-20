from typing import Protocol

from supabase import Client, create_client

from api.config import get_settings


class Repository(Protocol):
    def list_ros(self) -> list[str]: ...
    def list_pius(self, ro: str) -> list[str]: ...
    def list_projects(self, ro: str, piu: str) -> list[dict]: ...
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
        return self._fetch_all(
            self.client.table("projects")
            .select("ro,piu,project_name,upc")
            .eq("ro", ro)
            .eq("piu", piu)
            .order("project_name")
        )

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
            .select("proposal_id,state")
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
