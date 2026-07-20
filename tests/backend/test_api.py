from fastapi.testclient import TestClient

from api.index import create_app


class FakeRepository:
    def __init__(self):
        self.projects = [
            {"ro": "Delhi", "piu": "Dwarka", "project_name": "NH-48 Package", "upc": "UPC-001"},
            {"ro": "Delhi", "piu": "Gurugram", "project_name": "SPR Project", "upc": "UPC-002"},
            {"ro": "Mumbai", "piu": "Thane", "project_name": "Thane Bypass", "upc": "UPC-003"},
        ]
        self.master = {
            "ROB-001": {"proposal_id": "ROB-001", "state": "Delhi"},
            "RUB-002": {"proposal_id": "RUB-002", "state": "Haryana"},
            "ROB-003": {"proposal_id": "ROB-003", "state": "Maharashtra"},
        }
        self.existing = {("RUB-002", "UPC-001")}
        self.inserted = []

    def list_ros(self):
        return sorted({p["ro"] for p in self.projects})

    def list_pius(self, ro):
        return sorted({p["piu"] for p in self.projects if p["ro"] == ro})

    def list_projects(self, ro, piu):
        return [p for p in self.projects if p["ro"] == ro and p["piu"] == piu]

    def get_project(self, upc):
        return next((p for p in self.projects if p["upc"] == upc), None)

    def get_master_records(self, proposal_ids):
        return {pid: self.master[pid] for pid in proposal_ids if pid in self.master}

    def get_existing_mappings(self, proposal_ids):
        return {pid for pid in proposal_ids if any(existing_id == pid for existing_id, _ in self.existing)}

    def insert_mappings(self, rows):
        self.inserted.extend(rows)


def make_client():
    repository = FakeRepository()
    return TestClient(create_app(repository)), repository


def test_hierarchy_endpoints_filter_projects():
    client, _ = make_client()
    assert client.get("/api/ros").json() == ["Delhi", "Mumbai"]
    assert client.get("/api/pius", params={"ro": "Delhi"}).json() == ["Dwarka", "Gurugram"]
    assert client.get("/api/projects", params={"ro": "Delhi", "piu": "Dwarka"}).json() == [
        {"ro": "Delhi", "piu": "Dwarka", "project_name": "NH-48 Package", "upc": "UPC-001"}
    ]


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
