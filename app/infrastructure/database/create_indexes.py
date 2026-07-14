"""Database index creation script

Creates strategic indexes on the base productos table for query optimization.
."""

from sqlalchemy import text
from app.infrastructure.database.connection import SessionLocal


def create_strategic_indexes():
    """
    Create strategic indexes on frequently queried fields

    Note: SQLite doesn't allow indexing on views, so indexes are created
    on the base 'productos' table. The 'productos_clean' view benefits from these indexes.
    ."""

    session = SessionLocal()

    try:
        indexes = [
            # Index for primary key lookups (codigo)
            "CREATE INDEX IF NOT EXISTS idx_productos_codigo ON productos([CÓDIGO])",
            # Index for text search (descripcion)
            "CREATE INDEX IF NOT EXISTS idx_productos_descripcion ON productos([DESCRIPCIÓN])",
            # Index for brand filtering (marca)
            "CREATE INDEX IF NOT EXISTS idx_productos_marca ON productos(marca)",
            # Index for family grouping (familia)
            "CREATE INDEX IF NOT EXISTS idx_productos_familia ON productos(familia)",
            # Composite index for common brand + family filter combinations
            "CREATE INDEX IF NOT EXISTS idx_productos_marca_familia ON productos(marca, familia)",
            # Index for BC3 product type filtering
            "CREATE INDEX IF NOT EXISTS idx_productos_bc3_type ON productos(bc3_product_type)",
            # Index for price sorting (pvp)
            "CREATE INDEX IF NOT EXISTS idx_productos_pvp ON productos(pvp)",
        ]

        created_count = 0
        for index_sql in indexes:
            session.execute(text(index_sql))
            created_count += 1

        session.commit()

        print(f"✅ Successfully created {created_count} strategic indexes")

        # Verify indexes were created
        result = session.execute(
            text(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_productos_%'"
            )
        )
        created_indexes = [row[0] for row in result.fetchall()]

        print(f"📊 Indexes created: {', '.join(created_indexes)}")

        return created_indexes

    except Exception as e:
        session.rollback()
        print(f"❌ Error creating indexes: {e}")
        raise
    finally:
        session.close()


def analyze_index_usage():
    """
    Analyze index usage and provide recommendations
    """
    session = SessionLocal()

    try:
        # Get index statistics
        result = session.execute(
            text(
                """
            SELECT name, tbl
            FROM sqlite_master
            WHERE type='index' AND name LIKE 'idx_productos_%'
            ORDER BY name
        ."""
            )
        )

        indexes = result.fetchall()

        print("\n📊 Index Analysis:")
        print(f"   Total indexes: {len(indexes)}")

        for idx in indexes:
            print(f"   - {idx[0]} (table: {idx[1]})")

        # Get table statistics
        result = session.execute(
            text(
                """
            SELECT stat FROM sqlite_stat1 WHERE tbl='productos'
        ."""
            )
        )

        stats = result.fetchall()

        if stats:
            print("\n📈 Table Statistics:")
            for stat in stats:
                print(f"   {stat[0]}")

        return indexes

    finally:
        session.close()


if __name__ == "__main__":
    print("🚀 Creating strategic database indexes...")
    create_strategic_indexes()
    print("\n📊 Analyzing index usage...")
    analyze_index_usage()
    print("\n✅ Index creation complete!")
