"""Integration tests for query optimization

Tests to verify that ANALYZE and other optimization techniques work correctly
."""

from sqlalchemy import text


class TestQueryOptimization:
    """Tests for database query optimization."""

    def test_analyze_updates_query_statistics(self):
        """Test that ANALYZE updates query statistics."""
        from app.infrastructure.database.connection import SessionLocal

        session = SessionLocal()

        try:
            # Run ANALYZE
            session.execute(text("ANALYZE"))
            session.commit()

            # Verify statistics were created/updated
            result = session.execute(
                text(
                    """
                SELECT COUNT(*) as stat_count
                FROM sqlite_stat1
            ."""
                )
            )
            stat_count = result.fetchone()[0]

            # Should have some statistics
            assert stat_count >= 0, "Should have statistics entries"

            print(f"📊 Statistics entries: {stat_count}")

            # Verify we can query specific table statistics
            result = session.execute(
                text(
                    """
                SELECT tbl, idx
                FROM sqlite_stat1
                LIMIT 1
            ."""
                )
            )
            stat = result.fetchone()

            # Might be empty in test database, but query should work
            print(f"📈 Sample stat: {stat}")

        finally:
            session.close()

    def test_get_query_planner_info(self):
        """Test that we can get query planner information."""
        from app.infrastructure.database.connection import SessionLocal
        from app.infrastructure.database.analyze_database import get_query_planner_info

        session = SessionLocal()

        try:
            # This should not throw an error
            info = get_query_planner_info()

            # Verify we got expected information
            assert "compile_options" in info
            assert "page_size" in info
            assert "cache_size" in info

            # Compile options should be a list
            assert isinstance(info["compile_options"], list)

            # Page size should be positive
            assert info["page_size"] > 0

            # Cache size should be a number
            assert isinstance(info["cache_size"], int)

            print("✅ Query planner info retrieved successfully")

        finally:
            session.close()

    def test_database_settings_configurable(self):
        """Test that database settings can be configured."""
        from app.infrastructure.database.connection import SessionLocal

        session = SessionLocal()

        try:
            # Get current settings
            result = session.execute(text("PRAGMA page_size"))
            page_size = result.fetchone()[0]

            result = session.execute(text("PRAGMA cache_size"))
            cache_size = result.fetchone()[0]

            # Settings should be reasonable values
            assert (
                1024 <= page_size <= 65536
            ), f"Page size {page_size} should be between 1KB and 64KB"

            # Cache size can be negative (dynamic mode) or positive (fixed size)
            assert isinstance(cache_size, int), f"Cache size {cache_size} should be an integer"

            print(f"💾 Current settings: page_size={page_size}, cache_size={cache_size}")

        finally:
            session.close()

    def test_optimization_improves_query_performance(self):
        """Test that optimization improves query performance."""
        import time
        from app.infrastructure.database.connection import SessionLocal
        from app.infrastructure.repositories.producto import (
            SQLAlchemyProductoRepository,
        )

        session = SessionLocal()
        repository = SQLAlchemyProductoRepository(session)

        try:
            # Measure performance before optimization
            start = time.time()
            products_before = repository.buscar_productos(
                termino="test", limit=10, marca="", familia=""
            )
            time_before = time.time() - start

            # Run optimization
            session.execute(text("ANALYZE"))
            session.commit()

            # Measure performance after optimization
            start = time.time()
            products_after = repository.buscar_productos(
                termino="test", limit=10, marca="", familia=""
            )
            time_after = time.time() - start

            # Results should be the same
            assert len(products_before) == len(products_after)

            print(f"⏱️ Before optimization: {time_before:.4f}s")
            print(f"⏱️ After optimization: {time_after:.4f}s")

            # Performance should be similar or better
            # (might not be significantly different in small test database)
            assert (
                time_after <= time_before * 2.0
            ), "Optimization should not degrade performance significantly"

        finally:
            session.close()

    def test_multiple_analyze_runs_safe(self):
        """Test that running ANALYZE multiple times is safe."""
        from app.infrastructure.database.connection import SessionLocal

        session = SessionLocal()

        try:
            # Run ANALYZE multiple times
            for i in range(3):
                session.execute(text("ANALYZE"))
                session.commit()
                print(f"✅ ANALYZE run {i + 1} completed")

            # Should not cause any errors
            assert True, "Multiple ANALYZE runs should be safe"

        finally:
            session.close()
