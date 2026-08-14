"""Focused tests for local database backend configuration."""

from pathlib import Path

import pytest
from sqlalchemy.pool import StaticPool

from app.config import Settings
from app.infrastructure.database import connection


def test_production_engine_requires_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings(environment="production")
    monkeypatch.setattr(connection, "get_settings", lambda: settings)

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        connection.create_production_engine()


def test_production_engine_rejects_non_postgresql_url() -> None:
    with pytest.raises(ValueError, match="PostgreSQL"):
        connection.create_production_engine("mysql://catalog:secret@db/catalog")


def test_settings_read_database_url_from_existing_environment_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://catalog:secret@db.example.test/catalog")

    settings = Settings()

    assert settings.database_url == "postgresql://catalog:secret@db.example.test/catalog"


def test_production_engine_normalizes_bare_postgresql_driver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(
        database_url="postgresql://catalog:secret@db.example.test/catalog",
    )
    monkeypatch.setattr(connection, "get_settings", lambda: settings)

    normalized_url = connection._validate_database_url(settings.database_url, allow_sqlite=False)

    assert normalized_url.startswith("postgresql+psycopg://")


def test_production_engine_preserves_explicit_postgresql_driver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(
        database_url="postgresql+psycopg://catalog:secret@db.example.test/catalog",
    )
    monkeypatch.setattr(connection, "get_settings", lambda: settings)

    normalized_url = connection._validate_database_url(settings.database_url, allow_sqlite=False)

    assert normalized_url == settings.database_url


def test_production_engine_preserves_sqlite_static_pool(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database_path = Path(tmp_path) / "catalog.db"
    settings = Settings(
        environment="testing",
        database_url=f"sqlite:///{database_path}",
        database_path=str(database_path),
    )
    monkeypatch.setattr(connection, "get_settings", lambda: settings)
    monkeypatch.setattr(connection, "get_database_path", lambda: database_path)

    engine = connection.create_production_engine()

    assert engine.url.drivername == "sqlite"
    assert isinstance(engine.pool, StaticPool)
    assert engine.url.database == str(database_path)
    engine.dispose()


def test_application_engine_uses_factory_configuration() -> None:
    assert connection.engine.url.drivername == "sqlite"
    assert isinstance(connection.engine.pool, StaticPool)
    assert connection.SessionFactory.kw["bind"] is connection.engine
