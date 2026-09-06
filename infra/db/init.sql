CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS source_registry (
	source_id UUID PRIMARY KEY,
	source_name VARCHAR(255) NOT NULL,
	source_type VARCHAR(100) NOT NULL,
	access_method VARCHAR(100) NOT NULL,
	base_endpoint VARCHAR(2048),
	configuration JSONB NOT NULL DEFAULT '{}'::jsonb,
	enabled BOOLEAN NOT NULL DEFAULT TRUE,
	capabilities JSONB NOT NULL DEFAULT '[]'::jsonb,
	last_successful_run TIMESTAMPTZ,
	last_error JSONB,
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_source_registry_enabled
	ON source_registry (enabled);

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
	description TEXT,
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

CREATE TABLE IF NOT EXISTS job_profiles (
	job_id UUID PRIMARY KEY REFERENCES canonical_jobs(job_id) ON DELETE CASCADE,
	profile JSONB NOT NULL,
	analysis_version TEXT NOT NULL,
	model_version TEXT,
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS candidates (
	candidate_id UUID PRIMARY KEY,
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS candidate_profile_versions (
	candidate_id UUID NOT NULL REFERENCES candidates(candidate_id) ON DELETE CASCADE,
	version INTEGER NOT NULL CHECK (version > 0),
	status VARCHAR(20) NOT NULL DEFAULT 'draft',
	profile JSONB NOT NULL,
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	confirmed_at TIMESTAMPTZ,
	PRIMARY KEY (candidate_id, version),
	CONSTRAINT candidate_profile_status_check
		CHECK (status IN ('draft', 'confirmed')),
	CONSTRAINT candidate_profile_confirmation_check
		CHECK (
			(status = 'draft' AND confirmed_at IS NULL)
			OR (status = 'confirmed' AND confirmed_at IS NOT NULL)
		)
);

CREATE TABLE IF NOT EXISTS cv_extraction_jobs (
	job_id UUID PRIMARY KEY,
	candidate_id UUID NOT NULL REFERENCES candidates(candidate_id) ON DELETE CASCADE,
	status VARCHAR(20) NOT NULL DEFAULT 'queued',
	error_info JSONB,
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	started_at TIMESTAMPTZ,
	completed_at TIMESTAMPTZ,
	model_name TEXT,
	model_version TEXT,
	CONSTRAINT cv_extraction_job_status_check
		CHECK (status IN ('queued', 'processing', 'completed', 'failed'))
);

CREATE TABLE IF NOT EXISTS candidate_profile_drafts (
	draft_id UUID PRIMARY KEY,
	candidate_id UUID NOT NULL REFERENCES candidates(candidate_id) ON DELETE CASCADE,
	extraction_job_id UUID NOT NULL REFERENCES cv_extraction_jobs(job_id) ON DELETE CASCADE,
	structured_draft JSONB NOT NULL,
	validation_status VARCHAR(20) NOT NULL DEFAULT 'pending',
	model_name TEXT,
	model_version TEXT,
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	CONSTRAINT candidate_profile_draft_validation_check
		CHECK (validation_status IN ('pending', 'valid', 'invalid'))
);
