import httpx

from app.ashby_adapter import AshbyAdapter


def mocked_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_fetch_jobs_maps_public_ashby_posting():
    payload = {
        "id": "ashby-123",
        "title": "Senior Engineer",
        "department": "Engineering",
        "team": "Platform",
        "employmentType": "Full-time",
        "location": "Remote - Finland",
        "secondaryLocations": ["Helsinki, Finland"],
        "publishedAt": "2026-09-01T10:00:00.000Z",
        "isRemote": True,
        "workplaceType": "remote",
        "jobUrl": "https://jobs.ashbyhq.com/example/ashby-123",
        "applyUrl": "https://jobs.ashbyhq.com/example/ashby-123/application",
        "descriptionPlain": "Build reliable systems.",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/posting-api/job-board/example"
        return httpx.Response(200, json={"jobs": [payload]})

    record = AshbyAdapter("example", "Example Co", client=mocked_client(handler)).fetch_jobs()[0]

    assert record.source == "ashby"
    assert record.source_job_id == "ashby-123"
    assert record.company == "Example Co"
    assert record.title == "Senior Engineer"
    assert record.description == "Build reliable systems."
    assert record.locations == ["Remote - Finland", "Helsinki, Finland"]
    assert record.workplace_type == "remote"
    assert record.employment_type == "Full-time"
    assert record.posted_at.isoformat() == "2026-09-01T10:00:00+00:00"
    assert record.application_url.endswith("/application")
    assert record.source_url.endswith("ashby-123")
    assert record.raw_source_data == payload


def test_fetch_jobs_returns_empty_list_for_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    records = AshbyAdapter("example", "Example Co", client=mocked_client(handler)).fetch_jobs()

    assert records == []
