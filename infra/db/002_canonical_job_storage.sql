CREATE TABLE IF NOT EXISTS companies (
    company_id UUID PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS canonical_jobs (
    job_id UUID PRIMARY KEY,
    company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE RESTRICT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    responsibilities TEXT,
    locations JSONB,
    workplace_type VARCHAR(20),
    country TEXT,
    employment_type TEXT,
    opportunity_type TEXT,
    salary JSONB,
    application_url TEXT NOT NULL,
    source_url TEXT NOT NULL,
    posted_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    discovered_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'unknown',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at_record TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT canonical_jobs_status_check
        CHECK (status IN ('active', 'closed', 'expired', 'unavailable', 'unknown'))
);

CREATE INDEX IF NOT EXISTS ix_canonical_jobs_company_id
    ON canonical_jobs (company_id);

CREATE TABLE IF NOT EXISTS job_source_records (
    source_record_id UUID PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES canonical_jobs(job_id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    source_job_id TEXT NOT NULL,
    application_url TEXT NOT NULL,
    source_url TEXT NOT NULL,
    posted_at TIMESTAMPTZ,
    raw_source_data JSONB,
    ingestion_record JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source, source_job_id)
);

CREATE INDEX IF NOT EXISTS ix_job_source_records_job_id
    ON job_source_records (job_id);
