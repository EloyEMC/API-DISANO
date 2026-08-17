"""Integration checks for the production PostgreSQL indexes."""

import os

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL", "").startswith("postgresql"),
    reason="PostgreSQL integration test",
)

EXPECTED_INDEXES = {
    "idx_productos_codigo",
    "idx_productos_descripcion",
    "idx_productos_marca",
    "idx_productos_familia",
    "idx_productos_marca_familia",
    "idx_productos_bc3_type",
    "idx_productos_pvp",
}


def _index_rows(session):
    return (
        session.execute(
            text(
                """
            SELECT indexname AS name, tablename AS tbl, indexdef AS sql
            FROM pg_indexes
            WHERE schemaname = current_schema() AND indexname LIKE 'idx_productos_%'
            ORDER BY indexname
            """
            )
        )
        .mappings()
        .all()
    )


def _ensure_production_indexes(session):
    statements = {
        "idx_productos_codigo": (
            "CREATE INDEX IF NOT EXISTS idx_productos_codigo " 'ON "productos" ("CÓDIGO")'
        ),
        "idx_productos_descripcion": (
            "CREATE INDEX IF NOT EXISTS idx_productos_descripcion " 'ON "productos" ("DESCRIPCION")'
        ),
        "idx_productos_marca": (
            "CREATE INDEX IF NOT EXISTS idx_productos_marca " 'ON "productos" ("MARCA")'
        ),
        "idx_productos_familia": (
            "CREATE INDEX IF NOT EXISTS idx_productos_familia " 'ON "productos" ("Familia_WEB")'
        ),
        "idx_productos_marca_familia": (
            "CREATE INDEX IF NOT EXISTS idx_productos_marca_familia "
            'ON "productos" ("MARCA", "Familia_WEB")'
        ),
        "idx_productos_bc3_type": (
            "CREATE INDEX IF NOT EXISTS idx_productos_bc3_type "
            'ON "productos" ("bc3_product_type")'
        ),
        "idx_productos_pvp": (
            "CREATE INDEX IF NOT EXISTS idx_productos_pvp " 'ON "productos" ("PVP_26_01_26")'
        ),
    }
    for statement in statements.values():
        session.execute(text(statement))
    session.commit()


class TestDatabaseIndexes:
    def test_production_indexes_exist_on_base_table(self):
        from app.infrastructure.database.connection import SessionLocal

        with SessionLocal() as session:
            _ensure_production_indexes(session)
            rows = _index_rows(session)

        assert {row["name"] for row in rows} >= EXPECTED_INDEXES
        assert {row["tbl"] for row in rows if row["name"] in EXPECTED_INDEXES} == {"productos"}

    def test_production_index_definitions_use_expected_columns(self):
        from app.infrastructure.database.connection import SessionLocal

        with SessionLocal() as session:
            _ensure_production_indexes(session)
            definitions = {
                row["name"]: row["sql"]
                for row in _index_rows(session)
                if row["name"] in EXPECTED_INDEXES
            }

        assert '"CÓDIGO"' in definitions["idx_productos_codigo"]
        assert '"DESCRIPCION"' in definitions["idx_productos_descripcion"]
        assert '"MARCA", "Familia_WEB"' in definitions["idx_productos_marca_familia"]

    def test_query_plans_reference_production_indexes(self):
        from app.infrastructure.database.connection import SessionLocal

        with SessionLocal() as session:
            _ensure_production_indexes(session)
            session.execute(text("SET LOCAL enable_seqscan = off"))
            plan = (
                session.execute(
                    text(
                        'EXPLAIN (FORMAT TEXT) SELECT * FROM "productos" '
                        'WHERE "CÓDIGO" = :codigo AND "MARCA" = :marca'
                    ),
                    {"codigo": "missing", "marca": "missing"},
                )
                .scalars()
                .all()
            )

        assert plan
        assert any("idx_productos" in line for line in plan)
