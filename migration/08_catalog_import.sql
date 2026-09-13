-- Durable approval-bound insert-only imports for ESTADO=NEW catalog rows.
CREATE TABLE IF NOT EXISTS catalog_import_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    source_snapshot_id TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    canonical_payload TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending','approved','used','failed')),
    github_repository TEXT NOT NULL,
    github_pr_number INTEGER NOT NULL,
    github_head_sha TEXT NOT NULL,
    github_approval_count INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    used_at TIMESTAMP
);
CREATE TABLE IF NOT EXISTS catalog_import_row_audits (
    id BIGSERIAL PRIMARY KEY,
    snapshot_id TEXT NOT NULL REFERENCES catalog_import_snapshots(snapshot_id),
    code TEXT NOT NULL,
    result_status TEXT NOT NULL CHECK (result_status IN ('accepted','created','rejected','failed')),
    reason TEXT,
    before_values TEXT,
    after_values TEXT,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_catalog_import_rows_snapshot ON catalog_import_row_audits(snapshot_id);
