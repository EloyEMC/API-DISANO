"""PostgreSQL integration coverage for catalog-import approval modes."""

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
from app.config import get_settings
from app.infrastructure.models.catalog_import import (
    CatalogImportRowAuditModel,
    CatalogImportSnapshotModel,
)
from app.infrastructure.models.producto import ProductoRawModel
from app.infrastructure.repositories.producto import SQLAlchemyProductoRepository


@pytest.fixture
def catalog_approval_context(sqlalchemy_session, monkeypatch):
    """Create unique catalog-import data and remove only this test's rows."""
    actor_id = f"catalog-mode-test-{uuid4().hex}"
    code = f"TEST-CATALOG-MODE-{uuid4().hex[:12]}"
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
    settings = get_settings()
    monkeypatch.setattr(settings, "bc3_approval_mode", "github_review")
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
    factory = sessionmaker(bind=sqlalchemy_session.get_bind(), expire_on_commit=False)
    return factory()


def _evidence(reference, mode, approval_count, verified_at=None):
    return GitHubApprovalEvidence(
        repository=reference.repository,
        pull_request_number=reference.pull_request_number,
        head_sha=reference.head_sha,
        approval_count=approval_count,
        verified_at=verified_at or datetime.now(timezone.utc),
        approval_mode=mode,
    )


def _create_preview(context):
    sqlalchemy_session, actor_id, _, request, _ = context
    session = _new_session(sqlalchemy_session)
    try:
        return SQLAlchemyProductoRepository(session).catalog_import_preview(
            snapshot_id=str(uuid4()),
            actor_id=actor_id,
            request=request,
            accepted=request.rows,
            rejected=[],
        )
    finally:
        session.close()


def _approve(context, snapshot_id, mode, approval_count, verified_at=None):
    sqlalchemy_session, actor_id, _, _, reference = context
    session = _new_session(sqlalchemy_session)
    try:
        SQLAlchemyProductoRepository(session).catalog_import_approve(
            snapshot_id,
            actor_id,
            reference,
            _evidence(reference, mode, approval_count, verified_at),
        )
    finally:
        session.close()


def _apply(context, snapshot_id, idempotency_key):
    sqlalchemy_session, actor_id, _, request, _ = context
    session = _new_session(sqlalchemy_session)
    try:
        return SQLAlchemyProductoRepository(session).catalog_import_apply(
            snapshot_id=snapshot_id,
            actor_id=actor_id,
            request=request,
            idempotency_key=idempotency_key,
            expected_payload_hash=catalog_payload_hash(request.rows),
        )
    finally:
        session.close()


def test_catalog_apply_rejects_mode_mismatch_before_product_audit_or_status_write(
    catalog_approval_context, monkeypatch
):
    context = catalog_approval_context
    sqlalchemy_session, actor_id, code, request, reference = context
    preview = _create_preview(context)
    _approve(context, preview["snapshot_id"], "github_review", 1)

    settings = get_settings()
    monkeypatch.setattr(settings, "bc3_approval_mode", "sole_maintainer")
    action = _new_session(sqlalchemy_session)
    try:
        with pytest.raises(ValueError, match="approved catalog import snapshot"):
            SQLAlchemyProductoRepository(action).catalog_import_apply(
                snapshot_id=preview["snapshot_id"],
                actor_id=actor_id,
                request=request,
                idempotency_key=f"mode-mismatch-{uuid4().hex}",
                expected_payload_hash=catalog_payload_hash(request.rows),
            )
    finally:
        action.rollback()
        action.close()

    observation = _new_session(sqlalchemy_session)
    try:
        snapshot = observation.get(CatalogImportSnapshotModel, preview["snapshot_id"])
        assert snapshot.status == "approved"
        assert snapshot.approval_mode == "github_review"
        assert observation.query(ProductoRawModel).filter_by(codigo=code).one_or_none() is None
        audits = (
            observation.query(CatalogImportRowAuditModel)
            .filter_by(snapshot_id=preview["snapshot_id"])
            .all()
        )
        assert [(audit.code, audit.result_status) for audit in audits] == [(code, "accepted")]
    finally:
        observation.rollback()
        observation.close()


