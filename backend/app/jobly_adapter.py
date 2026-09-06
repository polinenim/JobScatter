from datetime import datetime, timezone
from html.parser import HTMLParser
from time import sleep
from typing import Any, Callable
from urllib.parse import urljoin

import httpx

from app.ingestion_contract import JobIngestionRecord


class JoblyAdapter:
    """Fetch a bounded Jobly search page while honoring its public robots rules."""

    base_url = "https://www.jobly.fi"
    robots_path = "/robots.txt"
    default_search_path = "/tyopaikat/teknologia"
    default_search_term = "software"
    default_location = "Finland"
    user_agent = "JobScatter/1.0 (+https://jobscatter.example/research)"

    def __init__(
        self,
        search_term: str = default_search_term,
        location: str = default_location,
        search_path: str = default_search_path,
        max_results: int = 20,
        client: httpx.Client | None = None,
        sleep_fn: Callable[[float], None] = sleep,
    ) -> None:
        if not search_term.strip() or not location.strip():
            raise ValueError("search_term and location must not be empty")
        if not search_path.startswith("/"):
            raise ValueError("search_path must start with /")
        if not 1 <= max_results <= 20:
            raise ValueError("max_results must be between 1 and 20")
        self.search_term = search_term
        self.location = location
        self.search_path = search_path
        self.max_results = max_results
        self._client = client
        self._sleep = sleep_fn
        self.last_run_stats = {
            "collected": 0,
            "rejected": 0,
            "duplicates": 0,
            "robots_status": None,
            "search_status": None,
            "parsed_listings": 0,
            "final_url": None,
            "html_length": 0,
            "listing_markers": 0,
            "article_starts": 0,
            "article_ends": 0,
        }

    def fetch_jobs(self) -> list[JobIngestionRecord]:
        self.last_run_stats = {
            "collected": 0,
            "rejected": 0,
            "duplicates": 0,
            "robots_status": None,
            "search_status": None,
            "parsed_listings": 0,
            "final_url": None,
            "html_length": 0,
            "listing_markers": 0,
            "article_starts": 0,
            "article_ends": 0,
        }
        client, should_close = self._get_client()
        try:
            robots_response = self._get(client, self.robots_path)
            if robots_response is None:
                return []
            self.last_run_stats["robots_status"] = robots_response.status_code
            if robots_response.is_error:
                return []
            allowed, crawl_delay = _robots_policy(
                robots_response.text, self.search_path, self.user_agent
            )
            if not allowed:
                return []
            if crawl_delay:
                self._sleep(crawl_delay)

            response = self._get(
                client,
                self.search_path,
                params={
                    "search": self.search_term,
                    "job_geo_location": self.location,
                    "country": self.location,
                },
            )
            if response is None:
                return []
            self.last_run_stats["search_status"] = response.status_code
            if response.is_error:
                return []
            self.last_run_stats["final_url"] = str(response.url)
            self.last_run_stats["html_length"] = len(response.text)
            self.last_run_stats["listing_markers"] = response.text.count("node--job-per-template--teaser")

            parser = _JoblyListingParser()
            parser.feed(response.text)
            self.last_run_stats["parsed_listings"] = len(parser.listings)
            self.last_run_stats["article_starts"] = parser.article_starts
            self.last_run_stats["article_ends"] = parser.article_ends
            records: list[JobIngestionRecord] = []
            seen_ids: set[str] = set()
            for listing in parser.listings:
                record = self._to_ingestion_record(listing)
                if record is None:
                    self.last_run_stats["rejected"] += 1
                    continue
                if record.source_job_id in seen_ids:
                    self.last_run_stats["duplicates"] += 1
                    continue
                seen_ids.add(record.source_job_id)
                records.append(record)
                self.last_run_stats["collected"] += 1
                if len(records) >= self.max_results:
                    break
            return records
        finally:
            if should_close:
                client.close()

    def _get(self, client: httpx.Client, path: str, params: dict[str, str] | None = None) -> httpx.Response | None:
        try:
            response = client.get(
                urljoin(self.base_url, path),
                params=params,
                headers={"User-Agent": self.user_agent},
            )
            return response
        except httpx.HTTPError as exc:
            if isinstance(exc, httpx.HTTPStatusError):
                return exc.response
            return None

    def _get_client(self) -> tuple[httpx.Client, bool]:
        if self._client is not None:
            return self._client, False
        return httpx.Client(timeout=30.0, follow_redirects=True), True

    def _to_ingestion_record(self, listing: dict[str, Any]) -> JobIngestionRecord | None:
        job_id = listing.get("source_job_id")
        title = listing.get("title")
        company = listing.get("company")
        job_url = listing.get("job_url")
        description = listing.get("description")
        if not all(isinstance(value, str) and value.strip() for value in (job_id, title, company, job_url)):
            return None
        if not isinstance(description, str) or not description.strip():
            description = None

        locations = listing.get("locations")
        if not isinstance(locations, list):
            locations = None
        posted_at = _parse_finnish_date(listing.get("posted_date"))
        return JobIngestionRecord(
            source="jobly",
            source_job_id=job_id,
            company=company,
            title=title,
            description=description,
            responsibilities=None,
            locations=locations,
            workplace_type=None,
            country=_country_from_locations(locations),
            employment_type=None,
            opportunity_type=None,
            posted_at=posted_at,
            updated_at=None,
            salary=None,
            application_url=job_url,
            source_url=job_url,
            raw_source_data=listing,
            discovered_at=datetime.now(timezone.utc),
        )


