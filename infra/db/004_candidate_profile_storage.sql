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

CREATE INDEX IF NOT EXISTS ix_candidate_profile_versions_status
    ON candidate_profile_versions (status);
