"""
Router de Productos
Endpoints para consultar productos
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import sqlite3

from app.database import get_db_connection
from app.models import Producto, ProductoList

router = APIRouter()


@router.get("/", response_model=List[Producto])
async def get_productos(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de registros"),
    marca: Optional[str] = Query(None, description="Filtrar por marca"),
    familia: Optional[str] = Query(None, alias="familia_web", description="Filtrar por familia"),
    buscar: Optional[str] = Query(None, description="Buscar en descripción"),
    con_bc3: bool = Query(False, description="Solo productos con BC3"),
    con_imagen: bool = Query(False, description="Solo productos con imagen")
):
    """
    Obtener lista de productos con filtros opcionales.

    - **skip**: Número de registros a saltar (paginación)
    - **limit**: Número máximo de registros (1-500)
    - **marca**: Filtrar por marca (ej: "Disano")
    - **familia**: Filtrar por familia web
    - **buscar**: Buscar texto en descripción
    - **con_bc3**: Solo productos con descripción BC3
    - **con_imagen**: Solo productos con imagen
    """
    with get_db_connection() as conn:
        query = "SELECT * FROM productos WHERE 1=1"
        params = []

        if marca:
            query += " AND MARCA = ?"
            params.append(marca)

        if familia:
            query += " AND [Familia_WEB] = ?"
            params.append(familia)

        if buscar:
            query += " AND DESCRIPCION LIKE ?"
            params.append(f"%{buscar}%")

        if con_bc3:
            query += " AND bc3_descripcion_corta IS NOT NULL"

        if con_imagen:
            query += " AND img_url IS NOT NULL"

        # Total count
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        cursor = conn.execute(count_query, params)
        total = cursor.fetchone()[0]

        # Paginación
        query += " ORDER BY [CÓDIGO] LIMIT ? OFFSET ?"
        params.extend([limit, skip])

        cursor = conn.execute(query, params)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]


@router.get("/{codigo}", response_model=Producto)
async def get_producto(codigo: str):
    """
    Obtener un producto por su código.

    - **codigo**: Código del producto (ej: "33036139")
    """
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM productos WHERE [CÓDIGO] = ?",
            (codigo,)
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail=f"Producto {codigo} no encontrado")

        return dict(row)


@router.get("/marca/{marca}", response_model=List[Producto])
async def get_productos_por_marca(
    marca: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """Obtener todos los productos de una marca"""
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM productos WHERE MARCA = ? ORDER BY [CÓDIGO] LIMIT ? OFFSET ?",
            (marca, limit, skip)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


@router.get("/familia/{familia}", response_model=List[Producto])
async def get_productos_por_familia(
    familia: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """Obtener todos los productos de una familia"""
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM productos WHERE [Familia_WEB] = ? ORDER BY [CÓDIGO] LIMIT ? OFFSET ?",
            (familia, limit, skip)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
