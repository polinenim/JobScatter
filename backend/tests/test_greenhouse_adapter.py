import httpx

from app.greenhouse_adapter import GreenhouseAdapter


SUMMARY = {
    "id": 123,
    "title": "Software Engineer",
    "updated_at": "2026-09-02T10:00:00Z",
    "absolute_url": "https://boards.greenhouse.io/example/jobs/123",
}

DETAIL = {
    **SUMMARY,
    "company_name": "Example Co",
    "first_published": "2026-09-01T10:00:00Z",
    "content": "Build reliable software.",
    "location": {"name": "New York, NY"},
    "pay_input_ranges": [
        {"min_cents": 10000000, "max_cents": 14000000, "currency_type": "USD"}
    ],
    "metadata": [{"id": 1, "name": "team", "value": "platform"}],
}


def mocked_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_fetch_jobs_maps_greenhouse_data_and_preserves_raw_payload():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/jobs"):
            return httpx.Response(200, json={"jobs": [SUMMARY], "meta": {"total": 1}})
        return httpx.Response(200, json=DETAIL)

    adapter = GreenhouseAdapter("example", mocked_client(handler))
    records = adapter.fetch_jobs()

    assert len(records) == 1
    record = records[0]
    assert record.source == "greenhouse"
    assert record.source_job_id == "123"
    assert record.company == "Example Co"
    assert record.title == "Software Engineer"
    assert record.description == "Build reliable software."
    assert record.locations == ["New York, NY"]
    assert record.posted_at.isoformat() == "2026-09-01T10:00:00+00:00"
    assert record.updated_at.isoformat() == "2026-09-02T10:00:00+00:00"
    assert record.salary == {"pay_input_ranges": DETAIL["pay_input_ranges"]}
    assert record.application_url == DETAIL["absolute_url"]
    assert record.source_url == DETAIL["absolute_url"]
    assert record.raw_source_data == DETAIL
    assert record.workplace_type is None
    assert record.country is None
    assert record.employment_type is None
    assert record.opportunity_type is None


def test_fetch_jobs_leaves_unprovided_fields_none():
    detail = {
        "id": 123,
        "company_name": "Example Co",
        "title": "Software Engineer",
        "content": "Build reliable software.",
        "absolute_url": "https://boards.greenhouse.io/example/jobs/123",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/jobs"):
            return httpx.Response(200, json={"jobs": [{"id": 123}]})
        return httpx.Response(200, json=detail)

    record = GreenhouseAdapter("example", mocked_client(handler)).fetch_jobs()[0]

    assert record.locations is None
    assert record.salary is None
    assert record.posted_at is None
    assert record.updated_at is None
    assert record.workplace_type is None
    assert record.country is None
    assert record.employment_type is None
    assert record.opportunity_type is None


def test_fetch_jobs_returns_empty_list_for_board_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    records = GreenhouseAdapter("example", mocked_client(handler)).fetch_jobs()

    assert records == []


def test_fetch_jobs_skips_a_posting_when_detail_request_fails():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/jobs"):
            return httpx.Response(200, json={"jobs": [SUMMARY]})
        return httpx.Response(404)

    records = GreenhouseAdapter("example", mocked_client(handler)).fetch_jobs()

    assert records == []
