"""PostgreSQL integration coverage for recovered catalog-import persistence."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker

from app.application.dto.catalog_import import (
    CatalogImportRequest,
    CatalogProductRow,
    catalog_payload_hash,
)
from app.application.services.github_approval import (
    GitHubApprovalEvidence,
    GitHubApprovalReference,
)
from app.infrastructure.models.catalog_import import (
    CatalogImportRowAuditModel,
    CatalogImportSnapshotModel,
)
from app.infrastructure.models.producto import ProductoRawModel
from app.infrastructure.repositories.producto import SQLAlchemyProductoRepository


@pytest.fixture
def catalog_recovery_context(sqlalchemy_session):
    """Create unique default GitHub-review catalog-import data."""
    actor_id = f"catalog-recovery-test-{uuid4().hex}"
    code = f"TEST-CATALOG-RECOVERY-{uuid4().hex[:12]}"
    reference = GitHubApprovalReference(
        repository="acme/catalog",
        pull_request_number=1000 + int(uuid4().hex[:6], 16) % 8000,
        head_sha="b" * 40,
    )
    request = CatalogImportRequest(
        source_snapshot_id=f"source-{uuid4().hex}",
        source_hash="c" * 64,
        github_pr=reference,
        rows=[
            CatalogProductRow(
                code=code,
                brand="Synthetic Brand",
                description="Synthetic catalog product",
                pvp=12.5,
                estado="NEW",
                bc3_descripcion_corta_ca="Distinct Catalan short",
                bc3_descripcion_larga_ca="Distinct Catalan long",
                bc3_descripcion_corta_gl="Distinct Galician short",
                bc3_descripcion_larga_gl="Distinct Galician long",
            )
        ],
    )
    yield sqlalchemy_session, actor_id, code, request, reference

    cleanup = sessionmaker(bind=sqlalchemy_session.get_bind(), expire_on_commit=False)()
    try:
        cleanup.rollback()
        snapshot_ids = [
            row.snapshot_id
            for row in cleanup.query(CatalogImportSnapshotModel).filter_by(actor_id=actor_id)
        ]
        if snapshot_ids:
            cleanup.query(CatalogImportRowAuditModel).filter(
                CatalogImportRowAuditModel.snapshot_id.in_(snapshot_ids)
            ).delete(synchronize_session=False)
            cleanup.query(CatalogImportSnapshotModel).filter(
                CatalogImportSnapshotModel.snapshot_id.in_(snapshot_ids)
            ).delete(synchronize_session=False)
        cleanup.query(ProductoRawModel).filter_by(codigo=code).delete(synchronize_session=False)
        cleanup.commit()
    finally:
        cleanup.close()


def _new_session(sqlalchemy_session):
    return sessionmaker(bind=sqlalchemy_session.get_bind(), expire_on_commit=False)()


def test_catalog_recovery_persists_default_github_review_and_translations(
    catalog_recovery_context,
):
    sqlalchemy_session, actor_id, code, request, reference = catalog_recovery_context
    preview_session = _new_session(sqlalchemy_session)
    try:
        preview = SQLAlchemyProductoRepository(preview_session).catalog_import_preview(
            snapshot_id=str(uuid4()),
            actor_id=actor_id,
            request=request,
            accepted=request.rows,
            rejected=[],
        )
    finally:
        preview_session.close()

    approval_session = _new_session(sqlalchemy_session)
    try:
        SQLAlchemyProductoRepository(approval_session).catalog_import_approve(
            preview["snapshot_id"],
            actor_id,
            reference,
            GitHubApprovalEvidence(
                repository=reference.repository,
                pull_request_number=reference.pull_request_number,
                head_sha=reference.head_sha,
                approval_count=1,
                verified_at=datetime.now(timezone.utc),
            ),
        )
    finally:
        approval_session.close()

    idempotency_key = f"recovery-{uuid4().hex}"
    apply_session = _new_session(sqlalchemy_session)
    try:
        result = SQLAlchemyProductoRepository(apply_session).catalog_import_apply(
            snapshot_id=preview["snapshot_id"],
            actor_id=actor_id,
            request=request,
            idempotency_key=idempotency_key,
            expected_payload_hash=catalog_payload_hash(request.rows),
        )
    finally:
        apply_session.close()

    assert result["status"] == "completed"
    assert result["created_codes"] == [code]
    observation = _new_session(sqlalchemy_session)
    try:
        product = observation.query(ProductoRawModel).filter_by(codigo=code).one()
        product_count = observation.query(ProductoRawModel).filter_by(codigo=code).count()
        audit_count = (
            observation.query(CatalogImportRowAuditModel)
            .filter_by(snapshot_id=preview["snapshot_id"], result_status="created")
            .count()
        )
        assert {
            "bc3_descripcion_corta_ca": product.bc3_descripcion_corta_ca,
            "bc3_descripcion_larga_ca": product.bc3_descripcion_larga_ca,
            "bc3_descripcion_corta_gl": product.bc3_descripcion_corta_gl,
            "bc3_descripcion_larga_gl": product.bc3_descripcion_larga_gl,
        } == {
            "bc3_descripcion_corta_ca": "Distinct Catalan short",
            "bc3_descripcion_larga_ca": "Distinct Catalan long",
            "bc3_descripcion_corta_gl": "Distinct Galician short",
            "bc3_descripcion_larga_gl": "Distinct Galician long",
        }
    finally:
        observation.rollback()
        observation.close()

    replay_session = _new_session(sqlalchemy_session)
    try:
        replay = SQLAlchemyProductoRepository(replay_session).catalog_import_apply(
            snapshot_id=preview["snapshot_id"],
            actor_id=actor_id,
            request=request,
            idempotency_key=idempotency_key,
            expected_payload_hash=catalog_payload_hash(request.rows),
        )
    finally:
        replay_session.close()

    assert replay == result
    observation = _new_session(sqlalchemy_session)
    try:
        assert observation.query(ProductoRawModel).filter_by(codigo=code).count() == product_count
        assert (
            observation.query(CatalogImportRowAuditModel)
            .filter_by(snapshot_id=preview["snapshot_id"], result_status="created")
            .count()
            == audit_count
        )
    finally:
        observation.rollback()
        observation.close()
