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

CREATE INDEX IF NOT EXISTS ix_cv_extraction_jobs_candidate_id
    ON cv_extraction_jobs (candidate_id);

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

CREATE INDEX IF NOT EXISTS ix_candidate_profile_drafts_candidate_id
    ON candidate_profile_drafts (candidate_id);

CREATE INDEX IF NOT EXISTS ix_candidate_profile_drafts_extraction_job_id
    ON candidate_profile_drafts (extraction_job_id);
