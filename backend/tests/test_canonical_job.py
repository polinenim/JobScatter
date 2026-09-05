from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.canonical_job import CanonicalJob, normalize_ingestion_record
from app.ingestion_contract import JobIngestionRecord


BASE_RECORD = {
    "source": "greenhouse",
    "source_job_id": "123",
    "company": "  Example Co  ",
    "title": "  Senior Engineer  ",
    "description": "  Build reliable software.  ",
    "application_url": " HTTPS://EXAMPLE.COM/jobs/123 ",
    "source_url": " https://EXAMPLE.COM/jobs/123 ",
    "raw_source_data": {"id": 123, "title": "Senior Engineer"},
    "discovered_at": datetime(2026, 9, 5, 12, tzinfo=timezone(timedelta(hours=-4))),
}


def test_normalizer_cleans_supported_values_and_preserves_source_data():
    ingestion = JobIngestionRecord(
        **BASE_RECORD,
        responsibilities="  Design systems. ",
        locations=[" New York ", "New York", " Remote ", ""],
        country=" US ",
        employment_type=" Full-Time ",
        opportunity_type=" Employment ",
        posted_at="2026-09-01T10:00:00-04:00",
        updated_at="2026-09-02T10:00:00-04:00",
        salary={"currency": "USD", "min": 100000},
        workplace_type="hybrid",
    )

    canonical = normalize_ingestion_record(ingestion)

    assert isinstance(canonical, CanonicalJob)
    assert canonical.title == "Senior Engineer"
    assert canonical.company == "Example Co"
    assert canonical.description == "Build reliable software."
    assert canonical.responsibilities == "Design systems."
    assert canonical.locations == ["New York", "Remote"]
    assert canonical.country == "US"
    assert canonical.employment_type == "full-time"
    assert canonical.opportunity_type == "employment"
    assert canonical.application_url == "https://example.com/jobs/123"
    assert canonical.source_url == "https://example.com/jobs/123"
    assert canonical.posted_at == datetime(2026, 9, 1, 14, tzinfo=timezone.utc)
    assert canonical.updated_at == datetime(2026, 9, 2, 14, tzinfo=timezone.utc)
    assert canonical.discovered_at == datetime(2026, 9, 5, 16, tzinfo=timezone.utc)
    assert canonical.salary == {"currency": "USD", "min": 100000}
    assert canonical.raw_source_data == BASE_RECORD["raw_source_data"]


def test_normalizer_preserves_unknown_optional_values_as_none():
    ingestion = JobIngestionRecord(**BASE_RECORD)

    canonical = normalize_ingestion_record(ingestion)

    assert canonical.responsibilities is None
    assert canonical.locations is None
    assert canonical.workplace_type is None
    assert canonical.country is None
    assert canonical.employment_type is None
    assert canonical.opportunity_type is None
    assert canonical.posted_at is None
    assert canonical.updated_at is None
    assert canonical.salary is None


@pytest.mark.parametrize("field", ["title", "company", "description"])
def test_canonical_job_validates_required_fields(field: str):
    payload = dict(BASE_RECORD)
    payload[field] = ""

    with pytest.raises(ValidationError):
        normalize_ingestion_record(JobIngestionRecord(**payload))
