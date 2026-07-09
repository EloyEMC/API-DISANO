"""
Configuración de la base de datos SQLite
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator
import os

# Ruta default a la base de datos de producción
DEFAULT_DB_PATH = Path(__file__).parent.parent / "database" / "tarifa_disano.db"


def get_db_path() -> Path:
    """
    Get database path from DATABASE_URL env or default to production.

    Priority:
    1. DATABASE_URL environment variable (testing/production override)
    2. Default production database (tarifa_disano.db)

    Returns:
        Path: Ruta a la base de datos SQLite
    """
    db_url = os.environ.get("DATABASE_URL", None)
    if db_url:
        # Extraer path de sqlite:///
        if db_url.startswith("sqlite:///"):
            return Path(db_url[10:])  # Remover "sqlite:///"
        return Path(db_url)
    return DEFAULT_DB_PATH


# Database path calculada (configurable via DATABASE_URL)
DB_PATH = get_db_path()


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager para conexiones a la base de datos.

    Uso:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM productos")
            results = cursor.fetchall()
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Acceso por nombre de columna
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_db_path_for_display() -> str:
    """Retorna la ruta a la base de datos para logging/display."""
    return str(DB_PATH)
