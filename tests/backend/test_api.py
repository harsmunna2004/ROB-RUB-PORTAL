from fastapi.testclient import TestClient

from backend.app import create_app


class FakeRepository:
    def __init__(self):
        self.projects = [
            {"ro": "Delhi", "piu": "Dwarka", "project_name": "NH-48 Package", "upc": "UPC-001"},
            {"ro": "Delhi", "piu": "Gurugram", "project_name": "SPR Project", "upc": "UPC-002"},
            {"ro": "Mumbai", "piu": "Thane", "project_name": "Thane Bypass", "upc": "UPC-003"},
        ]
        self.master = {
            "ROB-001": {"proposal_id": "ROB-001", "state": "Delhi", "district": "New Delhi", "name_of_work": "Delhi ROB"},
            "RUB-002": {"proposal_id": "RUB-002", "state": "Haryana", "district": "Gurugram", "name_of_work": "Gurugram RUB"},
            "ROB-003": {"proposal_id": "ROB-003", "state": "Maharashtra", "district": "Thane", "name_of_work": "Thane ROB"},
        }
        self.existing = {("RUB-002", "UPC-001")}
        self.inserted = []
        self.mappings = [
            {"proposal_id": "RUB-002", "upc": "UPC-001", "date_mapped": "2026-07-20T00:00:00Z"}
        ]

    def list_ros(self):
        return sorted({p["ro"] for p in self.projects})

    def list_pius(self, ro):
        return sorted({p["piu"] for p in self.projects if p["ro"] == ro})

    def list_projects(self, ro, piu):
        return [{**p, "certification_status": p.get("certification_status", "pending"),
                 "certified_at": p.get("certified_at"),
                 "mapped_rob_rub_count": sum(m["upc"] == p["upc"] for m in self.mappings)}
                for p in self.projects if p["ro"] == ro and p["piu"] == piu]

    def get_project(self, upc):
        return next((p for p in self.projects if p["upc"] == upc), None)

    def get_master_records(self, proposal_ids):
        return {pid: self.master[pid] for pid in proposal_ids if pid in self.master}

    def get_existing_mappings(self, proposal_ids):
        return {pid for pid in proposal_ids if any(existing_id == pid for existing_id, _ in self.existing)}

    def insert_mappings(self, rows):
        self.inserted.extend(rows)

    def get_project_detail(self, upc):
        project = self.get_project(upc)
        if not project:
            return None
        return {**project, "certification_status": project.get("certification_status", "pending"),
                "certified_at": project.get("certified_at"),
                "mapped_rob_rub_count": sum(m["upc"] == upc for m in self.mappings),
                "mappings": []}

    def set_certification(self, upc, status):
        project = self.get_project(upc)
        if not project:
            return False
        project["certification_status"] = status
        project["certified_at"] = "2026-07-21T00:00:00Z" if status == "certified" else None
        return True

    def list_rob_rubs(self, page, page_size, search, state, district, category, division, mapping_status):
        mapped = {m["proposal_id"]: m for m in self.mappings}
        rows = [{**record, "mapping_status": "mapped" if pid in mapped else "pending",
                 "mapped_upc": mapped.get(pid, {}).get("upc"), "mapped_project_name": None}
                for pid, record in self.master.items()]
        if search:
            rows = [r for r in rows if search.casefold() in " ".join(str(v) for v in r.values()).casefold()]
        if state:
            rows = [r for r in rows if r.get("state") == state]
        if district:
            rows = [r for r in rows if r.get("district") == district]
        if mapping_status != "all":
            rows = [r for r in rows if r["mapping_status"] == mapping_status]
        start = (page - 1) * page_size
        return {"items": rows[start:start + page_size], "page": page, "page_size": page_size, "total": len(rows)}

    def get_rob_rub_filters(self):
        return {"states": ["Delhi", "Haryana", "Maharashtra"],
                "districts": ["Gurugram", "New Delhi", "Thane"],
                "categories": [], "divisions": []}

    def get_dashboard(self, ro="", piu=""):
        projects = [p for p in self.projects if (not ro or p["ro"] == ro) and (not piu or p["piu"] == piu)]
        certified = sum(p.get("certification_status") == "certified" for p in projects)
        mapped = sum(m["upc"] in {p["upc"] for p in projects} for m in self.mappings)
        totals = {"projects_total": len(projects), "projects_certified": certified,
                  "projects_pending": len(projects) - certified, "rob_rubs_total": len(self.master),
                  "rob_rubs_mapped": mapped, "rob_rubs_pending": len(self.master) - mapped}
        rows = [{**totals, "ro": p["ro"], "piu": p["piu"]} for p in projects]
        return {"totals": totals, "ro_summary": [], "piu_summary": rows}


