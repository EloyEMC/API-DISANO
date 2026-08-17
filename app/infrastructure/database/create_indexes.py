"""Create and inspect strategic indexes on the productos table."""

from sqlalchemy import text

from app.infrastructure.database.connection import SessionLocal


_INDEXES = {
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
        "CREATE INDEX IF NOT EXISTS idx_productos_bc3_type " 'ON "productos" ("bc3_product_type")'
    ),
    "idx_productos_pvp": (
        "CREATE INDEX IF NOT EXISTS idx_productos_pvp " 'ON "productos" ("PVP_26_01_26")'
    ),
}


def _index_query(dialect_name: str) -> str:
    if dialect_name == "postgresql":
        return """
            SELECT indexname AS name, tablename AS tbl, indexdef AS sql
            FROM pg_indexes
            WHERE schemaname = current_schema() AND indexname LIKE 'idx_productos_%'
            ORDER BY indexname
        """
    return """
        SELECT name, tbl_name AS tbl, sql
        FROM sqlite_master
        WHERE type = 'index' AND name LIKE 'idx_productos_%'
        ORDER BY name
    """


def create_strategic_indexes():
    """Create indexes for the production query patterns."""
    session = SessionLocal()
    try:
        for statement in _INDEXES.values():
            session.execute(text(statement))
        session.commit()
        rows = session.execute(text(_index_query(session.bind.dialect.name))).mappings().all()
        created_indexes = [row["name"] for row in rows]
        print(f"Successfully created {len(_INDEXES)} strategic indexes")
        print(f"Indexes created: {', '.join(created_indexes)}")
        return created_indexes
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def analyze_index_usage():
    """Report index definitions and backend query statistics."""
    session = SessionLocal()
    try:
        dialect_name = session.bind.dialect.name
        indexes = session.execute(text(_index_query(dialect_name))).fetchall()
        print("\nIndex Analysis:")
        print(f"   Total indexes: {len(indexes)}")
        for index in indexes:
            print(f"   - {index[0]} (table: {index[1]})")

        if dialect_name == "postgresql":
            stats = session.execute(
                text("SELECT n_live_tup FROM pg_stat_user_tables WHERE relname = 'productos'")
            ).fetchall()
        else:
            stats = session.execute(
                text("SELECT stat FROM sqlite_stat1 WHERE tbl = 'productos'")
            ).fetchall()
        if stats:
            print("\nTable Statistics:")
            for stat in stats:
                print(f"   {stat[0]}")
        return indexes
    finally:
        session.close()


if __name__ == "__main__":
    create_strategic_indexes()
    analyze_index_usage()
