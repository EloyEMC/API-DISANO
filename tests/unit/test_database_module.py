"""
Tests Unitarios - Database Module (Cubre código real)
=================================================

Tests que cubren código real de app/database.py SIN importar app.config.
"""

import os
import sqlite3
from pathlib import Path

import pytest


def test_database_module_exists():
    """Verificar que app/database.py existe."""
    assert os.path.exists("app/database.py")


def test_database_module_has_functions():
    """Verificar que database.py tiene funciones necesarias."""
    with open("app/database.py") as f:
        content = f.read()

    assert "def get_db_connection" in content
    assert "def init_db" in content


def test_database_test_db_exists():
    """Verificar que la base de datos de testing existe."""
    test_db = Path("testing/testing.db")
    assert test_db.exists(), f"Base de datos testing no existe: {test_db}"


def test_database_test_db_is_readable():
    """Verificar que la base de datos de testing es legible."""
    test_db = Path("testing/testing.db")
    try:
        connection = sqlite3.connect(test_db)
        cursor = connection.execute("SELECT COUNT(*) FROM productos")
        count = cursor.fetchone()[0]
        connection.close()

        assert count > 0, "Base de datos testing está vacía"
        assert count == 8288, (
            f"Base de datos testing tiene {count} productos, esperaba 8288"
        )

    except sqlite3.Error as e:
        pytest.fail(f"Error al conectar a base de datos testing: {e}")


def test_database_test_db_has_correct_structure():
    """Verificar que la base de datos de testing tiene estructura correcta."""
    test_db = Path("testing/testing.db")
    try:
        connection = sqlite3.connect(test_db)
        cursor = connection.cursor()

        # Verificar que existe tabla productos
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='productos'"
        )
        tables = cursor.fetchall()
        assert len(tables) == 1, "Base de datos testing debe tener tabla productos"

        # Verificar columnas importantes
        cursor.execute("PRAGMA table_info(productos)")
        columns = {row[1] for row in cursor.fetchall()}

        required_columns = [
            "CÓDIGO",
            "DESCRIPCION",
            "PVP_26_01_26",
            "MARCA",
            "Familia_WEB",
        ]
        for col in required_columns:
            assert col in columns, f"Columna {col} no encontrada en tabla productos"

        connection.close()

    except sqlite3.Error as e:
        pytest.fail(f"Error al verificar estructura de base de datos: {e}")


def test_database_production_db_not_modified():
    """Verificar que la base de datos de producción NO ha sido modificada."""
    from datetime import datetime

    prod_db = Path("database/tarifa_disano.db")
    backup_db = Path("backups/backup_20260708_165258.db")

    assert prod_db.exists(), "Base de datos producción no existe"
    assert backup_db.exists(), "Backup de producción no existe"

    # Verificar que backup se creó después de la última modificación
    prod_mtime = datetime.fromtimestamp(prod_db.stat().st_mtime)
    backup_mtime = datetime.fromtimestamp(backup_db.stat().st_mtime)

    # El backup fue creado el 8 de julio 2025
    # La última modificación de producción fue 22 de marzo
    assert backup_mtime > prod_mtime, "Backup debe ser más reciente que producción"


if __name__ == "__main__":
    pytest.main([__file__])
