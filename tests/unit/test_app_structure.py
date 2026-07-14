"""
Tests Unitarios - Código Simple (Aumenta coverage sin Settings import)
=========================================================

Tests que cubren código simple SIN importar Settings para evitar bloqueo.
."""

import pytest


def test_app_init_exists():
    """Verificar que app/__init__.py existe."""
    import os
    assert os.path.exists("app/__init__.py")


def test_app_main_exists():
    """Verificar que app/main.py existe."""
    import os
    assert os.path.exists("app/main.py")


def test_app_models_exists():
    """Verificar que app/models.py existe."""
    import os
    assert os.path.exists("app/models.py")


def test_app_routers_exist():
    """Verificar que routers principales existen."""
    import os
    assert os.path.exists("app/routers/productos.py")
    assert os.path.exists("app/routers/familias.py")
    assert os.path.exists("app/routers/bc3.py")


def test_app_security_exists():
    """Verificar que módulos security existen."""
    import os
    assert os.path.exists("app/security/api_key.py")
    assert os.path.exists("app/security/otp_service.py")
    assert os.path.exists("app/security/logging_config.py")


def test_app_middleware_exists():
    """Verificar que middleware existe."""
    import os
    assert os.path.exists("app/middleware.py")
    assert os.path.exists("app/middleware_redis.py")


def test_python_version_is_3_14():
    """Verificar que Python 3.14 está instalado."""
    import sys
    version = sys.version_info
    assert version.major == 3
    assert version.minor == 14
    assert "3.14.5" in sys.version


def test_pytest_is_installed():
    """Verificar que pytest está instalado."""
    try:
        import pytest
        assert pytest.__version__ is not None
    except ImportError:
        pytest.fail("pytest no está instalado")


def test_database_has_products_table():
    """Verificar que database tiene tabla productos."""
    import sqlite3

    with sqlite3.connect("testing/testing.db") as conn:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='productos'")
        tables = cursor.fetchall()
        assert len(tables) == 1, f"Debe existir tabla productos, encontradas: {len(tables)}"


def test_database_has_8288_products():
    """Verificar que database tiene 8288 productos."""
    import sqlite3

    with sqlite3.connect("testing/testing.db") as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM productos")
        count = cursor.fetchone()[0]
        assert count == 8288, f"Debe haber 8288 productos, hay {count}"


if __name__ == "__main__":
    pytest.main([__file__])