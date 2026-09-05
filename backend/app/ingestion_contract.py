from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class JobIngestionRecord(BaseModel):
    """Source-adapter output before canonical job processing begins."""

    model_config = ConfigDict(extra="forbid")

    source: str = Field(min_length=1)
    source_job_id: str = Field(min_length=1)
    company: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    responsibilities: str | None = None
    locations: list[str] | None = None
    workplace_type: Literal["remote", "hybrid", "on-site"] | None = None
    country: str | None = None
    employment_type: str | None = None
    opportunity_type: str | None = None
    posted_at: datetime | None = None
    updated_at: datetime | None = None
    salary: dict[str, Any] | None = None
    application_url: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    raw_source_data: Any
    discovered_at: datetime
