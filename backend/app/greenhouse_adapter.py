from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import httpx

from app.ingestion_contract import JobIngestionRecord


class GreenhouseAdapter:
    """Stateless adapter for a public Greenhouse Job Board."""

    base_url = "https://boards-api.greenhouse.io/v1/boards"

    def __init__(self, board_token: str, client: httpx.Client | None = None) -> None:
        if not board_token.strip():
            raise ValueError("board_token must not be empty")
        self.board_token = board_token
        self._client = client

    def fetch_jobs(self) -> list[JobIngestionRecord]:
        """Fetch published jobs, returning no records when the board is unavailable."""
        client, should_close = self._get_client()
        try:
            jobs = self._fetch_job_summaries(client)
            records: list[JobIngestionRecord] = []
            for summary in jobs:
                record = self._fetch_record(client, summary)
                if record is not None:
                    records.append(record)
            return records
        finally:
            if should_close:
                client.close()

    def _get_client(self) -> tuple[httpx.Client, bool]:
        if self._client is not None:
            return self._client, False
        return httpx.Client(timeout=30.0), True

    def _fetch_job_summaries(self, client: httpx.Client) -> list[dict[str, Any]]:
        url = f"{self.base_url}/{quote(self.board_token, safe='')}/jobs"
        try:
            response = client.get(url, params={"content": "true"})
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError):
            return []

        jobs = payload.get("jobs") if isinstance(payload, dict) else None
        if not isinstance(jobs, list):
            return []
        return [job for job in jobs if isinstance(job, dict)]

    def _fetch_record(
        self, client: httpx.Client, summary: dict[str, Any]
    ) -> JobIngestionRecord | None:
        job_id = summary.get("id")
        if job_id is None:
            return None

        url = f"{self.base_url}/{quote(self.board_token, safe='')}/jobs/{job_id}"
        try:
            response = client.get(url, params={"pay_transparency": "true"})
            response.raise_for_status()
            detail = response.json()
        except (httpx.HTTPError, ValueError):
            return None

        if not isinstance(detail, dict):
            return None
        return self._to_ingestion_record(detail, summary)

    def _to_ingestion_record(
        self, detail: dict[str, Any], summary: dict[str, Any]
    ) -> JobIngestionRecord | None:
        company = detail.get("company_name")
        title = detail.get("title")
        description = detail.get("content")
        application_url = detail.get("absolute_url")
        if not all(isinstance(value, str) and value for value in (
            company,
            title,
            description,
            application_url,
        )):
            return None

        location = detail.get("location")
        locations = None
        if isinstance(location, dict) and isinstance(location.get("name"), str):
            locations = [location["name"]]

        pay_input_ranges = detail.get("pay_input_ranges")
        salary = None
        if isinstance(pay_input_ranges, list) and pay_input_ranges:
            salary = {"pay_input_ranges": pay_input_ranges}

        updated_at = detail.get("updated_at") or summary.get("updated_at")
        first_published = detail.get("first_published")

        return JobIngestionRecord(
            source="greenhouse",
            source_job_id=str(detail.get("id", summary["id"])),
            company=company,
            title=title,
            description=description,
            responsibilities=None,
            locations=locations,
            workplace_type=None,
            country=None,
            employment_type=None,
            opportunity_type=None,
            posted_at=first_published,
            updated_at=updated_at,
            salary=salary,
            application_url=application_url,
            source_url=application_url,
            raw_source_data=detail,
            discovered_at=datetime.now(timezone.utc),
        )
