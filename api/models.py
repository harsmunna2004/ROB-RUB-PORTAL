from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Project(BaseModel):
    ro: str
    piu: str
    project_name: str
    upc: str


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
