"""API-DISANO release module.

This module is part of the reviewed BC3/PostgreSQL release.
"""

from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError

from app.infrastructure.models.enrichment import (
    BC3EnrichmentJobItemModel,
    BC3EnrichmentJobModel,
)


MIGRATION_PATH = Path(__file__).parents[2] / "migration" / "03_add_bc3_enrichment_jobs.sql"


def test_enrichment_models_define_expected_tables_and_constraints() -> None:
    """Test."""
    job_table = BC3EnrichmentJobModel.__table__
    item_table = BC3EnrichmentJobItemModel.__table__

    assert job_table.name == "bc3_enrichment_jobs"
    assert item_table.name == "bc3_enrichment_job_items"
    assert {column.name for column in job_table.columns} == {
        "job_id",
        "idempotency_key",
        "request_hash",
        "status",
        "source_snapshot_id",
        "requested_by",
        "total_items",
        "updated_items",
        "unchanged_items",
        "missing_items",
        "created_at",
        "completed_at",
    }
    assert {
        "bc3_descripcion_corta",
        "bc3_descripcion_larga",
        "bc3_descripcion_completa",
        "bc3_product_type",
    } <= {column.name for column in item_table.columns}
    assert any(
        constraint.name == "uq_bc3_enrichment_jobs_idempotency_key"
        for constraint in job_table.constraints
    )
    assert any(
        constraint.name == "uq_bc3_enrichment_job_items_job_id_codigo"
        for constraint in item_table.constraints
    )
    assert any(
        foreign_key.target_fullname == "bc3_enrichment_jobs.job_id"
        for foreign_key in next(iter(item_table.foreign_key_constraints)).elements
    )


def _apply_migration(connection: Connection) -> None:
    """Apply migration."""
    statements = [statement.strip() for statement in MIGRATION_PATH.read_text().split(";")]
    for statement in statements:
        if statement:
            connection.execute(text(statement))


def test_migration_creates_schema_indexes_and_rejects_duplicate_idempotency_key() -> None:
    """Test."""
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _apply_migration(connection)
        _apply_migration(connection)
        inspector = inspect(connection)

        assert {"bc3_enrichment_jobs", "bc3_enrichment_job_items"} <= set(
            inspector.get_table_names()
        )
        job_indexes = {index["name"] for index in inspector.get_indexes("bc3_enrichment_jobs")}
        item_indexes = {
            index["name"] for index in inspector.get_indexes("bc3_enrichment_job_items")
        }
        assert {
            "ix_bc3_enrichment_jobs_idempotency_key",
            "ix_bc3_enrichment_jobs_status_created_at",
        } <= job_indexes
        assert {
            "ix_bc3_enrichment_job_items_job_id_codigo",
        } <= item_indexes

        connection.execute(
            text(
                "INSERT INTO bc3_enrichment_jobs "
                "(job_id, idempotency_key, request_hash, status, total_items, "
                "updated_items, unchanged_items, missing_items) "
                "VALUES (:job_id, :key, :request_hash, :status, 1, 0, 0, 0)"
            ),
            {
                "job_id": "job-1",
                "key": "same-request",
                "request_hash": "hash-1",
                "status": "pending",
            },
        )
        with pytest.raises(IntegrityError):
            connection.execute(
                text(
                    "INSERT INTO bc3_enrichment_jobs "
                    "(job_id, idempotency_key, request_hash, status, total_items, "
                    "updated_items, unchanged_items, missing_items) "
                    "VALUES ('job-2', 'same-request', 'hash-2', 'pending', 1, 0, 0, 0)"
                )
            )

        with pytest.raises(IntegrityError):
            connection.execute(
                text(
                    "INSERT INTO bc3_enrichment_jobs "
                    "(job_id, idempotency_key, request_hash, status, total_items, "
                    "updated_items, unchanged_items, missing_items) "
                    "VALUES ('job-3', 'other-request', 'hash-3', 'not-a-status', 1, 0, 0, 0)"
                )
            )

        with pytest.raises(IntegrityError):
            connection.execute(
                text(
                    "INSERT INTO bc3_enrichment_job_items "
                    "(job_id, codigo, result_status) "
                    "VALUES ('job-1', 'P-1', 'not-a-result')"
                )
            )
