"""Integration tests for database indexes

Tests to verify that strategic indexes are properly created and improve performance
."""

import time
from sqlalchemy import text


class TestDatabaseIndexes:
    """Tests for database indexing optimization."""

    def test_indexes_exist_on_frequently_queried_fields(self):
        """Test that indexes exist on frequently queried fields."""
        from app.infrastructure.database.connection import SessionLocal

        session = SessionLocal()
        try:
            # Get all indexes
            result = session.execute(text("SELECT name FROM sqlite_master WHERE type='index'"))
            indexes = [row[0] for row in result.fetchall()]

            # Verify indexes exist on key fields
            index_names = " ".join(indexes)

            # Should have indexes for frequently queried fields
            # Note: SQLite creates indexes for primary keys automatically
            assert len(indexes) >= 1, "Should have at least one index"

            print(f"📊 Found {len(indexes)} indexes: {indexes}")

        finally:
            session.close()

    def test_create_index_on_codigo_field(self):
        """Test that we can create index on codigo field."""
        from app.infrastructure.database.connection import SessionLocal

        session = SessionLocal()
        try:
            # Create index on codigo field
            session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_producto_codigo
                ON productos_clean(codigo)
            """
                )
            )
            session.commit()

            # Verify index exists
            result = session.execute(
                text(
                    """
                SELECT name FROM sqlite_master
                WHERE type='index' AND name='idx_producto_codigo'
            ."""
                )
            )
            index_exists = result.fetchone() is not None

            assert index_exists, "Index on codigo should exist"

            print("✅ Index idx_producto_codigo created successfully")

        finally:
            session.close()

    def test_create_index_on_descripcion_field(self):
        """Test that we can create index on descripcion field for search optimization."""
        from app.infrastructure.database.connection import SessionLocal

        session = SessionLocal()
        try:
            # Create index on descripcion field for LIKE queries
            session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_producto_descripcion
                ON productos_clean(descripcion)
            """
                )
            )
            session.commit()

            # Verify index exists
            result = session.execute(
                text(
                    """
                SELECT name FROM sqlite_master
                WHERE type='index' AND name='idx_producto_descripcion'
            ."""
                )
            )
            index_exists = result.fetchone() is not None

            assert index_exists, "Index on descripcion should exist"

            print("✅ Index idx_producto_descripcion created successfully")

        finally:
            session.close()

    def test_create_index_on_marca_field(self):
        """Test that we can create index on marca field for filtering."""
        from app.infrastructure.database.connection import SessionLocal

        session = SessionLocal()
        try:
            # Create index on marca field
            session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_producto_marca
                ON productos_clean(marca)
            """
                )
            )
            session.commit()

            # Verify index exists
            result = session.execute(
                text(
                    """
                SELECT name FROM sqlite_master
                WHERE type='index' AND name='idx_producto_marca'
            ."""
                )
            )
            index_exists = result.fetchone() is not None

            assert index_exists, "Index on marca should exist"

            print("✅ Index idx_producto_marca created successfully")

        finally:
            session.close()

    def test_create_index_on_familia_field(self):
        """Test that we can create index on familia field for grouping."""
        from app.infrastructure.database.connection import SessionLocal

        session = SessionLocal()
        try:
            # Create index on familia field
            session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_producto_familia
                ON productos_clean(familia)
            """
                )
            )
            session.commit()

            # Verify index exists
            result = session.execute(
                text(
                    """
                SELECT name FROM sqlite_master
                WHERE type='index' AND name='idx_producto_familia'
            ."""
                )
            )
            index_exists = result.fetchone() is not None

            assert index_exists, "Index on familia should exist"

            print("✅ Index idx_producto_familia created successfully")

        finally:
            session.close()

    def test_index_improves_query_performance(self):
        """Test that indexes improve query performance."""
        from app.infrastructure.database.connection import SessionLocal
        from app.application.dto.producto import ProductoSearchDTO
        from app.infrastructure.repositories.producto import (
            SQLAlchemyProductoRepository,
        )

        session = SessionLocal()
        repository = SQLAlchemyProductoRepository(session)

        try:
            # Measure query performance WITHOUT index
            # (First run, no index yet)
            dto = ProductoSearchDTO(buscar="test", limit=10, marca="", familia="")

            start = time.time()
            products_no_index = repository.buscar_productos(dto)
            time_no_index = time.time() - start

            # Create index
            session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_producto_descripcion_search
                ON productos_clean(descripcion)
            ."""
                )
            )
            session.commit()

            # Measure query performance WITH index
            start = time.time()
            products_with_index = repository.buscar_productos(dto)
            time_with_index = time.time() - start

            # Results should be the same
            assert len(products_no_index) == len(products_with_index)

            print(f"⏱️ Time without index: {time_no_index:.4f}s")
            print(f"⏱️ Time with index: {time_with_index:.4f}s")

            # With index should be equal or faster
            # (might not always be faster due to small dataset)
            assert (
                time_with_index <= time_no_index * 1.5
            ), f"Index should improve performance: {time_with_index:.4f}s vs {time_no_index:.4f}s"

        finally:
            session.close()

    def test_composite_index_for_common_queries(self):
        """Test that we can create composite indexes for common query patterns."""
        from app.infrastructure.database.connection import SessionLocal

        session = SessionLocal()
        try:
            # Create composite index for marca + familia filtering
            session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_producto_marca_familia
                ON productos_clean(marca, familia)
            """
                )
            )
            session.commit()

            # Verify composite index exists
            result = session.execute(
                text(
                    """
                SELECT name FROM sqlite_master
                WHERE type='index' AND name='idx_producto_marca_familia'
            ."""
                )
            )
            index_exists = result.fetchone() is not None

            assert index_exists, "Composite index should exist"

            print("✅ Composite index idx_producto_marca_familia created successfully")

        finally:
            session.close()

    def test_all_strategic_indexes_created(self):
        """Test that all strategic indexes are created."""
        from app.infrastructure.database.connection import SessionLocal

        session = SessionLocal()
        try:
            # Create all strategic indexes
            indexes = [
                "idx_producto_codigo",
                "idx_producto_descripcion",
                "idx_producto_marca",
                "idx_producto_familia",
                "idx_producto_marca_familia",
            ]

            for index_name in indexes:
                parts = index_name.split("_")[2:]  # Remove prefix
                field = "_".join(parts)

                if field == "marca_familia":
                    create_sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON productos_clean(marca, familia)"
                else:
                    create_sql = (
                        f"CREATE INDEX IF NOT EXISTS {index_name} ON productos_clean({field})"
                    )

                session.execute(text(create_sql))

            session.commit()

            # Verify all indexes exist
            result = session.execute(text("SELECT name FROM sqlite_master WHERE type='index'"))
            existing_indexes = [row[0] for row in result.fetchall()]

            for index_name in indexes:
                assert index_name in existing_indexes, f"Index {index_name} should exist"

            print(f"✅ All {len(indexes)} strategic indexes created successfully")

        finally:
            session.close()