def make_client():
    repository = FakeRepository()
    return TestClient(create_app(repository)), repository


def test_hierarchy_endpoints_filter_projects():
    client, _ = make_client()
    assert client.get("/api/ros").json() == ["Delhi", "Mumbai"]
    assert client.get("/api/pius", params={"ro": "Delhi"}).json() == ["Dwarka", "Gurugram"]
    assert client.get("/api/projects", params={"ro": "Delhi", "piu": "Dwarka"}).json() == [
        {"ro": "Delhi", "piu": "Dwarka", "project_name": "NH-48 Package", "upc": "UPC-001",
         "certification_status": "pending", "certified_at": None, "mapped_rob_rub_count": 1}
    ]


def test_project_can_be_certified_without_mappings_and_reopened():
    client, _ = make_client()
    detail = client.get("/api/projects", params={"upc": "UPC-002"})
    assert detail.status_code == 200
    certified = client.patch("/api/projects", params={"upc": "UPC-002"}, json={"status": "certified"})
    assert certified.status_code == 200
    assert certified.json()["certification_status"] == "certified"
    assert certified.json()["certified_at"] is not None
    reopened = client.patch("/api/projects", params={"upc": "UPC-002"}, json={"status": "pending"})
    assert reopened.json()["certification_status"] == "pending"
    assert reopened.json()["certified_at"] is None


def test_rob_rub_register_search_filter_and_pagination():
    client, _ = make_client()
    searched = client.get("/api/rob-rubs", params={"search": "Gurugram"}).json()
    assert searched["total"] == 1
    assert searched["items"][0]["proposal_id"] == "RUB-002"
    pending = client.get("/api/rob-rubs", params={"mapping_status": "pending", "page_size": 1}).json()
    assert pending["total"] == 2
    assert len(pending["items"]) == 1


def test_dashboard_and_csv_endpoints():
    client, _ = make_client()
    dashboard = client.get("/api/dashboard").json()
    assert dashboard["totals"]["projects_total"] == 3
    assert dashboard["totals"]["rob_rubs_mapped"] == 1
    csv_response = client.get("/api/dashboard.csv")
    assert csv_response.status_code == 200
    assert csv_response.headers["content-type"].startswith("text/csv")
    assert "RO,PIU,Projects Total" in csv_response.text


def test_one_project_accepts_multiple_valid_rob_rub_ids():
    client, repository = make_client()
    response = client.post("/api/mappings", json={"upc": "UPC-003", "proposal_ids": ["ROB-001", "ROB-003"]})
    assert response.status_code == 200
    assert [item["status"] for item in response.json()["results"]] == ["saved", "saved"]
    assert len(repository.inserted) == 2
    assert {row["upc"] for row in repository.inserted} == {"UPC-003"}


def test_mapping_returns_per_id_invalid_duplicate_and_existing_results():
    client, repository = make_client()
    response = client.post(
        "/api/mappings",
        json={"upc": "UPC-001", "proposal_ids": [" ROB-001 ", "BAD-999", "ROB-001", "RUB-002"]},
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert [(r["proposal_id"], r["status"]) for r in results] == [
        ("ROB-001", "saved"),
        ("BAD-999", "invalid"),
        ("ROB-001", "duplicate_in_request"),
        ("RUB-002", "already_mapped"),
    ]
    assert len(repository.inserted) == 1


def test_unknown_project_is_rejected():
    client, _ = make_client()
    response = client.post("/api/mappings", json={"upc": "MISSING", "proposal_ids": ["ROB-001"]})
    assert response.status_code == 404
    assert response.json()["detail"] == "Selected project was not found."


def test_proposal_id_cannot_be_mapped_to_a_different_project():
    client, repository = make_client()
    response = client.post(
        "/api/mappings",
        json={"upc": "UPC-003", "proposal_ids": ["RUB-002"]},
    )
    assert response.status_code == 200
    assert response.json()["results"][0]["status"] == "already_mapped"
    assert repository.inserted == []


def test_empty_proposal_id_list_is_rejected():
    client, _ = make_client()
    response = client.post("/api/mappings", json={"upc": "UPC-001", "proposal_ids": []})
    assert response.status_code == 422
