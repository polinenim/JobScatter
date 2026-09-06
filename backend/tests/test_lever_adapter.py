import httpx

from app.lever_adapter import LeverAdapter


def mocked_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_fetch_jobs_maps_public_lever_posting():
    payload = {
        "id": "lever-123",
        "text": "Platform Engineer",
        "descriptionPlain": "Build reliable systems.",
        "categories": {
            "location": "Helsinki, Finland",
            "allLocations": ["Helsinki, Finland"],
            "commitment": "Full-time",
        },
        "country": "FI",
        "workplaceType": "hybrid",
        "createdAt": 1760000000000,
        "updatedAt": 1760001000000,
        "hostedUrl": "https://jobs.lever.co/example/lever-123",
        "applyUrl": "https://jobs.lever.co/example/lever-123/apply",
        "lists": [{"text": "Responsibilities", "content": "Ship features."}],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v0/postings/example"
        assert request.url.params["mode"] == "json"
        return httpx.Response(200, json=[payload])

    record = LeverAdapter("example", "Example Co", client=mocked_client(handler)).fetch_jobs()[0]

    assert record.source == "lever"
    assert record.source_job_id == "lever-123"
    assert record.company == "Example Co"
    assert record.title == "Platform Engineer"
    assert record.description == "Build reliable systems."
    assert record.responsibilities == "Responsibilities: Ship features."
    assert record.locations == ["Helsinki, Finland"]
    assert record.country == "FI"
    assert record.workplace_type == "hybrid"
    assert record.employment_type == "Full-time"
    assert record.application_url.endswith("/apply")
    assert record.source_url.endswith("lever-123")
    assert record.raw_source_data == payload
    assert record.posted_at.isoformat() == "2025-10-09T08:53:20+00:00"


def test_fetch_jobs_returns_empty_list_for_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    records = LeverAdapter("example", "Example Co", client=mocked_client(handler)).fetch_jobs()

    assert records == []
