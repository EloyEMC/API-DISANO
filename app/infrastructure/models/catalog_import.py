"""Immutable catalog import snapshots and per-row audit records."""

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)

from app.infrastructure.models.producto import Base


class CatalogImportSnapshotModel(Base):
    """Persist an approval-bound catalog import snapshot."""

    __tablename__ = "catalog_import_snapshots"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'used', 'failed')",
            name="ck_catalog_import_status",
        ),
        UniqueConstraint("idempotency_key", name="uq_catalog_import_idempotency"),
    )
    snapshot_id = Column(String, primary_key=True)
    idempotency_key = Column(String, nullable=False)
    source_snapshot_id = Column(String, nullable=False)
    source_hash = Column(String, nullable=False)
    payload_hash = Column(String, nullable=False)
    canonical_payload = Column(Text, nullable=False)
    actor_id = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    github_repository = Column(String, nullable=False)
    github_pr_number = Column(Integer, nullable=False)
    github_head_sha = Column(String, nullable=False)
    approval_mode = Column(String, nullable=True)
    github_approval_count = Column(Integer)
    github_approval_verified_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    approved_at = Column(DateTime)
    used_at = Column(DateTime)


class CatalogImportRowAuditModel(Base):
    """Persist per-row catalog import audit information."""

    __tablename__ = "catalog_import_row_audits"
    __table_args__ = (
        CheckConstraint(
            "result_status IN ('accepted', 'created', 'rejected', 'failed')",
            name="ck_catalog_import_row_status",
        ),
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String, nullable=False)
    code = Column(String, nullable=False)
    result_status = Column(String, nullable=False)
    reason = Column(String)
    before_values = Column(JSON)
    after_values = Column(JSON)
    error_message = Column(String)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
