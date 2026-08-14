CREATE TABLE IF NOT EXISTS bc3_enrichment_jobs (
    job_id TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    request_hash TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    source_snapshot_id TEXT,
    requested_by TEXT,
    total_items INTEGER NOT NULL DEFAULT 0,
    updated_items INTEGER NOT NULL DEFAULT 0,
    unchanged_items INTEGER NOT NULL DEFAULT 0,
    missing_items INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bc3_enrichment_job_items (
    id INTEGER PRIMARY KEY,
    job_id TEXT NOT NULL,
    codigo TEXT NOT NULL,
    bc3_descripcion_corta TEXT,
    bc3_descripcion_larga TEXT,
    bc3_descripcion_completa TEXT,
    bc3_product_type TEXT,
    source_pdf_hash TEXT,
    ai_model TEXT,
    confidence REAL,
    result_status TEXT NOT NULL CHECK (
        result_status IN ('pending', 'updated', 'unchanged', 'missing', 'failed')
    ),
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_bc3_enrichment_job_items_job
        FOREIGN KEY (job_id) REFERENCES bc3_enrichment_jobs(job_id),
    CONSTRAINT uq_bc3_enrichment_job_items_job_id_codigo UNIQUE (job_id, codigo)
);

CREATE INDEX IF NOT EXISTS ix_bc3_enrichment_jobs_idempotency_key
    ON bc3_enrichment_jobs (idempotency_key);
CREATE INDEX IF NOT EXISTS ix_bc3_enrichment_jobs_status_created_at
    ON bc3_enrichment_jobs (status, created_at);
CREATE INDEX IF NOT EXISTS ix_bc3_enrichment_job_items_job_id_codigo
    ON bc3_enrichment_job_items (job_id, codigo);
