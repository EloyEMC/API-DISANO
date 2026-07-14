"""Database optimization script using SQLite ANALYZE

Updates query planner statistics for improved performance.
."""

from sqlalchemy import text
from app.infrastructure.database.connection import SessionLocal


def analyze_database():
    """
    Run SQLite ANALYZE command to update query planner statistics

    ANALYZE collects statistics about tables and indexes to help
    the query optimizer make better decisions about query execution plans.
    ."""

    session = SessionLocal()

    try:
        print("🔍 Running ANALYZE on database...")

        # Run ANALYZE on all tables
        session.execute(text("ANALYZE"))
        session.commit()

        # Verify statistics were updated
        result = session.execute(
            text(
                """
            SELECT COUNT(*) as stat_count
            FROM sqlite_stat1
        ."""
            )
        )
        stat_count = result.fetchone()[0]

        print("✅ ANALYZE completed successfully")
        print(f"📊 Statistics updated: {stat_count} entries")

        if stat_count > 0:
            # Show some statistics
            result = session.execute(
                text(
                    """
                SELECT tbl, stat
                FROM sqlite_stat1
                LIMIT 5
            ."""
                )
            )

            print("📈 Sample statistics:")
            for row in result.fetchall():
                print(f"   {row[0]}: {row[1]}")

        return stat_count

    except Exception as e:
        session.rollback()
        print(f"❌ Error running ANALYZE: {e}")
        raise
    finally:
        session.close()


def get_query_planner_info():
    """
    Get query planner information for optimization analysis
    ."""
    session = SessionLocal()

    try:
        # Get compile options
        result = session.execute(text("PRAGMA compile_options"))
        compile_options = [row[0] for row in result.fetchall()]

        print("🔧 SQLite Compile Options:")
        for opt in compile_options:
            print(f"   - {opt}")

        # Get database settings
        result = session.execute(text("PRAGMA page_size"))
        page_size = result.fetchone()[0]

        result = session.execute(text("PRAGMA cache_size"))
        cache_size = result.fetchone()[0]

        print("💾 Database Settings:")
        print(f"   - Page size: {page_size} bytes")
        print(f"   - Cache size: {cache_size} pages")

        return {
            "compile_options": compile_options,
            "page_size": page_size,
            "cache_size": cache_size,
        }

    finally:
        session.close()


if __name__ == "__main__":
    print("🚀 Optimizing database query planner...")

    # Show current settings
    print("\n📊 Current Database Configuration:")
    get_query_planner_info()

    # Run ANALYZE
    print("\n🔍 Updating Query Statistics...")
    stat_count = analyze_database()

    print("\n✅ Database optimization complete!")
    print(f"📈 {stat_count} statistics entries for query optimization")
