from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.ingestion_contract import JobIngestionRecord


REQUIRED_FIELDS = {
    "source": "example_source",
    "source_job_id": "job-123",
    "company": "Example Co",
    "title": "Software Engineer",
    "description": "Build reliable software.",
    "application_url": "https://example.test/apply/job-123",
    "source_url": "https://example.test/jobs/job-123",
    "raw_source_data": {"id": "job-123", "title": "Software Engineer"},
    "discovered_at": datetime(2026, 9, 5, tzinfo=timezone.utc),
}


def test_contract_accepts_required_fields_with_optional_values_missing():
    record = JobIngestionRecord.model_validate(REQUIRED_FIELDS)

    assert record.source_job_id == "job-123"
    assert record.responsibilities is None
    assert record.locations is None
    assert record.workplace_type is None
    assert record.country is None
    assert record.employment_type is None
    assert record.opportunity_type is None
    assert record.posted_at is None
    assert record.updated_at is None
    assert record.salary is None


def test_contract_preserves_optional_values_and_raw_source_data():
    raw_source_data = {"id": "job-123", "salary": {"min": 100000}}
    payload = {
        **REQUIRED_FIELDS,
        "responsibilities": "Design and test systems.",
        "locations": ["New York", "Remote"],
        "workplace_type": "hybrid",
        "country": "US",
        "employment_type": "full-time",
        "opportunity_type": "employment",
        "posted_at": "2026-09-01T10:00:00Z",
        "updated_at": "2026-09-02T10:00:00Z",
        "salary": {"currency": "USD", "min": 100000, "max": 140000},
        "raw_source_data": raw_source_data,
    }

    record = JobIngestionRecord.model_validate(payload)

    assert record.raw_source_data == raw_source_data
    assert record.salary == {"currency": "USD", "min": 100000, "max": 140000}
    assert record.workplace_type == "hybrid"
    assert record.posted_at == datetime(2026, 9, 1, 10, tzinfo=timezone.utc)


@pytest.mark.parametrize("field", ["source", "source_job_id", "company", "title"])
def test_contract_requires_core_identity_fields(field: str):
    payload = dict(REQUIRED_FIELDS)
    del payload[field]

    with pytest.raises(ValidationError):
        JobIngestionRecord.model_validate(payload)


def test_contract_allows_missing_description():
    payload = dict(REQUIRED_FIELDS)
    payload.pop("description")

    assert JobIngestionRecord.model_validate(payload).description is None


def test_contract_rejects_unknown_workplace_type():
    payload = {**REQUIRED_FIELDS, "workplace_type": "flexible"}

    with pytest.raises(ValidationError):
        JobIngestionRecord.model_validate(payload)
