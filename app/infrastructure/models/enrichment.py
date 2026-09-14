"""Durable BC3 enrichment job and audit records."""

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)

from app.infrastructure.models.producto import Base


class BC3EnrichmentPreviewModel(Base):
    """Immutable, expiring authorization snapshot for one proposed batch."""

    __tablename__ = "bc3_enrichment_previews"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'used', 'expired')",
            name="ck_bc3_enrichment_previews_status",
        ),
        Index("ix_bc3_enrichment_previews_expires_status", "expires_at", "status"),
    )

    preview_id = Column(String, primary_key=True, nullable=False)
    payload_hash = Column(String, nullable=False)
    canonical_payload = Column(String, nullable=False)
    source_snapshot_id = Column(String, nullable=False)
    actor_id = Column(String, nullable=False)
    scope = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    expires_at = Column(DateTime, nullable=False)
    approved_at = Column(DateTime, nullable=True)
    approval_actor_id = Column(String, nullable=True)
    github_repository = Column(String, nullable=False)
    github_pr_number = Column(Integer, nullable=False)
    github_head_sha = Column(String, nullable=False)
    github_approval_count = Column(Integer, nullable=True)
    github_approval_verified_at = Column(DateTime, nullable=True)
    used_at = Column(DateTime, nullable=True)


class BC3EnrichmentPreviewItemModel(Base):
    """Snapshot values retained privately for compare-and-set apply."""

    __tablename__ = "bc3_enrichment_preview_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    preview_id = Column(String, ForeignKey("bc3_enrichment_previews.preview_id"), nullable=False)
    codigo = Column(String, nullable=False)
    current_values = Column(JSON, nullable=False)
    proposed_values = Column(JSON, nullable=False)
    __table_args__ = (UniqueConstraint("preview_id", "codigo", name="uq_bc3_preview_item"),)


class BC3EnrichmentJobModel(Base):
    """A durable request-level record for a BC3 enrichment operation."""

    __tablename__ = "bc3_enrichment_jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed')",
            name="ck_bc3_enrichment_jobs_status",
        ),
        Index("ix_bc3_enrichment_jobs_idempotency_key", "idempotency_key"),
        Index("ix_bc3_enrichment_jobs_status_created_at", "status", "created_at"),
        UniqueConstraint(
            "idempotency_key",
            name="uq_bc3_enrichment_jobs_idempotency_key",
        ),
    )

    job_id = Column(String, primary_key=True, nullable=False)
    idempotency_key = Column(String, nullable=False)
    request_hash = Column(String, nullable=False)
    status = Column(String, nullable=False)
    source_snapshot_id = Column(String, nullable=True)
    requested_by = Column(String, nullable=True)
    actor_id = Column(String, nullable=True)
    preview_id = Column(String, nullable=True)
    total_items = Column(Integer, nullable=False, default=0)
    updated_items = Column(Integer, nullable=False, default=0)
    unchanged_items = Column(Integer, nullable=False, default=0)
    missing_items = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    completed_at = Column(DateTime, nullable=True)


class BC3EnrichmentJobItemModel(Base):
    """A per-product proposed result retained as part of an enrichment job."""

    __tablename__ = "bc3_enrichment_job_items"
    __table_args__ = (
        CheckConstraint(
            "result_status IN ('pending', 'updated', 'unchanged', 'missing', 'failed')",
            name="ck_bc3_enrichment_job_items_result_status",
        ),
        Index("ix_bc3_enrichment_job_items_job_id_codigo", "job_id", "codigo"),
        UniqueConstraint(
            "job_id",
            "codigo",
            name="uq_bc3_enrichment_job_items_job_id_codigo",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String, ForeignKey("bc3_enrichment_jobs.job_id"), nullable=False)
    codigo = Column(String, nullable=False)
    bc3_descripcion_corta = Column(String, nullable=True)
    bc3_descripcion_larga = Column(String, nullable=True)
    bc3_descripcion_completa = Column(String, nullable=True)
    bc3_product_type = Column(String, nullable=True)
    bc3_descripcion_corta_ca = Column(String, nullable=True)
    bc3_descripcion_larga_ca = Column(String, nullable=True)
    bc3_descripcion_corta_gl = Column(String, nullable=True)
    bc3_descripcion_larga_gl = Column(String, nullable=True)
    source_pdf_hash = Column(String, nullable=True)
    ai_model = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    result_status = Column(String, nullable=False)
    error_message = Column(String, nullable=True)
    before_values = Column(JSON, nullable=True)
    after_values = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
