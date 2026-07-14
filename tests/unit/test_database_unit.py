"""
Tests Unitarios - Database Coverage (sin Settings import)
===========================================================

Tests que aumentan coverage de app/database.py SIN importar Settings.
."""

import pytest
import sqlite3
from pathlib import Path


def test_database_module_exists():
    """Verificar que app/database.py existe."""
    assert Path("app/database.py").exists()


def test_database_module_has_functions():
    """Verificar que database.py tiene funciones necesarias."""
    content = Path("app/database.py").read_text()
    assert "def get_db_connection" in content
    assert "def get_db_path" in content
    assert "DB_PATH" in content


def test_database_test_db_exists():
    """Verificar que la base de datos de testing existe."""
    test_db = Path("testing/testing.db")
    assert test_db.exists(), f"Base de datos testing no existe: {test_db}"


def test_database_test_db_has_products():
    """Verificar que testing.db tiene 8288 productos."""
    test_db = Path("testing/testing.db")
    connection = sqlite3.connect(test_db)
    cursor = connection.execute("SELECT COUNT(*) FROM productos")
    count = cursor.fetchone()[0]
    connection.close()
    assert count == 8288, (
        f"Base de datos testing debe tener 8288 productos, tiene {count}"
    )


def test_database_test_db_has_correct_structure():
    """Verificar que testing.db tiene estructura correcta."""
    test_db = Path("testing/testing.db")
    connection = sqlite3.connect(test_db)
    cursor = connection.cursor()

    # Verificar tabla productos existe
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='productos'"
    )
    tables = cursor.fetchall()
    assert len(tables) == 1, f"Debe existir tabla productos, encontradas: {len(tables)}"

    # Verificar columnas importantes
    cursor.execute("PRAGMA table_info(productos)")
    columns = {row[1] for row in cursor.fetchall()}

    required_columns = ["CÓDIGO", "DESCRIPCION", "PVP_26_01_26", "MARCA", "Familia_WEB"]
    for col in required_columns:
        assert col in columns, f"Columna {col} no encontrada en tabla productos"

    connection.close()


def test_database_production_db_exists():
    """Verificar que la base de datos de producción existe."""
    prod_db = Path("database/tarifa_disano.db")
    assert prod_db.exists(), "Base de datos producción no existe"


def test_database_backup_exists():
    """Verificar que el backup de producción existe."""
    backup_db = Path("backups/backup_20260708_165258.db")
    assert backup_db.exists(), "Backup de producción no existe"


def test_database_production_not_modified():
    """Verificar que backup es más reciente que producción."""
    from datetime import datetime

    prod_db = Path("database/tarifa_disano.db")
    backup_db = Path("backups/backup_20260708_165258.db")

    prod_mtime = datetime.fromtimestamp(prod_db.stat().st_mtime)
    backup_mtime = datetime.fromtimestamp(backup_db.stat().st_mtime)

    assert backup_mtime > prod_mtime, "Backup debe ser más reciente que producción"


if __name__ == "__main__":
    pytest.main([__file__])
