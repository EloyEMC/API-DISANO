"""Focused tests for local database backend configuration."""

from pathlib import Path

import pytest
from sqlalchemy.pool import QueuePool, StaticPool

from app.config import Settings
from app.infrastructure.database import connection


def test_settings_keep_sqlite_path_when_database_url_is_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings(database_path="database/local.db")

    assert settings.database_url is None
    assert settings.database_path == "database/local.db"


def test_settings_read_database_url_from_existing_environment_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://catalog:secret@db.example.test/catalog")

    settings = Settings()

    assert settings.database_url == "postgresql://catalog:secret@db.example.test/catalog"


def test_production_engine_selects_postgresql_without_connecting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test."""
    settings = Settings(
        database_url="postgresql://catalog:secret@db.example.test/catalog",
    )
    monkeypatch.setattr(connection, "get_settings", lambda: settings)

    engine = connection.create_production_engine()

    assert engine.url.drivername == "postgresql"
    assert isinstance(engine.pool, QueuePool)
    engine.dispose()


def test_production_engine_preserves_sqlite_static_pool(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Test."""
    database_path = Path(tmp_path) / "catalog.db"
    settings = Settings(database_path=str(database_path))
    monkeypatch.setattr(connection, "get_settings", lambda: settings)
    monkeypatch.setattr(connection, "get_database_path", lambda: database_path)

    engine = connection.create_production_engine()

    assert engine.url.drivername == "sqlite"
    assert isinstance(engine.pool, StaticPool)
    assert engine.url.database == str(database_path)
    engine.dispose()


def test_application_engine_uses_factory_configuration() -> None:
    """Test."""
    assert connection.engine.url.drivername == "sqlite"
    assert isinstance(connection.engine.pool, StaticPool)
    assert connection.SessionFactory.kw["bind"] is connection.engine
