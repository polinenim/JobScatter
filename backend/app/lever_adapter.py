from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import httpx

from app.ingestion_contract import JobIngestionRecord


class LeverAdapter:
    """Fetch published postings from Lever's documented public Postings API."""

    base_urls = {
        "global": "https://api.lever.co/v0/postings",
        "eu": "https://api.eu.lever.co/v0/postings",
    }

    def __init__(self, site: str, company_name: str, region: str = "global", client: httpx.Client | None = None, max_results: int | None = None) -> None:
        if not site.strip() or not company_name.strip():
            raise ValueError("site and company_name must not be empty")
        if region not in self.base_urls:
            raise ValueError("region must be global or eu")
        self.site = site
        self.company_name = company_name
        self.base_url = self.base_urls[region]
        self._client = client
        self.max_results = max_results

    def fetch_jobs(self) -> list[JobIngestionRecord]:
        client, should_close = self._get_client()
        try:
            records: list[JobIngestionRecord] = []
            skip = 0
            while True:
                postings = self._fetch_page(client, skip)
                if self.max_results is not None:
                    postings = postings[:max(self.max_results - len(records), 0)]
                records.extend(
                    record for posting in postings
                    if (record := self._to_ingestion_record(posting)) is not None
                )
                if self.max_results is not None or len(postings) < 100:
                    return records
                skip += len(postings)
        finally:
            if should_close:
                client.close()

    def _get_client(self) -> tuple[httpx.Client, bool]:
        if self._client is not None:
            return self._client, False
        return httpx.Client(timeout=30.0), True

    def _fetch_page(self, client: httpx.Client, skip: int) -> list[dict[str, Any]]:
        url = f"{self.base_url}/{quote(self.site, safe='')}"
        try:
            response = client.get(url, params={"mode": "json", "limit": 100, "skip": skip})
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError):
            return []
        return [item for item in payload if isinstance(item, dict)] if isinstance(payload, list) else []

    def _to_ingestion_record(self, posting: dict[str, Any]) -> JobIngestionRecord | None:
        title = posting.get("text")
        description = posting.get("descriptionPlain")
        application_url = posting.get("applyUrl")
        source_url = posting.get("hostedUrl") or application_url
        source_job_id = posting.get("id")
        if not all(isinstance(value, str) and value for value in (title, description, application_url, source_url)):
            return None
        if source_job_id is None or not str(source_job_id):
            return None

        categories = posting.get("categories") if isinstance(posting.get("categories"), dict) else {}
        locations = categories.get("allLocations")
        if not isinstance(locations, list):
            location = categories.get("location")
            locations = [location] if isinstance(location, str) and location else None
        workplace_type = posting.get("workplaceType")
        if workplace_type == "onsite":
            workplace_type = "on-site"
        if workplace_type not in {"remote", "hybrid", "on-site", None}:
            workplace_type = None

        return JobIngestionRecord(
            source="lever",
            source_job_id=str(source_job_id),
            company=self.company_name,
            title=title,
            description=description,
            responsibilities=_lever_lists(posting.get("lists")),
            locations=locations,
            workplace_type=workplace_type,
            country=posting.get("country") if isinstance(posting.get("country"), str) else None,
            employment_type=categories.get("commitment") if isinstance(categories.get("commitment"), str) else None,
            opportunity_type=None,
            posted_at=_milliseconds_to_datetime(posting.get("createdAt")),
            updated_at=_milliseconds_to_datetime(posting.get("updatedAt")),
            salary=posting.get("salaryRange") if isinstance(posting.get("salaryRange"), dict) else None,
            application_url=application_url,
            source_url=source_url,
            raw_source_data=posting,
            discovered_at=datetime.now(timezone.utc),
        )


def _milliseconds_to_datetime(value: Any) -> datetime | None:
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc) if isinstance(value, (int, float)) else None


def _lever_lists(value: Any) -> str | None:
    if not isinstance(value, list):
        return None
    parts = [f"{item.get('text')}: {item.get('content')}" for item in value if isinstance(item, dict) and item.get("content")]
    return "\n".join(parts) or None