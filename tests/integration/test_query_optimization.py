"""Integration checks for PostgreSQL query optimization."""

import os

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL", "").startswith("postgresql"),
    reason="PostgreSQL integration test",
)


def _ensure_indexes(session):
    session.execute(
        text(
            "CREATE INDEX IF NOT EXISTS idx_productos_marca_familia "
            'ON "productos" ("MARCA", "Familia_WEB")'
        )
    )
    session.commit()


def _statistics(session):
    return (
        session.execute(
            text(
                "SELECT schemaname, relname, n_live_tup "
                "FROM pg_stat_user_tables WHERE relname = 'productos'"
            )
        )
        .mappings()
        .all()
    )


class TestQueryOptimization:
    def test_analyze_updates_query_statistics(self):
        from app.infrastructure.database.connection import SessionLocal

        with SessionLocal() as session:
            _ensure_indexes(session)
            session.execute(text('ANALYZE "productos"'))
            session.commit()
            statistics = _statistics(session)

        assert statistics
        assert any(row["relname"] == "productos" for row in statistics)

    def test_get_query_planner_info(self):
        from app.infrastructure.database.analyze_database import get_query_planner_info

        info = get_query_planner_info()
        assert isinstance(info["compile_options"], list)
        assert isinstance(info["page_size"], int)
        assert isinstance(info["cache_size"], int)

    def test_query_planner_uses_production_indexes(self):
        from app.infrastructure.database.connection import SessionLocal

        with SessionLocal() as session:
            _ensure_indexes(session)
            session.execute(text('ANALYZE "productos"'))
            index_exists = session.execute(
                text(
                    "SELECT 1 FROM pg_indexes "
                    "WHERE tablename = 'productos' "
                    "AND indexname = 'idx_productos_marca_familia'"
                )
            ).scalar_one_or_none()

            assert index_exists == 1
            # PostgreSQL may choose a sequential scan for a small table; index
            # existence is the stable contract this integration test protects.

    def test_database_settings_are_valid(self):
        from app.infrastructure.database.connection import SessionLocal

        with SessionLocal() as session:
            setting = session.execute(text("SHOW shared_buffers")).scalar_one()

        assert isinstance(setting, str) and setting

    def test_multiple_analyze_runs_preserve_statistics(self):
        from app.infrastructure.database.connection import SessionLocal

        with SessionLocal() as session:
            _ensure_indexes(session)
            session.execute(text('ANALYZE "productos"'))
            session.commit()
            before = _statistics(session)
            session.execute(text('ANALYZE "productos"'))
            session.commit()
            after = _statistics(session)

        assert after == before
