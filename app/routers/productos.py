"""
Router de Productos
Endpoints para consultar y gestionar productos
"""

from fastapi import APIRouter, HTTPException, Query, Request, status
from typing import Optional, List
import sqlite3

from app.database import get_db_connection
from app.models import (
    Producto, ProductoList,
    ProductoCreate, ProductoUpdate, ProductoPrecioUpdate, AdminResponse
)
from app.security import verify_admin_api_key

router = APIRouter()


# =============================================================================
# ENDPOINTS DE LECTURA (PÚBLICOS)
# =============================================================================

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


# =============================================================================
# ENDPOINTS DE ESCRITURA (SOLO ADMIN)
# =============================================================================

@router.post("/", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
async def create_producto(
    producto: ProductoCreate,
    request: Request
):
    """
    Crear un nuevo producto (SOLO ADMIN).

    Requiere header X-Admin-API-Key con la admin API key.
    """
    # Verificar admin API key
    if not verify_admin_api_key(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required. Use X-Admin-API-Key header."
        )

    try:
        with get_db_connection() as conn:
            # Verificar que el código no existe
            cursor = conn.execute(
                "SELECT COUNT(*) FROM productos WHERE [CÓDIGO] = ?",
                (producto.codigo,)
            )
            if cursor.fetchone()[0] > 0:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Producto con código {producto.codigo} ya existe"
                )

            # Insertar producto
            cursor.execute("""
                INSERT INTO productos (
                    [CÓDIGO], MARCA, REFERENCIA, DESCRIPCION,
                    [PVP_26_01_26], imagen, img_url, url_ficha_tec,
                    descontinuado, [Familia_WEB], descripcion_corta,
                    bc3_descripcion_corta, bc3_descripcion_larga, bc3_product_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                producto.codigo,
                producto.marca,
                producto.referencia,
                producto.descripcion,
                producto.pvp,
                producto.imagen,
                producto.img_url,
                producto.url_ficha_tec,
                int(producto.descontinuado),
                producto.familia_web,
                producto.descripcion_corta,
                producto.bc3_descripcion_corta,
                producto.bc3_descripcion_larga,
                producto.bc3_product_type
            ))
            conn.commit()

            return AdminResponse(
                success=True,
                message=f"Producto {producto.codigo} creado exitosamente",
                data={"codigo": producto.codigo}
            )

    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de integridad: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear producto: {str(e)}"
        )


@router.put("/{codigo}", response_model=AdminResponse)
async def update_producto(
    codigo: str,
    producto: ProductoUpdate,
    request: Request
):
    """
    Actualizar un producto existente (SOLO ADMIN).

    Requiere header X-Admin-API-Key con la admin API key.
    """
    # Verificar admin API key
    if not verify_admin_api_key(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required. Use X-Admin-API-Key header."
        )

    try:
        with get_db_connection() as conn:
            # Verificar que el producto existe
            cursor = conn.execute(
                "SELECT COUNT(*) FROM productos WHERE [CÓDIGO] = ?",
                (codigo,)
            )
            if cursor.fetchone()[0] == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Producto {codigo} no encontrado"
                )

            # Construir query dinámico solo con campos proporcionados
            update_fields = []
            params = []

            if producto.marca is not None:
                update_fields.append("MARCA = ?")
                params.append(producto.marca)

            if producto.referencia is not None:
                update_fields.append("REFERENCIA = ?")
                params.append(producto.referencia)

            if producto.descripcion is not None:
                update_fields.append("DESCRIPCION = ?")
                params.append(producto.descripcion)

            if producto.pvp is not None:
                update_fields.append("[PVP_26_01_26] = ?")
                params.append(producto.pvp)

            if producto.imagen is not None:
                update_fields.append("imagen = ?")
                params.append(producto.imagen)

            if producto.img_url is not None:
                update_fields.append("img_url = ?")
                params.append(producto.img_url)

            if producto.url_ficha_tec is not None:
                update_fields.append("url_ficha_tec = ?")
                params.append(producto.url_ficha_tec)

            if producto.descontinuado is not None:
                update_fields.append("descontinuado = ?")
                params.append(int(producto.descontinuado))

            if producto.familia_web is not None:
                update_fields.append("[Familia_WEB] = ?")
                params.append(producto.familia_web)

            if producto.descripcion_corta is not None:
                update_fields.append("descripcion_corta = ?")
                params.append(producto.descripcion_corta)

            if producto.bc3_descripcion_corta is not None:
                update_fields.append("bc3_descripcion_corta = ?")
                params.append(producto.bc3_descripcion_corta)

            if producto.bc3_descripcion_larga is not None:
                update_fields.append("bc3_descripcion_larga = ?")
                params.append(producto.bc3_descripcion_larga)

            if producto.bc3_product_type is not None:
                update_fields.append("bc3_product_type = ?")
                params.append(producto.bc3_product_type)

            if not update_fields:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se proporcionaron campos para actualizar"
                )

            # Añadir código al WHERE
            params.append(codigo)

            query = f"UPDATE productos SET {', '.join(update_fields)} WHERE [CÓDIGO] = ?"
            cursor.execute(query, params)
            conn.commit()

            return AdminResponse(
                success=True,
                message=f"Producto {codigo} actualizado exitosamente",
                data={"codigo": codigo, "campos_actualizados": len(update_fields)}
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar producto: {str(e)}"
        )


@router.patch("/{codigo}/precio", response_model=AdminResponse)
async def update_precio(
    codigo: str,
    precio_update: ProductoPrecioUpdate,
    request: Request
):
    """
    Actualizar solo el precio de un producto (SOLO ADMIN).

    Requiere header X-Admin-API-Key con la admin API key.
    """
    # Verificar admin API key
    if not verify_admin_api_key(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required. Use X-Admin-API-Key header."
        )

    try:
        with get_db_connection() as conn:
            # Verificar que el producto existe
            cursor = conn.execute(
                "SELECT COUNT(*) FROM productos WHERE [CÓDIGO] = ?",
                (codigo,)
            )
            if cursor.fetchone()[0] == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Producto {codigo} no encontrado"
                )

            # Actualizar precio
            cursor.execute(
                "UPDATE productos SET [PVP_26_01_26] = ? WHERE [CÓDIGO] = ?",
                (precio_update.pvp, codigo)
            )
            conn.commit()

            return AdminResponse(
                success=True,
                message=f"Precio de producto {codigo} actualizado a {precio_update.pvp}",
                data={"codigo": codigo, "nuevo_pvp": precio_update.pvp}
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar precio: {str(e)}"
        )


@router.delete("/{codigo}", response_model=AdminResponse)
async def delete_producto(
    codigo: str,
    request: Request
):
    """
    Eliminar un producto (SOLO ADMIN).

    Requiere header X-Admin-API-Key con la admin API key.

    ⚠️ PRECAUCIÓN: Esta operación no se puede deshacer.
    """
    # Verificar admin API key
    if not verify_admin_api_key(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required. Use X-Admin-API-Key header."
        )

    try:
        with get_db_connection() as conn:
            # Verificar que el producto existe
            cursor = conn.execute(
                "SELECT COUNT(*) FROM productos WHERE [CÓDIGO] = ?",
                (codigo,)
            )
            if cursor.fetchone()[0] == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Producto {codigo} no encontrado"
                )

            # Eliminar producto
            cursor.execute(
                "DELETE FROM productos WHERE [CÓDIGO] = ?",
                (codigo,)
            )
            conn.commit()

            return AdminResponse(
                success=True,
                message=f"Producto {codigo} eliminado permanentemente",
                data={"codigo": codigo}
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar producto: {str(e)}"
        )
