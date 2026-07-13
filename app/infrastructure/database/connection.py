"""Database connection management

SQLAlchemy engine and session management for infrastructure layer.
"""

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool, QueuePool

from app.config import get_settings


def get_database_path() -> Path:
    """
    Get the database path from settings or fallback to testing DB.

    Returns:
        Path: Path to the SQLite database file
    """
    try:
        settings = get_settings()
        db_path = Path(settings.database_path)
    except Exception:
        # Fallback to testing database
        db_path = Path(__file__).parent.parent.parent / "testing" / "testing.db"

    # Create directory if it doesn't exist
    db_path.parent.mkdir(parents=True, exist_ok=True)

    return db_path


# SQLAlchemy Engine
# Using StaticPool for SQLite to avoid connection issues
engine = create_engine(
    f"sqlite:///{get_database_path()}",
    connect_args={"check_same_thread": False},  # SQLite specific
    poolclass=StaticPool,  # Single connection for SQLite
    echo=False,  # Set to True for SQL query logging
)

# Session factory
# expire_on_commit=False prevents detached instance errors
SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)

# Thread-safe session using scoped_session
SessionLocal = scoped_session(SessionFactory)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.

    Usage:
        with get_db_session() as session:
            producto = session.query(ProductoModel).filter_by(CÓDIGO="TEST001").first()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        if hasattr(SessionLocal, "remove"):
            SessionLocal.remove()  # Clean up thread-local session
        else:
            session.close()  # Alternative cleanup