class _JoblyListingParser(HTMLParser):
    _void_tags = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
    _field_classes = {
        "node__title": "title",
        "recruiter-company-profile-job-organization": "company",
        "location": "location",
        "date": "posted_date",
        "description": "description",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.listings: list[dict[str, Any]] = []
        self.article_starts = 0
        self.article_ends = 0
        self._current: dict[str, Any] | None = None
        self._article_depth: int | None = None
        self._depth = 0
        self._active_field: str | None = None
        self._active_depth: int | None = None
        self._field_buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        is_void = tag in self._void_tags
        if not is_void:
            self._depth += 1
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())
        if tag == "article" and "node--job-per-template--teaser" in classes:
            self.article_starts += 1
            self._current = {"source_job_id": _article_id(attributes.get("id"))}
            self._article_depth = self._depth
        if self._current is None:
            return

        if tag == "a" and not self._current.get("job_url"):
            href = attributes.get("href")
            if href and "/tyopaikka/" in href:
                self._current["job_url"] = urljoin(JoblyAdapter.base_url, href.split("?", 1)[0])
        for class_name, field_name in self._field_classes.items():
            if class_name in classes:
                self._active_field = field_name
                self._active_depth = self._depth
                self._field_buffer = []
                break

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in self._void_tags:
            self.handle_endtag(tag)

    def handle_data(self, data: str) -> None:
        if self._active_field is not None:
            self._field_buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._active_field is not None and self._active_depth == self._depth:
            value = " ".join("".join(self._field_buffer).split())
            if value:
                if self._active_field == "location":
                    self._current.setdefault("locations", []).append(value)
                else:
                    self._current[self._active_field] = value
            self._active_field = None
            self._active_depth = None
            self._field_buffer = []

        if tag == "article" and self._current is not None:
            self.article_ends += 1
            self.listings.append(self._current)
            self._current = None
            self._article_depth = None
        self._depth -= 1


def _article_id(value: str | None) -> str | None:
    return value.removeprefix("node-") if value and value.startswith("node-") else None


def _parse_finnish_date(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value.rstrip(", "), "%d.%m.%Y").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _country_from_locations(locations: list[str] | None) -> str | None:
    if not locations:
        return None
    text = " ".join(locations).casefold()
    return "FI" if "finland" in text or "suomi" in text else None


def _robots_policy(robots_text: str, path: str, user_agent: str) -> tuple[bool, float | None]:
    active_agents: list[str] = []
    rules: dict[str, list[str]] = {}
    delays: dict[str, float] = {}
    for raw_line in robots_text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        key = key.casefold()
        if key == "user-agent":
            active_agents = [value.casefold()]
            rules.setdefault(value.casefold(), [])
        elif key == "disallow" and active_agents:
            for agent in active_agents:
                rules.setdefault(agent, []).append(value)
        elif key == "crawl-delay" and active_agents:
            try:
                delay = float(value)
            except ValueError:
                continue
            for agent in active_agents:
                delays[agent] = delay
    selected = rules.get(user_agent.casefold()) or rules.get("*") or []
    selected_agent = user_agent.casefold() if user_agent.casefold() in rules else "*"
    return (
        not any(rule and path.startswith(rule) for rule in selected),
        delays.get(selected_agent),
    )