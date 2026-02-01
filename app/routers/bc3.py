"""
Router de BC3
Endpoints para descripciones BC3
"""

from fastapi import APIRouter, HTTPException
from typing import List
import sqlite3

from app.database import get_db_connection
from app.models import BC3Descripcion

router = APIRouter()


@router.get("/")
async def get_bc3_stats():
    """Obtener estadísticas de descripciones BC3"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN bc3_descripcion_corta IS NOT NULL THEN 1 ELSE 0 END) as con_descripcion_corta,
                SUM(CASE WHEN bc3_descripcion_larga IS NOT NULL THEN 1 ELSE 0 END) as con_descripcion_larga,
                SUM(CASE WHEN bc3_product_type IS NOT NULL THEN 1 ELSE 0 END) as con_tipo_producto
            FROM productos
        """)
        row = cursor.fetchone()
        return dict(row)


@router.get("/tipo/{tipo}")
async def get_productos_por_tipo_bc3(tipo: str):
    """
    Obtener productos por tipo BC3 (columna o articulacion)

    - **tipo**: "columna" o "articulacion"
    """
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM productos WHERE bc3_product_type = ? ORDER BY [CÓDIGO]",
            (tipo,)
        )
        rows = cursor.fetchall()
        return {
            "tipo": tipo,
            "total": len(rows),
            "productos": [dict(row) for row in rows]
        }


@router.get("/columnas")
async def get_columnas():
    """Obtener todos los productos tipo Columna"""
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM productos WHERE bc3_product_type = 'columna' ORDER BY [CÓDIGO]"
        )
        rows = cursor.fetchall()
        return {
            "total": len(rows),
            "productos": [dict(row) for row in rows]
        }


@router.get("/articulaciones")
async def get_articulaciones():
    """Obtener todos los productos tipo Articulación"""
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM productos WHERE bc3_product_type = 'articulacion' ORDER BY [CÓDIGO]"
        )
        rows = cursor.fetchall()
        return {
            "total": len(rows),
            "productos": [dict(row) for row in rows]
        }


@router.get("/{codigo}", response_model=BC3Descripcion)
async def get_bc3_descripcion(codigo: str):
    """Obtener descripción BC3 de un producto"""
    with get_db_connection() as conn:
        cursor = conn.execute(
            """SELECT
                [CÓDIGO] as codigo,
                bc3_descripcion_corta as descripcion_corta,
                bc3_descripcion_larga as descripcion_larga,
                bc3_product_type as product_type
            FROM productos
            WHERE [CÓDIGO] = ?""",
            (codigo,)
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail=f"Producto {codigo} no encontrado")

        return dict(row)
