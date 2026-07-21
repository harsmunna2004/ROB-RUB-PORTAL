from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Project(BaseModel):
    ro: str
    piu: str
    project_name: str
    upc: str


class ProjectSummary(Project):
    certification_status: Literal["pending", "certified"] = "pending"
    certified_at: datetime | None = None
    mapped_rob_rub_count: int = 0


class MappedRobRub(BaseModel):
    proposal_id: str
    name_of_work: str | None = None
    district: str | None = None
    state: str | None = None
    date_mapped: datetime


class ProjectDetail(ProjectSummary):
    mappings: list[MappedRobRub] = []


class CertificationRequest(BaseModel):
    status: Literal["pending", "certified"]


class RobRubRecord(BaseModel):
    proposal_id: str
    proposal_date: date | None = None
    name_of_work: str | None = None
    division_railway: str | None = None
    district: str | None = None
    state: str | None = None
    associated_road_authority: str | None = None
    category_of_road: str | None = None
    name_of_road: str | None = None
    mapping_status: Literal["mapped", "pending"]
    mapped_upc: str | None = None
    mapped_project_name: str | None = None


class RobRubPage(BaseModel):
    items: list[RobRubRecord]
    page: int
    page_size: int
    total: int


class RobRubFilters(BaseModel):
    states: list[str]
    districts: list[str]
    categories: list[str]
    divisions: list[str]


class DashboardTotals(BaseModel):
    projects_total: int
    projects_certified: int
    projects_pending: int
    rob_rubs_total: int
    rob_rubs_mapped: int
    rob_rubs_pending: int


class DashboardRow(DashboardTotals):
    ro: str
    piu: str | None = None


class DashboardResponse(BaseModel):
    totals: DashboardTotals
    ro_summary: list[DashboardRow]
    piu_summary: list[DashboardRow]


class MappingRequest(BaseModel):
    upc: str = Field(min_length=1)
    proposal_ids: list[str] = Field(min_length=1, max_length=100)

    @field_validator("upc")
    @classmethod
    def clean_upc(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("UPC cannot be blank.")
        return cleaned


class MappingResult(BaseModel):
    proposal_id: str
    status: Literal["saved", "invalid", "duplicate_in_request", "already_mapped"]
    message: str


class MappingResponse(BaseModel):
    results: list[MappingResult]
