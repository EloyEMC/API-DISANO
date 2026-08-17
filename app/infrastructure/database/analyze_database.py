"""Database statistics helpers for SQLite and PostgreSQL."""

from sqlalchemy import text

from app.infrastructure.database.connection import SessionLocal


def analyze_database():
    """Run ANALYZE and return the number of available table statistics."""
    session = SessionLocal()
    try:
        session.execute(text("ANALYZE"))
        session.commit()
        if session.bind.dialect.name == "postgresql":
            count = session.execute(
                text("SELECT COUNT(*) FROM pg_stat_user_tables WHERE reltuples >= 0")
            ).scalar_one()
        else:
            count = session.execute(text("SELECT COUNT(*) FROM sqlite_stat1")).scalar_one()
        return int(count)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _postgres_setting_bytes(value: str) -> int:
    units = {"kB": 1024, "MB": 1024**2, "GB": 1024**3}
    value = value.strip()
    for suffix, multiplier in units.items():
        if value.endswith(suffix):
            return int(float(value[: -len(suffix)].strip()) * multiplier)
    return int(value)


def get_query_planner_info():
    """Return backend-appropriate query planner settings."""
    session = SessionLocal()
    try:
        if session.bind.dialect.name == "postgresql":
            page_size = int(session.execute(text("SHOW block_size")).scalar_one())
            cache_size = _postgres_setting_bytes(
                str(session.execute(text("SHOW shared_buffers")).scalar_one())
            )
            compile_options = []
        else:
            compile_options = [
                row[0] for row in session.execute(text("PRAGMA compile_options")).fetchall()
            ]
            page_size = int(session.execute(text("PRAGMA page_size")).scalar_one())
            cache_size = int(session.execute(text("PRAGMA cache_size")).scalar_one())
        return {
            "compile_options": compile_options,
            "page_size": page_size,
            "cache_size": cache_size,
        }
    finally:
        session.close()


if __name__ == "__main__":
    print(f"Statistics updated: {analyze_database()}")