def get_db_dependency():
    """
    FastAPI dependency for database sessions.

    Usage in FastAPI routers:
        @router.get("/productos/{codigo}")
        def get_producto(codigo: str, db: Session = Depends(get_db_dependency)):
            ...
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_pool_config(environment: str = "development") -> dict[str, int | str]:
    """
    Get database pool configuration for specified environment.

    Args:
        environment: Environment name (development, production, testing)

    Returns:
        Dictionary with pool configuration settings
    """
    configs = {
        "development": {
            "pool_size": 5,
            "max_overflow": 0,
            "pool_timeout": 30,
            "pool_recycle": 3600,
            "pool_pre_ping": True,
            "echo": False,
        },
        "production": {
            "pool_size": 10,
            "max_overflow": 5,
            "pool_timeout": 30,
            "pool_recycle": 1800,  # 30 minutes
            "pool_pre_ping": True,
            "echo": False,
        },
        "testing": {
            "pool_size": 1,
            "max_overflow": 0,
            "pool_timeout": 10,
            "pool_recycle": 3600,
            "pool_pre_ping": True,
            "echo": False,
        },
    }

    return configs.get(environment, configs["development"])


def get_pool_stats() -> dict[str, int | str]:
    """
    Get current pool statistics and usage metrics.

    Returns:
        Dictionary with pool statistics
    """
    pool = engine.pool

    # StaticPool doesn't have all attributes, so we need to handle it
    stats = {
        "size": 1
        if isinstance(pool, StaticPool)
        else (pool.size() if hasattr(pool, "size") else 1),
        "checked_in": 1
        if isinstance(pool, StaticPool)
        else (pool.checkedout() if hasattr(pool, "checkedout") else 1),
        "checked_out": 0 if isinstance(pool, StaticPool) else 0,
        "overflow": 0
        if isinstance(pool, StaticPool)
        else (pool.overflow() if hasattr(pool, "overflow") else 0),
        "pool_type": type(pool).__name__,
    }

    return stats


def check_pool_exhaustion(stats: dict[str, int | str]) -> bool:
    """
    Check if pool is approaching exhaustion.

    Args:
        stats: Pool statistics from get_pool_stats()

    Returns:
        True if pool is exhausted or approaching exhaustion
    """
    # For StaticPool, exhaustion is not applicable
    if stats.get("pool_type") == "StaticPool":
        return False

    # Check if pool is exhausted (all connections checked out)
    try:
        pool_size = int(stats.get("size", 0))
        checked_out = int(stats.get("checked_out", 0))
    except (ValueError, TypeError):
        return False

    if pool_size > 0:
        utilization = checked_out / pool_size
        return utilization > 0.8  # 80% utilization threshold

    return False


def get_pool_logging_config() -> dict[str, bool | int]:
    """
    Get pool logging configuration.

    Returns:
        Dictionary with logging configuration
    """
    return {
        "enabled": True,
        "log_pool_stats": True,
        "log_frequency_seconds": 300,  # Log every 5 minutes
        "log_exhaustion_alerts": True,
        "log_performance_metrics": True,
    }


def get_pool_optimization_recommendations() -> list[str]:
    """
    Get pool optimization recommendations based on current configuration.

    Returns:
        List of optimization recommendations
    """
    recommendations = []
    stats = get_pool_stats()

    # Analyze current configuration
    pool_type = stats.get("pool_type", "Unknown")

    if pool_type == "StaticPool":
        recommendations.append(
            "StaticPool is optimal for SQLite development. "
            "For production with PostgreSQL/MySQL, use QueuePool."
        )
        recommendations.append(
            "Consider increasing pool_size for production: 10-20 connections."
        )
        recommendations.append("Set max_overflow to 5-10 for burst traffic handling.")
        recommendations.append(
            "Configure pool_recycle to 1800 seconds (30 minutes) for production."
        )
    else:
        # Analyze QueuePool configuration
        try:
            pool_size = int(stats.get("size", 0))
            checked_out = int(stats.get("checked_out", 0))
            utilization = checked_out / pool_size if pool_size > 0 else 0
        except (ValueError, TypeError):
            pool_size = 0
            checked_out = 0
            utilization = 0

        if utilization > 0.8:
            recommendations.append(
                "High pool utilization detected (>80%). Consider increasing pool_size."
            )

        if pool_size < 10:
            recommendations.append(
                "Pool size is relatively small. "
                "Consider increasing to 10-20 for production."
            )

    # General recommendations
    recommendations.append("Enable pool_pre_ping for connection health checks.")
    recommendations.append(
        "Set reasonable pool_timeout (30 seconds) to prevent hanging."
    )

    return recommendations


def create_production_engine(database_url: str | None = None) -> Engine:
    """
    Create database engine optimized for production deployment.

    Args:
        database_url: Optional database URL, uses settings if not provided

    Returns:
        SQLAlchemy engine with production-optimized pool configuration
    """
    from app.config import get_settings

    # Get database URL or use settings
    if database_url is None:
        settings = get_settings()
        database_url = getattr(
            settings, "database_url", f"sqlite:///{get_database_path()}"
        )

    # Ensure we have a valid database URL
    if database_url is None:
        database_url = f"sqlite:///{get_database_path()}"

    # Get production pool configuration
    pool_config = get_pool_config("production")

    # Create production engine with QueuePool
    if database_url.startswith("sqlite"):
        # SQLite still uses StaticPool
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=pool_config["echo"],  # type: ignore
        )
    else:
        # PostgreSQL/MySQL use QueuePool
        return create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=pool_config["pool_size"],  # type: ignore
            max_overflow=pool_config["max_overflow"],  # type: ignore
            pool_timeout=pool_config["pool_timeout"],  # type: ignore
            pool_recycle=pool_config["pool_recycle"],  # type: ignore
            pool_pre_ping=pool_config["pool_pre_ping"],  # type: ignore
            echo=pool_config["echo"],
        )


def log_pool_stats() -> None:
    """Log current pool statistics for monitoring."""
    import logging

    logger = logging.getLogger(__name__)
    stats = get_pool_stats()

    logger.info(
        f"Pool Stats - Type: {stats['pool_type']}, "
        f"Size: {stats['size']}, "
        f"Checked In: {stats['checked_in']}, "
        f"Checked Out: {stats['checked_out']}, "
        f"Overflow: {stats['overflow']}"
    )


def monitor_pool_health() -> dict[str, bool | list[str]]:
    """
    Monitor pool health and return status with recommendations.

    Returns:
        Dictionary with health status and recommendations
    """
    stats = get_pool_stats()
    recommendations = get_pool_optimization_recommendations()
    exhausted = check_pool_exhaustion(stats)

    health_status = {
        "healthy": not exhausted,
        "exhausted": exhausted,
        "recommendations": recommendations,
        "stats": stats,
    }

    return health_status
