import httpx

from app.jobly_adapter import JoblyAdapter


ROBOTS = """User-agent: *
Crawl-delay: 10
Allow: /tyopaikat/teknologia
Disallow: /search/
"""

LISTING = """
<article id="node-2748751" class="node node--job-per-template--teaser">
  <h2 class="node__title"><a href="/tyopaikka/software-engineer-helsinki-2748751">Software Engineer</a></h2>
  <a class="recruiter-company-profile-job-organization" href="/yritys/example">Example Oy</a>
  <div class="description">Build useful software.</div>
  <div class="location">Helsinki</div>
  <div class="date">05.09.2026,</div>
</article>
"""


def mocked_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_fetch_jobs_maps_listing_and_honors_url_and_crawl_delay():
    requests = []
    delays = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text=ROBOTS)
        assert request.url.path == "/tyopaikat/teknologia"
        assert request.url.params["search"] == "software"
        assert request.url.params["job_geo_location"] == "Finland"
        return httpx.Response(200, text=LISTING)

    records = JoblyAdapter(
        client=mocked_client(handler), sleep_fn=delays.append
    ).fetch_jobs()

    assert delays == [10.0]
    assert len(requests) == 2
    record = records[0]
    assert record.source == "jobly"
    assert record.source_job_id == "2748751"
    assert record.company == "Example Oy"
    assert record.title == "Software Engineer"
    assert record.locations == ["Helsinki"]
    assert record.country is None
    assert record.posted_at.isoformat() == "2026-09-05T00:00:00+00:00"
    assert record.updated_at is None
    assert record.employment_type is None
    assert record.opportunity_type is None
    assert record.source_url == "https://www.jobly.fi/tyopaikka/software-engineer-helsinki-2748751"
    assert record.application_url == record.source_url
    assert record.raw_source_data["description"] == "Build useful software."
    assert records[0].source_job_id == "2748751"


def test_fetch_jobs_rejects_missing_required_listing_fields():
    missing_company = LISTING.replace(
        '<a class="recruiter-company-profile-job-organization" href="/yritys/example">Example Oy</a>',
        "",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=ROBOTS if request.url.path == "/robots.txt" else missing_company)

    records = JoblyAdapter(client=mocked_client(handler), sleep_fn=lambda _: None).fetch_jobs()

    assert records == []


def test_fetch_jobs_accepts_listing_without_description():
    listing = LISTING.replace('  <div class="description">Build useful software.</div>\n', "")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=ROBOTS if request.url.path == "/robots.txt" else listing)

    records = JoblyAdapter(client=mocked_client(handler), sleep_fn=lambda _: None).fetch_jobs()

    assert len(records) == 1
    assert records[0].description is None
    assert records[0].company == "Example Oy"
    assert records[0].title == "Software Engineer"


def test_fetch_jobs_rejects_malformed_listing_and_deduplicates_ids():
    malformed = "<article id=\"node-bad\" class=\"node--job-per-template--teaser\"><h2 class=\"node__title\">No URL</h2></article>"
    duplicate = LISTING.replace("2748751", "2748751").replace("Software Engineer", "Software Engineer Duplicate")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=ROBOTS if request.url.path == "/robots.txt" else malformed + duplicate + LISTING)

    records = JoblyAdapter(client=mocked_client(handler), sleep_fn=lambda _: None).fetch_jobs()

    assert len(records) == 1
    assert records[0].source_job_id == "2748751"
    assert records[0].title == "Software Engineer Duplicate"


def test_fetch_jobs_returns_empty_when_robots_disallows_search():
    robots = "User-agent: *\nDisallow: /\n"
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        return httpx.Response(200, text=robots)

    records = JoblyAdapter(client=mocked_client(handler), sleep_fn=lambda _: None).fetch_jobs()

    assert records == []
    assert calls == ["/robots.txt"]


def test_fetch_jobs_returns_empty_for_robots_or_page_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    records = JoblyAdapter(client=mocked_client(handler), sleep_fn=lambda _: None).fetch_jobs()

    assert records == []
