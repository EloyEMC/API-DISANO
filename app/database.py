"""
Configuración de la base de datos SQLite
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

# Ruta a la base de datos
DB_PATH = Path(__file__).parent.parent / "database" / "tarifa_disano.db"


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


def get_db_path() -> Path:
    """Retorna la ruta a la base de datos"""
    return DB_PATH
