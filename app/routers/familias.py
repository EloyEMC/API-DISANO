"""
Router de Familias
Endpoints para consultar familias y estadísticas
"""

from fastapi import APIRouter
from typing import List
import sqlite3

from app.database import get_db_connection
from app.models import FamiliaStats

router = APIRouter()


@router.get("/")
async def get_familias():
    """Obtener lista de todas las familias"""
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT DISTINCT [Familia_WEB] FROM productos WHERE [Familia_WEB] IS NOT NULL ORDER BY [Familia_WEB]"
        )
        rows = cursor.fetchall()
        return {"familias": [row["Familia_WEB"] for row in rows]}


@router.get("/stats")
async def get_familias_stats():
    """Obtener estadísticas de todas las familias"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT
                [Familia_WEB] as familia,
                COUNT(*) as total_productos,
                SUM(CASE WHEN bc3_descripcion_corta IS NOT NULL THEN 1 ELSE 0 END) as con_bc3,
                SUM(CASE WHEN img_url IS NOT NULL THEN 1 ELSE 0 END) as con_imagen,
                SUM(CASE WHEN descontinuado = 1 THEN 1 ELSE 0 END) as descontinuados
            FROM productos
            WHERE [Familia_WEB] IS NOT NULL
            GROUP BY [Familia_WEB]
            ORDER BY total_productos DESC
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


@router.get("/{familia}", response_model=FamiliaStats)
async def get_familia_info(familia: str):
    """Obtener información detallada de una familia"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT
                [Familia_WEB] as familia,
                COUNT(*) as total_productos,
                SUM(CASE WHEN bc3_descripcion_corta IS NOT NULL THEN 1 ELSE 0 END) as con_bc3,
                SUM(CASE WHEN img_url IS NOT NULL THEN 1 ELSE 0 END) as con_imagen,
                SUM(CASE WHEN descontinuado = 1 THEN 1 ELSE 0 END) as descontinuados
            FROM productos
            WHERE [Familia_WEB] = ?
            GROUP BY [Familia_WEB]
        """, (familia,))
        row = cursor.fetchone()

        if not row:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"Familia {familia} no encontrada")

        return dict(row)
