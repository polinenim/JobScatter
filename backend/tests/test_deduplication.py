from datetime import datetime, timezone

from app.canonical_job import CanonicalJob
from app.deduplication import are_duplicates, deduplicate_jobs


def make_job(
    source_job_id: str,
    *,
    source: str = "greenhouse",
    company: str = "Example Co",
    title: str = "Senior Software Engineer",
    description: str = "Build and maintain reliable platform services.",
    location: str | None = "New York, NY",
    application_url: str | None = None,
) -> CanonicalJob:
    return CanonicalJob(
        source=source,
        source_job_id=source_job_id,
        company=company,
        title=title,
        description=description,
        locations=[location] if location else None,
        application_url=application_url or f"https://jobs.example.test/{source_job_id}",
        source_url=f"https://source.example.test/{source_job_id}",
        raw_source_data={"id": source_job_id},
        discovered_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
    )


def test_same_source_and_source_job_id_is_duplicate():
    left = make_job("123")
    right = make_job("123", title="Different title", description="Different description")

    assert are_duplicates(left, right)


def test_same_normalized_application_url_is_duplicate():
    left = make_job("123", application_url="https://jobs.example.test/123")
    right = make_job(
        "456",
        company="Other Co",
        application_url=" HTTPS://JOBS.EXAMPLE.TEST/123 ",
    )

    assert are_duplicates(left, right)


def test_same_company_and_highly_similar_job_is_duplicate():
    left = make_job("123")
    right = make_job(
        "456",
        title="Senior Software Engineer ",
        description="Build and maintain reliable platform services.",
    )

    assert are_duplicates(left, right)


def test_same_company_different_jobs_remain_separate():
    left = make_job("123")
    right = make_job(
        "456",
        title="Product Manager",
        description="Lead product planning and customer discovery.",
    )

    assert not are_duplicates(left, right)


def test_different_companies_with_identical_descriptions_remain_separate():
    left = make_job("123", company="Example Co")
    right = make_job("456", company="Other Co")

    assert not are_duplicates(left, right)


def test_uncertain_similarity_remains_separate():
    left = make_job("123", title="Software Engineer")
    right = make_job(
        "456",
        title="Staff Software Engineer",
        description="Own a broad technical strategy across multiple engineering teams.",
    )

    assert not are_duplicates(left, right)


def test_deduplication_retains_all_source_records():
    first = make_job("123")
    second = make_job("456", application_url=first.application_url)

    groups = deduplicate_jobs([first, second])

    assert len(groups) == 1
    assert groups[0].representative == first
    assert groups[0].source_records == (first, second)