def test_catalog_apply_persists_all_four_bc3_translation_values(
    catalog_approval_context, monkeypatch
):
    context = catalog_approval_context
    sqlalchemy_session, _, code, _, _ = context
    settings = get_settings()
    monkeypatch.setattr(settings, "bc3_approval_mode", "sole_maintainer")
    preview = _create_preview(context)
    _approve(context, preview["snapshot_id"], "sole_maintainer", None)

    result = _apply(context, preview["snapshot_id"], f"translations-{uuid4().hex}")
    assert result["created_codes"] == [code]

    observation = _new_session(sqlalchemy_session)
    try:
        product = observation.query(ProductoRawModel).filter_by(codigo=code).one()
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


def test_catalog_apply_sole_maintainer_persists_truthful_provenance_and_replays(
    catalog_approval_context, monkeypatch
):
    context = catalog_approval_context
    sqlalchemy_session, _, code, _, _ = context
    settings = get_settings()
    monkeypatch.setattr(settings, "bc3_approval_mode", "sole_maintainer")
    preview = _create_preview(context)
    _approve(context, preview["snapshot_id"], "sole_maintainer", None)

    observation = _new_session(sqlalchemy_session)
    try:
        snapshot = observation.get(CatalogImportSnapshotModel, preview["snapshot_id"])
        assert snapshot.approval_mode == "sole_maintainer"
        assert snapshot.github_approval_count is None
        assert snapshot.approved_at is not None
    finally:
        observation.rollback()
        observation.close()

    result = _apply(context, preview["snapshot_id"], f"sole-apply-{uuid4().hex}")
    assert result["status"] == "completed"
    assert result["created_codes"] == [code]


def test_catalog_approval_persists_verification_time_distinct_from_approval_time(
    catalog_approval_context, monkeypatch
):
    context = catalog_approval_context
    sqlalchemy_session, _, _, _, _ = context
    settings = get_settings()
    monkeypatch.setattr(settings, "bc3_approval_mode", "sole_maintainer")
    preview = _create_preview(context)
    verified_at = datetime(2024, 1, 2, 3, 4, 5, 678901, tzinfo=timezone.utc)

    _approve(
        context,
        preview["snapshot_id"],
        "sole_maintainer",
        None,
        verified_at=verified_at,
    )

    observation = _new_session(sqlalchemy_session)
    try:
        snapshot = observation.get(CatalogImportSnapshotModel, preview["snapshot_id"])
        assert snapshot.approved_at is not None
        assert snapshot.github_approval_verified_at == verified_at.replace(tzinfo=None)
        assert snapshot.approved_at != snapshot.github_approval_verified_at
    finally:
        observation.rollback()
        observation.close()


def test_catalog_apply_idempotent_replay_rejects_current_mode_mismatch_without_writes(
    catalog_approval_context, monkeypatch
):
    context = catalog_approval_context
    sqlalchemy_session, actor_id, code, request, _ = context
    settings = get_settings()
    monkeypatch.setattr(settings, "bc3_approval_mode", "sole_maintainer")
    preview = _create_preview(context)
    _approve(context, preview["snapshot_id"], "sole_maintainer", None)
    idempotency_key = f"sole-replay-{uuid4().hex}"
    _apply(context, preview["snapshot_id"], idempotency_key)

    monkeypatch.setattr(settings, "bc3_approval_mode", "github_review")
    action = _new_session(sqlalchemy_session)
    try:
        with pytest.raises(ValueError):
            SQLAlchemyProductoRepository(action).catalog_import_apply(
                snapshot_id=preview["snapshot_id"],
                actor_id=actor_id,
                request=request,
                idempotency_key=idempotency_key,
                expected_payload_hash=catalog_payload_hash(request.rows),
            )
    finally:
        action.rollback()
        action.close()

    observation = _new_session(sqlalchemy_session)
    try:
        snapshot = observation.get(CatalogImportSnapshotModel, preview["snapshot_id"])
        assert snapshot.status == "used"
        assert snapshot.approval_mode == "sole_maintainer"
        assert observation.query(ProductoRawModel).filter_by(codigo=code).count() == 1
        assert (
            observation.query(CatalogImportRowAuditModel)
            .filter_by(snapshot_id=preview["snapshot_id"], result_status="created")
            .count()
            == 1
        )
    finally:
        observation.rollback()
        observation.close()
