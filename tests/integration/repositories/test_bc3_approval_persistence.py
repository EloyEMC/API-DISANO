"""Real SQLAlchemy regression coverage for the approval-bound BC3 workflow."""

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.application.dto.bc3_enrichment import hash_bc3_enrichment_items
from app.application.services.github_approval import (
    GitHubApprovalEvidence,
    GitHubApprovalReference,
)
from app.config import get_settings
from app.infrastructure.models.enrichment import (
    BC3EnrichmentJobItemModel,
    BC3EnrichmentJobModel,
    BC3EnrichmentPreviewItemModel,
    BC3EnrichmentPreviewModel,
)
from app.infrastructure.models.producto import ProductoRawModel
from app.infrastructure.repositories.producto import SQLAlchemyProductoRepository


MIGRATION_07 = Path(__file__).resolve().parents[3] / "migration" / "07_bc3_approval_snapshots.sql"


@pytest.mark.skipif(
    not os.environ.get("DISANO_MIGRATION_TEST_DATABASE_URL"),
    reason="requires an explicitly disposable PostgreSQL database",
)
def test_migration_07_upgrades_legacy_ids_and_job_description_columns():
    """Upgrade legacy rows, then exercise both generated IDs through SQLAlchemy."""
    disposable_url = make_url(os.environ["DISANO_MIGRATION_TEST_DATABASE_URL"])
    database_name = f"disano_migration_{uuid4().hex}"
    admin_engine = create_engine(
        disposable_url.set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    quoted_database_name = admin_engine.dialect.identifier_preparer.quote(database_name)
    database_created = False
    engine = None
    try:
        with admin_engine.connect() as connection:
            connection.execute(text(f"CREATE DATABASE {quoted_database_name}"))
        database_created = True
        engine = create_engine(disposable_url.set(database=database_name))
        with engine.begin() as connection:
            connection.execute(text("DROP TABLE IF EXISTS bc3_enrichment_preview_items CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS bc3_enrichment_job_items CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS bc3_enrichment_jobs CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS bc3_enrichment_previews CASCADE"))
            connection.execute(
                text(
                    """
                CREATE TABLE bc3_enrichment_previews (
                    preview_id TEXT PRIMARY KEY, payload_hash TEXT NOT NULL,
                    canonical_payload TEXT NOT NULL, source_snapshot_id TEXT NOT NULL,
                    actor_id TEXT NOT NULL, scope TEXT NOT NULL, status TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL, github_repository TEXT NOT NULL,
                    github_pr_number INTEGER NOT NULL, github_head_sha TEXT NOT NULL
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE bc3_enrichment_jobs (
                    job_id TEXT PRIMARY KEY, idempotency_key TEXT NOT NULL,
                    request_hash TEXT NOT NULL, status TEXT NOT NULL
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE bc3_enrichment_job_items (
                    id INTEGER PRIMARY KEY, job_id TEXT NOT NULL, codigo TEXT NOT NULL,
                    bc3_descripcion_corta TEXT, bc3_descripcion_larga TEXT,
                    bc3_descripcion_completa TEXT, bc3_product_type TEXT,
                    source_pdf_hash TEXT, ai_model TEXT, confidence DOUBLE PRECISION,
                    result_status TEXT NOT NULL, error_message TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                CREATE TABLE bc3_enrichment_preview_items (
                    id INTEGER PRIMARY KEY, preview_id TEXT NOT NULL, codigo TEXT NOT NULL,
                    current_values TEXT NOT NULL, proposed_values TEXT NOT NULL
                )
            """
                )
            )
            connection.execute(
                text(
                    """
                INSERT INTO bc3_enrichment_jobs VALUES ('job-legacy', 'key-legacy', 'hash', 'pending')
            """
                )
            )
            connection.execute(
                text(
                    """
                INSERT INTO bc3_enrichment_job_items
                    (id, job_id, codigo, result_status) VALUES (41, 'job-legacy', 'old', 'pending')
            """
                )
            )
            connection.execute(
                text(
                    """
                INSERT INTO bc3_enrichment_preview_items
                    (id, preview_id, codigo, current_values, proposed_values)
                VALUES (73, 'preview-legacy', 'old', '{}', '{}')
            """
                )
            )
            connection.execute(text(MIGRATION_07.read_text()))
            connection.execute(text(MIGRATION_07.read_text()))

            assert (
                connection.execute(
                    text("SELECT COUNT(*) FROM bc3_enrichment_job_items WHERE id = 41")
                ).scalar_one()
                == 1
            )
            assert (
                connection.execute(
                    text("SELECT COUNT(*) FROM bc3_enrichment_preview_items WHERE id = 73")
                ).scalar_one()
                == 1
            )
            for table in ("bc3_enrichment_job_items", "bc3_enrichment_preview_items"):
                generated = connection.execute(
                    text(
                        """
                    SELECT c.is_identity = 'YES' OR c.column_default LIKE 'nextval%'
                    FROM information_schema.columns c
                    WHERE c.table_name = :table AND c.column_name = 'id'
                """
                    ),
                    {"table": table},
                ).scalar_one()
                assert generated

            session = sessionmaker(bind=connection, expire_on_commit=False)()
            try:
                item = BC3EnrichmentJobItemModel(
                    job_id="job-legacy",
                    codigo="new",
                    result_status="pending",
                    bc3_descripcion_corta_ca=None,
                    bc3_descripcion_larga_ca="largo ca",
                    bc3_descripcion_corta_gl="curto",
                    bc3_descripcion_larga_gl=None,
                )
                session.add(item)
                session.flush()
                assert item.id > 41
            finally:
                session.close()
    finally:
        if engine is not None:
            engine.dispose()
        try:
            if database_created:
                with admin_engine.connect() as connection:
                    connection.execute(text(f"DROP DATABASE {quoted_database_name}"))
        finally:
            admin_engine.dispose()


@pytest.fixture
def approval_context(sqlalchemy_session, monkeypatch):
    """Use the sanitized PostgreSQL fixture and restore its BC3 fields afterwards."""
    settings = get_settings()
    monkeypatch.setattr(settings, "bc3_approval_scope", "bc3-enrichment")
    monkeypatch.setattr(settings, "bc3_preview_ttl_seconds", 900)

    product = sqlalchemy_session.query(ProductoRawModel).filter_by(codigo="33036139").one()
    original = {
        field: getattr(product, field)
        for field in (
            "bc3_descripcion_corta",
            "bc3_descripcion_larga",
            "bc3_descripcion_completa",
        )
    }
    yield sqlalchemy_session, product.codigo, original
    # A repository failure leaves the transaction unusable until rollback;
    # clear it before teardown reads the database.
    sqlalchemy_session.rollback()
    for field, value in original.items():
        setattr(product, field, value)
    preview_ids = [
        row.preview_id
        for row in sqlalchemy_session.query(BC3EnrichmentPreviewModel).all()
        if row.actor_id == "isolated-test-actor"
    ]
    job_ids = [
        row.job_id
        for row in sqlalchemy_session.query(BC3EnrichmentJobModel).all()
        if row.actor_id == "isolated-test-actor"
    ]
    if job_ids:
        sqlalchemy_session.query(BC3EnrichmentJobItemModel).filter(
            BC3EnrichmentJobItemModel.job_id.in_(job_ids)
        ).delete(synchronize_session=False)
        sqlalchemy_session.query(BC3EnrichmentJobModel).filter(
            BC3EnrichmentJobModel.job_id.in_(job_ids)
        ).delete(synchronize_session=False)
    if preview_ids:
        sqlalchemy_session.query(BC3EnrichmentPreviewItemModel).filter(
            BC3EnrichmentPreviewItemModel.preview_id.in_(preview_ids)
        ).delete(synchronize_session=False)
        sqlalchemy_session.query(BC3EnrichmentPreviewModel).filter(
            BC3EnrichmentPreviewModel.preview_id.in_(preview_ids)
        ).delete(synchronize_session=False)
    try:
        sqlalchemy_session.commit()
    except Exception:
        sqlalchemy_session.rollback()
        raise


def _new_session(sqlalchemy_session):
    """Create a session matching the one-session-per-request HTTP dependency."""
    factory = sessionmaker(bind=sqlalchemy_session.get_bind(), expire_on_commit=False)
    return factory()


def _reference() -> GitHubApprovalReference:
    return GitHubApprovalReference(
        repository="acme/catalog", pull_request_number=42, head_sha="a" * 40
    )


def _evidence() -> GitHubApprovalEvidence:
    return GitHubApprovalEvidence(
        repository="acme/catalog",
        pull_request_number=42,
        head_sha="a" * 40,
        approval_count=1,
        verified_at=datetime.now(timezone.utc),
    )


def _create_preview(sqlalchemy_session, items):
    session = _new_session(sqlalchemy_session)
    try:
        return SQLAlchemyProductoRepository(session).create_bc3_preview(
            items, "isolated-test-actor", _reference().head_sha, _reference()
        )
    finally:
        session.close()


def _approve(sqlalchemy_session, preview_id):
    session = _new_session(sqlalchemy_session)
    try:
        SQLAlchemyProductoRepository(session).approve_bc3_preview(
            preview_id,
            "isolated-test-actor",
            "bc3-enrichment",
            _reference(),
            _evidence(),
        )
    finally:
        session.close()


def test_real_repository_preserves_approval_provenance_and_idempotency(approval_context):
    sqlalchemy_session, codigo, _ = approval_context
    items = [
        {
            "codigo": codigo,
            "bc3_descripcion_corta": "isolated short",
            "bc3_descripcion_larga": "isolated long",
            "bc3_descripcion_completa": "isolated complete",
        }
    ]

    preview = _create_preview(sqlalchemy_session, items)
    observation = _new_session(sqlalchemy_session)
    try:
        persisted = observation.get(BC3EnrichmentPreviewModel, preview["preview_id"])
        assert persisted is not None
        assert persisted.actor_id == "isolated-test-actor"
        assert persisted.payload_hash == hash_bc3_enrichment_items(items)
        assert persisted.expires_at > datetime.now(timezone.utc).replace(tzinfo=None)
    finally:
        observation.close()

    _approve(sqlalchemy_session, preview["preview_id"])
    action = _new_session(sqlalchemy_session)
    try:
        applied = SQLAlchemyProductoRepository(action).apply_bc3_enrichment(
            items,
            "isolated-idempotency-key",
            preview["preview_id"],
            "isolated-test-actor",
            _reference(),
        )
        assert applied["updated_codes"] == [codigo]
    finally:
        action.close()

    idempotency_observation = _new_session(sqlalchemy_session)
    try:
        assert (
            SQLAlchemyProductoRepository(idempotency_observation).apply_bc3_enrichment(
                items,
                "isolated-idempotency-key",
                preview["preview_id"],
                "isolated-test-actor",
                _reference(),
            )
            == applied
        )
    finally:
        idempotency_observation.close()

    observation = _new_session(sqlalchemy_session)
    try:
        product = SQLAlchemyProductoRepository(observation).get_private_by_codigo(codigo)
        assert product.bc3_descripcion_corta == "isolated short"
        assert product.bc3_descripcion_larga == "isolated long"
        assert product.bc3_descripcion_completa == "isolated complete"
    finally:
        observation.close()


def test_real_repository_rejects_approved_preview_drift(approval_context):
    sqlalchemy_session, codigo, _ = approval_context
    items = [{"codigo": codigo, "bc3_descripcion_corta": "drift target"}]
    preview = _create_preview(sqlalchemy_session, items)
    _approve(sqlalchemy_session, preview["preview_id"])

    mutation = _new_session(sqlalchemy_session)
    try:
        product = mutation.query(ProductoRawModel).filter_by(codigo=codigo).one()
        product.bc3_descripcion_corta = "unapproved drift"
        mutation.commit()
    finally:
        mutation.close()

    action = _new_session(sqlalchemy_session)
    try:
        with pytest.raises(ValueError, match="drifted"):
            SQLAlchemyProductoRepository(action).apply_bc3_enrichment(
                items,
                "isolated-drift-key",
                preview["preview_id"],
                "isolated-test-actor",
                _reference(),
            )
    finally:
        action.close()


def test_real_repository_rejects_expired_preview(approval_context):
    sqlalchemy_session, codigo, _ = approval_context
    items = [{"codigo": codigo, "bc3_descripcion_corta": "expired"}]
    preview = _create_preview(sqlalchemy_session, items)

    mutation = _new_session(sqlalchemy_session)
    try:
        expired = mutation.get(BC3EnrichmentPreviewModel, preview["preview_id"])
        expired.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
        mutation.commit()
    finally:
        mutation.close()

    action = _new_session(sqlalchemy_session)
    try:
        with pytest.raises(ValueError, match="not eligible"):
            SQLAlchemyProductoRepository(action).approve_bc3_preview(
                preview["preview_id"],
                "isolated-test-actor",
                "bc3-enrichment",
                _reference(),
                _evidence(),
            )
    finally:
        action.close()
