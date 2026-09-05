from datetime import datetime, timezone
from typing import Any, Literal
from urllib.parse import urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field

from app.ingestion_contract import JobIngestionRecord


class CanonicalJob(BaseModel):
    """Source-independent job representation before deduplication or ranking."""

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


def normalize_ingestion_record(record: JobIngestionRecord) -> CanonicalJob:
    return CanonicalJob(
        source=_required_text(record.source),
        source_job_id=_required_text(record.source_job_id),
        company=_required_text(record.company),
        title=_required_text(record.title),
        description=_required_text(record.description),
        responsibilities=_optional_text(record.responsibilities),
        locations=_normalize_locations(record.locations),
        workplace_type=record.workplace_type,
        country=_optional_text(record.country),
        employment_type=_normalize_field(record.employment_type),
        opportunity_type=_normalize_field(record.opportunity_type),
        posted_at=_normalize_timestamp(record.posted_at),
        updated_at=_normalize_timestamp(record.updated_at),
        salary=record.salary,
        application_url=_normalize_url(record.application_url),
        source_url=_normalize_url(record.source_url),
        raw_source_data=record.raw_source_data,
        discovered_at=_normalize_timestamp(record.discovered_at),
    )


def _required_text(value: str) -> str:
    return value.strip()


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _normalize_field(value: str | None) -> str | None:
    cleaned = _optional_text(value)
    return cleaned.casefold() if cleaned is not None else None


def _normalize_locations(locations: list[str] | None) -> list[str] | None:
    if locations is None:
        return None

    normalized = list(dict.fromkeys(
        location.strip() for location in locations if location.strip()
    ))
    return normalized or None


def _normalize_url(value: str) -> str:
    cleaned = value.strip()
    try:
        parsed = urlsplit(cleaned)
    except ValueError:
        return cleaned

    if not parsed.scheme or not parsed.netloc:
        return cleaned
    return urlunsplit(
        (
            parsed.scheme.casefold(),
            parsed.netloc.casefold(),
            parsed.path,
            parsed.query,
            parsed.fragment,
        )
    )


def _normalize_timestamp(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is None or value.utcoffset() is None:
        return value
    return value.astimezone(timezone.utc)
