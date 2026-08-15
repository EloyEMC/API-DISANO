"""Durable BC3 enrichment job and audit records."""

from sqlalchemy import (
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
    source_pdf_hash = Column(String, nullable=True)
    ai_model = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    result_status = Column(String, nullable=False)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
