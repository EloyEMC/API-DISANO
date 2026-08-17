"""Structural checks for the current hexagonal application layout."""

from pathlib import Path

from sqlalchemy import inspect


APP_ROOT = Path(__file__).parents[2] / "app"


def test_hexagonal_application_modules_exist():
    """The application exposes domain, application, infrastructure and HTTP layers."""
    expected = (
        "domain/entities/producto.py",
        "domain/services/producto.py",
        "application/dto/producto.py",
        "infrastructure/database/connection.py",
        "infrastructure/repositories/producto.py",
        "interfaces/http/productos.py",
        "main.py",
    )
    for relative_path in expected:
        assert (APP_ROOT / relative_path).is_file()


def test_removed_legacy_modules_are_not_required_by_structure():
    """The structure test does not assert deleted legacy app modules."""
    assert not (APP_ROOT / "models.py").exists()
    assert not (APP_ROOT / "database.py").exists()


def test_security_and_middleware_modules_exist():
    """Security and middleware remain part of the active application boundary."""
    for relative_path in (
        "security/api_key.py",
        "security/logging_config.py",
        "middleware.py",
        "middleware_redis.py",
    ):
        assert (APP_ROOT / relative_path).is_file()


def test_configured_database_exposes_product_table(test_db_path):
    """The configured PostgreSQL schema exposes the product table."""
    from app.infrastructure.database import connection

    assert test_db_path.startswith("postgresql")
    assert connection.engine.url.drivername.startswith("postgresql")
    assert inspect(connection.engine).has_table("productos", schema="public")
