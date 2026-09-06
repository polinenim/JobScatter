from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import httpx

from app.ingestion_contract import JobIngestionRecord


class AshbyAdapter:
    """Fetch postings from Ashby's public job-board JSON endpoint."""

    base_url = "https://api.ashbyhq.com/posting-api/job-board"

    def __init__(self, board_name: str, company_name: str, client: httpx.Client | None = None, max_results: int | None = None) -> None:
        if not board_name.strip() or not company_name.strip():
            raise ValueError("board_name and company_name must not be empty")
        self.board_name = board_name
        self.company_name = company_name
        self._client = client
        self.max_results = max_results

    def fetch_jobs(self) -> list[JobIngestionRecord]:
        client, should_close = self._get_client()
        try:
            url = f"{self.base_url}/{quote(self.board_name, safe='')}"
            try:
                response = client.get(url)
                response.raise_for_status()
                payload = response.json()
            except (httpx.HTTPError, ValueError):
                return []
            jobs = payload.get("jobs") if isinstance(payload, dict) else None
            jobs = jobs[:self.max_results] if self.max_results is not None else jobs
            return [record for job in jobs or [] if isinstance(job, dict) and (record := self._to_ingestion_record(job)) is not None]
        finally:
            if should_close:
                client.close()

    def _get_client(self) -> tuple[httpx.Client, bool]:
        if self._client is not None:
            return self._client, False
        return httpx.Client(timeout=30.0), True

    def _to_ingestion_record(self, job: dict[str, Any]) -> JobIngestionRecord | None:
        title = job.get("title")
        description = job.get("descriptionPlain") or job.get("descriptionHtml")
        application_url = job.get("applyUrl")
        source_url = job.get("jobUrl") or application_url
        job_id = job.get("id")
        if not all(isinstance(value, str) and value for value in (title, description, application_url, source_url, job_id)):
            return None

        locations = [value for value in [job.get("location"), *(job.get("secondaryLocations") or [])] if isinstance(value, str) and value]
        workplace_type = job.get("workplaceType")
        if workplace_type == "onsite":
            workplace_type = "on-site"
        if workplace_type not in {"remote", "hybrid", "on-site", None}:
            workplace_type = "remote" if job.get("isRemote") is True else None

        return JobIngestionRecord(
            source="ashby",
            source_job_id=str(job_id),
            company=self.company_name,
            title=title,
            description=description,
            responsibilities=None,
            locations=locations or None,
            workplace_type=workplace_type,
            country=job.get("country") if isinstance(job.get("country"), str) else None,
            employment_type=job.get("employmentType") if isinstance(job.get("employmentType"), str) else None,
            opportunity_type=None,
            posted_at=_parse_datetime(job.get("publishedAt")),
            updated_at=_parse_datetime(job.get("updatedAt")),
            salary=None,
            application_url=application_url,
            source_url=source_url,
            raw_source_data=job,
            discovered_at=datetime.now(timezone.utc),
        )


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None