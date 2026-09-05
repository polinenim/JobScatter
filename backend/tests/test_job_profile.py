from datetime import datetime, timezone

from app.canonical_job import CanonicalJob
from app.job_profile import UNKNOWN, extract_job_profile


def make_job(title: str, description: str) -> CanonicalJob:
    return CanonicalJob(
        source="test",
        source_job_id="1",
        company="Example Co",
        title=title,
        description=description,
        application_url="https://example.test/jobs/1",
        source_url="https://example.test/jobs/1",
        raw_source_data={"title": title, "description": description},
        discovered_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
    )


def test_extracts_ai_architecture_hierarchy_without_changing_canonical_job():
    job = make_job(
        "AI Solutions Architect",
        "Design ML platforms with Python, PyTorch, Docker and PostgreSQL. Finnish required.",
    )

    profile = extract_job_profile(job)

    assert profile.it_field == "AI / Machine Learning"
    assert profile.role_family == "AI Architecture"
    assert profile.specific_role == "AI Solutions Architect"
    assert profile.skills == ["Python", "PyTorch", "Docker", "PostgreSQL"]
    assert profile.capabilities == ["ML"]
    assert profile.required_languages == ["Finnish"]
    assert profile.analysis_version == "deterministic-v1"
    assert job.description.startswith("Design ML")


def test_unrecognized_title_keeps_unknown_classification():
    profile = extract_job_profile(
        make_job("Technology Specialist", "Support technology initiatives.")
    )

    assert profile.it_field == UNKNOWN
    assert profile.role_family == UNKNOWN
    assert profile.specific_role == "Technology Specialist"
    assert profile.seniority == UNKNOWN
    assert profile.required_experience.priority == "unknown"
    assert profile.required_languages is None
    assert profile.education_requirements is None


def test_extracts_seniority_and_required_experience_rules():
    profile = extract_job_profile(
        make_job(
            "Senior Backend Engineer",
            "Minimum of 3 years required. English only. Bachelor degree preferred.",
        )
    )

    assert profile.seniority == "Senior"
    assert profile.required_experience.minimum_years == 3
    assert profile.required_experience.required is True
    assert profile.required_experience.priority == "ineligible"
    assert profile.required_languages == []
    assert profile.education_requirements == "bachelor degree preferred"


def test_unknown_optional_requirements_remain_unknown():
    profile = extract_job_profile(
        make_job("Backend Engineer", "Build services using FastAPI and SQL.")
    )

    assert profile.it_field == "Software Engineering"
    assert profile.role_family == "Backend"
    assert profile.skills == ["SQL", "FastAPI"]
    assert profile.capabilities == ["Backend development"]
    assert profile.required_experience.priority == "unknown"
    assert profile.required_languages is None
    assert profile.education_requirements is None
    assert profile.workplace_type is None
    assert profile.locations is None
