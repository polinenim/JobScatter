from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.job_repository import JobRepository

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobSourceInfo(BaseModel):
    source: str
    source_job_id: str
    source_url: str
    application_url: str


class CanonicalJobListItem(BaseModel):
    job_id: UUID
    company: str
    title: str
    description: str
    locations: list[str] | None = None
    workplace_type: str | None = None
    country: str | None = None
    employment_type: str | None = None
    opportunity_type: str | None = None
    posted_at: datetime | None = None
    updated_at: datetime | None = None
    application_url: str
    source_url: str
    status: str
    source_records: list[JobSourceInfo]
    it_field: str | None = None
    experience_suitability: str | None = None


class PaginatedJobs(BaseModel):
    items: list[CanonicalJobListItem]
    page: int
    page_size: int
    total: int


@router.get("", response_model=PaginatedJobs)
def list_jobs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    search: str | None = None,
    it_field: str | None = None,
    opportunity_type: str | None = None,
    experience_suitability: str | None = None,
    location: str | None = None,
    workplace_type: str | None = None,
    include_inactive: bool = False,
) -> PaginatedJobs:
    items, total = JobRepository().list_jobs(
        page=page,
        page_size=page_size,
        search=search,
        it_field=it_field,
        opportunity_type=opportunity_type,
        experience_suitability=experience_suitability,
        location=location,
        workplace_type=workplace_type,
        include_inactive=include_inactive,
    )
    return PaginatedJobs(
        items=[CanonicalJobListItem.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )
