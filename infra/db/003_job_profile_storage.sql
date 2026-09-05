CREATE TABLE IF NOT EXISTS job_profiles (
    job_id UUID PRIMARY KEY REFERENCES canonical_jobs(job_id) ON DELETE CASCADE,
    profile JSONB NOT NULL,
    analysis_version TEXT NOT NULL,
    model_version TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
