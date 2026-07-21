import csv
from datetime import datetime, timezone
from io import StringIO
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend.models import (CertificationRequest, MappedRobRub, MappingRequest, MappingResponse,
                        MappingResult, ProjectDetail, ProjectHierarchy, ProjectSummary,
                        RobRubFilters, RobRubPage, DashboardResponse)
from backend.repository import Repository, create_repository


def create_app(repository: Repository | None = None) -> FastAPI:
    app = FastAPI(title="ROB/RUB Mapping API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["*"],
    )

    def repo() -> Repository:
        try:
            return repository or create_repository()
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail="The database service is not configured or is unavailable.",
            ) from exc

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/ros", response_model=list[str])
    def list_ros():
        return repo().list_ros()

    @app.get("/api/pius", response_model=list[str])
    def list_pius(ro: str = Query(min_length=1)):
        return repo().list_pius(ro.strip())

    @app.get("/api/projects", response_model=list[ProjectSummary] | ProjectDetail | ProjectHierarchy)
    def list_projects(ro: str = "", piu: str = "", upc: str = "", hierarchy: bool = False):
        if upc.strip():
            project = repo().get_project_detail(upc.strip())
            if not project:
                raise HTTPException(404, "Selected project was not found.")
            return project
        if hierarchy:
            return {"projects": repo().list_project_hierarchy()}
        if not ro.strip() or not piu.strip():
            raise HTTPException(422, "RO and PIU are required.")
        return repo().list_projects(ro.strip(), piu.strip())

    @app.patch("/api/projects", response_model=ProjectDetail)
    def update_certification(payload: CertificationRequest, upc: str = Query(min_length=1)):
        repository_instance = repo()
        if not repository_instance.set_certification(upc.strip(), payload.status):
            raise HTTPException(404, "Selected project was not found.")
        return repository_instance.get_project_detail(upc.strip())

    @app.get("/api/rob-rubs", response_model=RobRubPage)
    def list_rob_rubs(page: int = Query(1, ge=1),
                      page_size: int = Query(25, ge=1, le=100), search: str = "",
                      state: str = "", category: str = "",
                      division: str = "",
                      mapping_status: Literal["all", "mapped", "pending"] = "all"):
        return repo().list_rob_rubs(page, page_size, search.strip(), state.strip(),
                                    category.strip(), division.strip(),
                                    mapping_status)

    @app.get("/api/rob-rubs/filters", response_model=RobRubFilters)
    def rob_rub_filters():
        return repo().get_rob_rub_filters()

    @app.get("/api/dashboard", response_model=DashboardResponse)
    def dashboard(ro: str = "", piu: str = ""):
        return repo().get_dashboard(ro.strip(), piu.strip())

    @app.get("/api/dashboard.csv")
    def dashboard_csv(ro: str = "", piu: str = ""):
        data = repo().get_dashboard(ro.strip(), piu.strip())
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["RO", "PIU", "Projects Total", "Projects Certified",
                         "Projects Pending", "ROBs/RUBs Total", "ROBs/RUBs Mapped",
                         "ROBs/RUBs Pending"])
        for row in data["piu_summary"]:
            writer.writerow([row["ro"], row["piu"], row["projects_total"],
                             row["projects_certified"], row["projects_pending"],
                             row["rob_rubs_total"], row["rob_rubs_mapped"],
                             row["rob_rubs_pending"]])
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=rob-rub-dashboard.csv"})

    @app.post("/api/mappings", response_model=MappingResponse)
    def create_mappings(payload: MappingRequest):
        repository_instance = repo()
        project = repository_instance.get_project(payload.upc)
        if not project:
            raise HTTPException(404, "Selected project was not found.")

        cleaned_ids = [proposal_id.strip() for proposal_id in payload.proposal_ids]
        unique_nonempty_ids = list(dict.fromkeys(pid for pid in cleaned_ids if pid))
        master = repository_instance.get_master_records(unique_nonempty_ids)
        existing = repository_instance.get_existing_mappings(unique_nonempty_ids)
        seen: set[str] = set()
        rows: list[dict] = []
        results: list[MappingResult] = []
        saved_records: list[MappedRobRub] = []

        for proposal_id in cleaned_ids:
            if not proposal_id or proposal_id not in master:
                results.append(MappingResult(
                    proposal_id=proposal_id,
                    status="invalid",
                    message="This ROB/RUB ID does not exist in the master table.",
                ))
            elif proposal_id in seen:
                results.append(MappingResult(
                    proposal_id=proposal_id,
                    status="duplicate_in_request",
                    message="This ID was entered more than once.",
                ))
            elif proposal_id in existing:
                results.append(MappingResult(
                    proposal_id=proposal_id,
                    status="already_mapped",
                    message="This ID is already mapped to a project.",
                ))
            else:
                date_mapped = datetime.now(timezone.utc)
                row = {
                    "proposal_id": proposal_id,
                    "upc": project["upc"],
                    "project_name": project["project_name"],
                    "piu": project["piu"],
                    "regional_office": project["ro"],
                    "state": master[proposal_id].get("state"),
                    "date_mapped": date_mapped.isoformat(),
                }
                rows.append(row)
                saved_records.append(MappedRobRub(
                    **master[proposal_id], date_mapped=date_mapped
                ))
                results.append(MappingResult(
                    proposal_id=proposal_id,
                    status="saved",
                    message="Mapping saved successfully.",
                ))
            seen.add(proposal_id)

        repository_instance.insert_mappings(rows)
        return MappingResponse(results=results, saved_records=saved_records)

    return app


app = create_app()
