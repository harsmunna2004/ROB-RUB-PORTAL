from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from api.models import MappingRequest, MappingResponse, MappingResult, Project
from api.repository import Repository, create_repository


def create_app(repository: Repository | None = None) -> FastAPI:
    app = FastAPI(title="ROB/RUB Mapping API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST"],
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

    @app.get("/api/projects", response_model=list[Project])
    def list_projects(
        ro: str = Query(min_length=1), piu: str = Query(min_length=1)
    ):
        return repo().list_projects(ro.strip(), piu.strip())

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
                rows.append({
                    "proposal_id": proposal_id,
                    "upc": project["upc"],
                    "project_name": project["project_name"],
                    "piu": project["piu"],
                    "regional_office": project["ro"],
                    "state": master[proposal_id].get("state"),
                })
                results.append(MappingResult(
                    proposal_id=proposal_id,
                    status="saved",
                    message="Mapping saved successfully.",
                ))
            seen.add(proposal_id)

        repository_instance.insert_mappings(rows)
        return MappingResponse(results=results)

    return app


app = create_app()
