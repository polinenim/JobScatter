from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from psycopg import connect
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.canonical_job import CanonicalJob
from app.config import settings
from app.deduplication import DeduplicatedJob, are_duplicates
from app.job_profile import JobProfile


class JobStatus(StrEnum):
    ACTIVE = "active"
    CLOSED = "closed"
    EXPIRED = "expired"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class JobRepository:
    def __init__(self, connection_factory=None) -> None:
        self._connection_factory = connection_factory or self._get_connection

    @staticmethod
    def _get_connection():
        return connect(settings.database_url, row_factory=dict_row)

    def save_deduplicated_job(
        self,
        group: DeduplicatedJob,
        status: JobStatus = JobStatus.UNKNOWN,
    ) -> UUID:
        job = group.representative
        job_id = uuid4()
        with self._connection_factory() as connection:
            company_id = self._upsert_company(connection, job.company)
            self._insert_job(connection, job_id, company_id, job, status)
            for source_record in group.source_records:
                self._upsert_source_record(connection, job_id, source_record)
        return job_id

    def find_matching_job(self, candidate: CanonicalJob) -> UUID | None:
        with self._connection_factory() as connection:
            records = connection.execute(
                "SELECT job_id, ingestion_record FROM job_source_records"
            ).fetchall()

        for record in records:
            existing = CanonicalJob.model_validate(record["ingestion_record"])
            if are_duplicates(candidate, existing):
                return record["job_id"]
        return None

    def attach_source_records(
        self,
        job_id: UUID,
        source_records: tuple[CanonicalJob, ...],
    ) -> None:
        with self._connection_factory() as connection:
            for source_record in source_records:
                self._upsert_source_record(connection, job_id, source_record)

    def save_job_profile(self, job_id: UUID, profile: JobProfile) -> None:
        with self._connection_factory() as connection:
            connection.execute(
                """
                INSERT INTO job_profiles (
                    job_id, profile, analysis_version, model_version
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (job_id) DO UPDATE SET
                    profile = EXCLUDED.profile,
                    analysis_version = EXCLUDED.analysis_version,
                    model_version = EXCLUDED.model_version,
                    updated_at = NOW()
                """,
                (
                    job_id,
                    Jsonb(profile.model_dump(mode="json")),
                    profile.analysis_version,
                    profile.model_version,
                ),
            )

    def list_canonical_jobs(self) -> list[tuple[UUID, CanonicalJob]]:
        with self._connection_factory() as connection:
            records = connection.execute(
                """
                SELECT DISTINCT ON (job_id) job_id, ingestion_record
                FROM job_source_records
                ORDER BY job_id, created_at
                """
            ).fetchall()
        return [
            (record["job_id"], CanonicalJob.model_validate(record["ingestion_record"]))
            for record in records
        ]

    def job_profile_exists(self, job_id: UUID) -> bool:
        with self._connection_factory() as connection:
            record = connection.execute(
                "SELECT 1 FROM job_profiles WHERE job_id = %s", (job_id,)
            ).fetchone()
        return record is not None

    def list_jobs(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        it_field: str | None = None,
        opportunity_type: str | None = None,
        experience_suitability: str | None = None,
        location: str | None = None,
        workplace_type: str | None = None,
        include_inactive: bool = False,
    ) -> tuple[list[dict[str, Any]], int]:
        conditions = []
        parameters: list[Any] = []
        if not include_inactive:
            conditions.append("j.status NOT IN ('closed', 'expired')")
        if search:
            conditions.append("(j.title ILIKE %s OR j.description ILIKE %s OR c.name ILIKE %s)")
            value = f"%{search}%"
            parameters.extend([value, value, value])
        if it_field:
            conditions.append("p.profile->>'it_field' = %s")
            parameters.append(it_field)
        if opportunity_type:
            conditions.append("p.profile->>'opportunity_type' = %s")
            parameters.append(opportunity_type)
        if experience_suitability:
            conditions.append("p.profile->'required_experience'->>'priority' = %s")
            parameters.append(experience_suitability)
        if location:
            conditions.append("EXISTS (SELECT 1 FROM jsonb_array_elements_text(COALESCE(j.locations, '[]'::jsonb)) AS location_name WHERE location_name ILIKE %s)")
            parameters.append(f"%{location}%")
        if workplace_type:
            conditions.append("j.workplace_type = %s")
            parameters.append(workplace_type)

        where_clause = " AND ".join(conditions) or "TRUE"
        with self._connection_factory() as connection:
            total = connection.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM canonical_jobs j
                JOIN companies c ON c.company_id = j.company_id
                LEFT JOIN job_profiles p ON p.job_id = j.job_id
                WHERE {where_clause}
                """,
                parameters,
            ).fetchone()["total"]
            records = connection.execute(
                f"""
                SELECT
                    j.job_id, c.name AS company, j.title, j.description,
                    j.locations, j.workplace_type, j.country, j.employment_type,
                    j.opportunity_type, j.posted_at, j.updated_at,
                    j.application_url, j.source_url, j.status,
                    p.profile->>'it_field' AS it_field,
                    p.profile->'required_experience'->>'priority' AS experience_suitability,
                    COALESCE(
                        jsonb_agg(jsonb_build_object(
                            'source', r.source,
                            'source_job_id', r.source_job_id,
                            'source_url', r.source_url,
                            'application_url', r.application_url
                        ) ORDER BY r.created_at) FILTER (WHERE r.source_record_id IS NOT NULL),
                        '[]'::jsonb
                    ) AS source_records
                FROM canonical_jobs j
                JOIN companies c ON c.company_id = j.company_id
                LEFT JOIN job_profiles p ON p.job_id = j.job_id
                LEFT JOIN job_source_records r ON r.job_id = j.job_id
                WHERE {where_clause}
                GROUP BY j.job_id, c.name, p.profile
                ORDER BY j.posted_at DESC NULLS LAST, j.job_id
                LIMIT %s OFFSET %s
                """,
                parameters + [page_size, (page - 1) * page_size],
            ).fetchall()
        return records, total

    def _upsert_company(self, connection, company_name: str) -> UUID:
        result = connection.execute(
            """
            INSERT INTO companies (company_id, name)
            VALUES (%s, %s)
            ON CONFLICT (name) DO UPDATE SET updated_at = NOW()
            RETURNING company_id
            """,
            (uuid4(), company_name),
        )
        return result.fetchone()["company_id"]

    def _insert_job(
        self,
        connection,
        job_id: UUID,
        company_id: UUID,
        job: CanonicalJob,
        status: JobStatus,
    ) -> None:
        connection.execute(
            """
            INSERT INTO canonical_jobs (
                job_id, company_id, title, description, responsibilities,
                locations, workplace_type, country, employment_type,
                opportunity_type, salary, application_url, source_url,
                posted_at, updated_at, discovered_at, status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                job_id,
                company_id,
                job.title,
                job.description,
                job.responsibilities,
                _jsonb_or_none(job.locations),
                job.workplace_type,
                job.country,
                job.employment_type,
                job.opportunity_type,
                _jsonb_or_none(job.salary),
                job.application_url,
                job.source_url,
                job.posted_at,
                job.updated_at,
                job.discovered_at,
                status.value,
            ),
        )

    def _upsert_source_record(
        self,
        connection,
        job_id: UUID,
        source_record: CanonicalJob,
    ) -> None:
        connection.execute(
            """
            INSERT INTO job_source_records (
                source_record_id, job_id, source, source_job_id,
                application_url, source_url, posted_at, raw_source_data,
                ingestion_record
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (source, source_job_id) DO UPDATE SET
                job_id = EXCLUDED.job_id,
                application_url = EXCLUDED.application_url,
                source_url = EXCLUDED.source_url,
                posted_at = EXCLUDED.posted_at,
                raw_source_data = EXCLUDED.raw_source_data,
                ingestion_record = EXCLUDED.ingestion_record
            """,
            (
                uuid4(),
                job_id,
                source_record.source,
                source_record.source_job_id,
                source_record.application_url,
                source_record.source_url,
                source_record.posted_at,
                _jsonb_or_none(source_record.raw_source_data),
                Jsonb(source_record.model_dump(mode="json")),
            ),
        )


def _jsonb_or_none(value: Any) -> Jsonb | None:
    return Jsonb(value) if value is not None else None
