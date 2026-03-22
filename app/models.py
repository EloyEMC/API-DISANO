"""
API DISANO - NEW PYDANTIC MODELS (V2.0)

Migrated to snake_case standard naming convention.

This file replaces app/models.py with standardized field names.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProductoBaseV2(BaseModel):
    """
    Modelo base de producto V2.0

    Nombres de campos estandarizados a snake_case
    siguiendo mejores prácticas de APIs REST.
    """

    # ============================================
    # IDENTIFICATION FIELDS (snake_case)
    # ============================================
    codigo: str = Field(
        ...,
        description="Código del producto",
        min_length=1,
        max_length=50,
        alias="CÓDIGO"
    )
    codigo_web: Optional[str] = Field(
        None,
        description="Código web",
        alias="CODIGO_WEB"
    )
    marca: Optional[str] = Field(
        None,
        description="Marca del producto",
        alias="MARCA"
    )
    referencia: Optional[str] = Field(
        None,
        description="Referencia",
        alias="REFERENCIA"
    )
    ean13: Optional[float] = Field(
        None,
        description="Código EAN 13",
        alias="EAN13"
    )

    # ============================================
    # DESCRIPTION FIELDS (snake_case)
    # ============================================
    descripcion: Optional[str] = Field(
        None,
        description="Descripción del producto",
        alias="DESCRIPCION"
    )
    descripcion_corta: Optional[str] = Field(
        None,
        description="Descripción corta",
        alias="DESCRIPCION_CORTA"
    )

    # ============================================
    # PRICE FIELDS (static + historical)
    # ============================================
    pvp: Optional[float] = Field(
        None,
        description="Precio de venta público actual (static field)",
        ge=0,
        alias="PVP"
    )
    pvp_by_date: Optional[float] = Field(
        None,
        alias="PVP_26_01_26",
        description="Precio histórico con fecha en nombre (PVP_DD_MM_YY). Mantenido para auditoría y referencia histórica."
    )

    # ============================================
    # UNIT FIELDS (snake_case)
    # ============================================
    up_log: Optional[float] = Field(
        None,
        description="Unidades por log",
        alias="UP_LOG"
    )
    u_caja: Optional[int] = Field(
        None,
        description="Unidades por caja",
        ge=0,
        alias="U_CAJA"
    )

    # ============================================
    # CLASSIFICATION FIELDS (snake_case)
    # ============================================
    dto: Optional[str] = Field(
        None,
        description="DTO",
        alias="DTO"
    )
    clase_etim: Optional[str] = Field(
        None,
        description="Clase ETIM",
        alias="CLASE_ETIM"
    )

    # ============================================
    # DIMENSION FIELDS - WEIGHTS (snake_case)
    # ============================================
    peso_bruto_kg: Optional[float] = Field(
        None,
        description="Peso bruto en KG",
        alias="PESO_BRUTO_KG"
    )
    peso_bruto_gr: Optional[float] = Field(
        None,
        description="Peso bruto en gramos",
        alias="PESO_BRUTO_GR"
    )
    peso_neto_kg: Optional[float] = Field(
        None,
        description="Peso neto en KG",
        alias="PESO_NETO_KG"
    )
    peso_neto_gr: Optional[float] = Field(
        None,
        description="Peso neto en gramos",
        alias="PESO_NETO_GR"
    )

    # ============================================
    # DIMENSION FIELDS - LENGTHS (snake_case)
    # ============================================
    longitud_m: Optional[float] = Field(
        None,
        description="Longitud en metros",
        alias="LONGITUD_M"
    )
    longitud_mm: Optional[float] = Field(
        None,
        description="Longitud en milímetros",
        alias="LONGITUD_MM"
    )
    ancho_m: Optional[float] = Field(
        None,
        description="Ancho en metros",
        alias="ANCHO_M"
    )
    ancho_mm: Optional[float] = Field(
        None,
        description="Ancho en milímetros",
        alias="ANCHO_MM"
    )
    alto_m: Optional[float] = Field(
        None,
        description="Alto en metros",
        alias="ALTO_M"
    )
    altura_mm: Optional[float] = Field(
        None,
        description="Altura en milímetros",
        alias="ALTURA_MM"
    )

    # ============================================
    # DIMENSION FIELDS - VOLUMES (snake_case)
    # ============================================
    volumen_dm3: Optional[float] = Field(
        None,
        description="Volumen en dm³",
        alias="VOLUMEN_DM3"
    )
    cm3: Optional[float] = Field(
        None,
        description="Volumen en cm³",
        alias="CM3"
    )

    # ============================================
    # CLASSIFICATION FIELDS (snake_case)
    # ============================================
    Serie_familia_1: Optional[str] = Field(
        None,
        description="Serie familia 1",
        alias="SERIE_FAMILIA_1"
    )
    familia_web: Optional[str] = Field(
        None,
        description="Familia web",
        alias="FAMILIA_WEB"
    )
    familia_catalogo: Optional[str] = Field(
        None,
        description="Familia catálogo",
        alias="FAMILIA_CATALOGO"
    )
    familia_catalogo_ptl: Optional[str] = Field(
        None,
        description="Familia catálogo PTL",
        alias="FAMILIA_CATALOGO_PTL"
    )

    # ============================================
    # IMAGE FIELDS (snake_case)
    # ============================================
    imagen: Optional[str] = Field(
        None,
        description="Nombre de imagen",
        alias="IMAGEN"
    )
    img_url: Optional[str] = Field(
        None,
        description="URL de imagen optimizada",
        alias="IMG_URL"
    )
    url_imagen: Optional[str] = Field(
        None,
        description="URL de imagen directa",
        alias="URL_IMAGEN"
    )

    # ============================================
    # TECHNICAL SHEET FIELDS (snake_case)
    # ============================================
    url_ficha_tec: Optional[str] = Field(
        None,
        description="URL de ficha técnica",
        alias="URL_FICHA_TEC"
    )

    # ============================================
    # STATUS FIELDS (snake_case)
    # ============================================
    descontinuado: Optional[bool] = Field(
        None,
        description="Producto discontinuado",
        alias="DESCONTINUADO"
    )

    # ============================================
    # RAEE FIELDS (standard, keeping as is)
    # ============================================
    raee_a: Optional[float] = Field(
        None,
        description="RAEE Aparatos (€)",
        alias="RAEE_A"
    )
    raee_l: Optional[float] = Field(
        None,
        description="RAEE Lámparas (€)",
        alias="RAEE_L"
    )
    raee_t: Optional[float] = Field(
        None,
        description="RAEE Total (€)",
        alias="RAEE_T"
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "codigo": "33036139",
                "descripcion": "3275 MINISTELVIO LED 67W CLD RAL7021 3000K",
                "pvp": 676.0,
                "PVP_26_01_26": 676.0,
                "marca": "Disano",
                "familia_web": "Luminarias viales"
            }
        }


class ProductoV2(ProductoBaseV2):
    """
    Modelo completo de producto V2.0

    Incluye campos BC3 con nombres estandarizados.
    """

    # ============================================
    # BC3 FIELDS (snake_case, standard format)
    # ============================================
    bc3_descripcion_corta: Optional[str] = Field(
        None,
        description="Descripción BC3 corta"
    )
    bc3_descripcion_larga: Optional[str] = Field(
        None,
        description="Descripción BC3 larga"
    )
    bc3_product_type: Optional[str] = Field(
        None,
        description="Tipo de producto BC3"
    )
    bc3_descripcion_completa: Optional[str] = Field(
        None,
        description="Descripción BC3 completa"
    )
    bc3_processed_at: Optional[datetime] = Field(
        None,
        description="Fecha de procesamiento BC3"
    )

    class Config:
        populate_by_name = True


class ProductoListV2(BaseModel):
    """
    Modelo para lista de productos V2.0

    Nombres estandarizados para paginación.
    """
    total: int = Field(..., description="Total de productos")
    page: int = Field(..., description="Número de página actual")
    page_size: int = Field(..., description="Elementos por página")
    items: list[ProductoV2] = Field(..., description="Lista de productos")


class FamiliaStatsV2(BaseModel):
    """
    Estadísticas de familia V2.0
    """
    familia: str = Field(..., description="Nombre de familia")
    total_productos: int = Field(..., description="Total productos en familia")
    con_bc3: int = Field(..., description="Productos con descripción BC3")
    con_imagen: int = Field(..., description="Productos con imagen")
    descontinuados: int = Field(..., description="Productos discontinuados")


class BC3DescripcionV2(BaseModel):
    """
    Descripción BC3 V2.0
    """
    codigo: str = Field(..., description="Código del producto")
    descripcion_corta: Optional[str] = Field(
        None,
        description="Descripción BC3 corta"
    )
    descripcion_larga: Optional[str] = Field(
        None,
        description="Descripción BC3 larga"
    )
    product_type: Optional[str] = Field(
        None,
        description="Tipo de producto"
    )
    bc3_descripcion_completa: Optional[str] = Field(
        None,
        description="Descripción BC3 completa"
    )


# ============================================
# BACKWARD COMPATIBILITY MODELS (V1)
# ============================================

class ProductoBaseV1(BaseModel):
    """
    Modelo base de producto V1.0 (BACKWARD COMPATIBLE)

    Mantiene nombres antiguos para sistemas que aún los usan.
    """
    CÓDIGO: Optional[str] = Field(None, alias="codigo")
    marca: Optional[str] = None
    referencia: Optional[str] = None
    DESCRIPCION: Optional[str] = Field(None, alias="descripcion")
    pvp: Optional[float] = Field(
        None,
        description="Precio de venta público actual (static field)",
        ge=0
    )
    PVP_26_01_26: Optional[float] = Field(
        None,
        alias="pvp_by_date",
        description="Precio histórico con fecha en nombre (PVP_DD_MM_YY). Mantenido para auditoría y referencia histórica."
    )
    imagen: Optional[str] = None
    img_url: Optional[str] = None
    Url_ficha_tec: Optional[str] = Field(None, alias="url_ficha_tec")
    descontinuado: Optional[bool] = None
    Familia_WEB: Optional[str] = Field(None, alias="familia_web")
    descripcion_corta: Optional[str] = None
    RAEE_A: Optional[float] = None
    RAEE_L: Optional[float] = None

    class Config:
        populate_by_name = True


class ProductoV1(ProductoBaseV1):
    """
    Modelo completo de producto V1.0 (BACKWARD COMPATIBLE)

    Mantiene compatibilidad con sistemas que usan nombres antiguos.
    """
    bc3_descripcion_corta: Optional[str] = None
    bc3_descripcion_larga: Optional[str] = None
    bc3_product_type: Optional[str] = None
    bc3_processed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


# ============================================
# ADMIN MODELS (create/update)
# ============================================

class ProductoCreateV2(BaseModel):
    """
    Modelo para crear producto V2.0

    Usa nombres estandarizados snake_case.
    """
    codigo: str = Field(..., min_length=1, max_length=50)
    marca: Optional[str] = None
    referencia: Optional[str] = None
    descripcion: str = Field(..., min_length=1)
    pvp: Optional[float] = Field(None, ge=0, description="Precio de venta público actual (static field)")
    pvp_by_date: Optional[float] = Field(
        None,
        alias="PVP_26_01_26",
        description="Precio histórico con fecha en nombre (PVP_DD_MM_YY). Mantenido para auditoría y referencia histórica."
    )
    imagen: Optional[str] = None
    img_url: Optional[str] = None
    url_ficha_tec: Optional[str] = None
    descontinuado: bool = False
    familia_web: Optional[str] = None
    descripcion_corta: Optional[str] = None
    raee_a: Optional[float] = None
    raee_l: Optional[float] = None
    bc3_descripcion_corta: Optional[str] = None
    bc3_descripcion_larga: Optional[str] = None
    bc3_product_type: Optional[str] = None
    bc3_descripcion_completa: Optional[str] = None
    url_imagen: Optional[str] = None

    # Dimensions (optional for brevity)
    peso_bruto_kg: Optional[float] = None
    longitud_m: Optional[float] = None
    ancho_m: Optional[float] = None
    alto_m: Optional[float] = None


class ProductoUpdateV2(BaseModel):
    """
    Modelo para actualizar producto V2.0

    Todos los campos opcionales para actualización parcial.
    """
    marca: Optional[str] = None
    referencia: Optional[str] = None
    descripcion: Optional[str] = None
    pvp: Optional[float] = Field(None, ge=0, description="Precio de venta público actual (static field)")
    pvp_by_date: Optional[float] = Field(
        None,
        alias="PVP_26_01_26",
        description="Precio histórico con fecha en nombre (PVP_DD_MM_YY). Mantenido para auditoría y referencia histórica."
    )
    imagen: Optional[str] = None
    img_url: Optional[str] = None
    url_ficha_tec: Optional[str] = None
    descontinuado: Optional[bool] = None
    familia_web: Optional[str] = None
    descripcion_corta: Optional[str] = None
    raee_a: Optional[float] = None
    raee_l: Optional[float] = None
    bc3_descripcion_corta: Optional[str] = None
    bc3_descripcion_larga: Optional[str] = None
    bc3_product_type: Optional[str] = None
    bc3_descripcion_completa: Optional[str] = None
    url_imagen: Optional[str] = None


class ProductoPrecioUpdateV2(BaseModel):
    """
    Modelo para actualizar precio V2.0

    Campo pvp estático (sin fecha en nombre).
    """
    pvp: float = Field(..., ge=0, description="Nuevo PVP del producto")


class AdminResponseV2(BaseModel):
    """
    Respuesta de operaciones admin V2.0
    """
    success: bool = Field(..., description="Indica si la operación fue exitosa")
    message: str = Field(..., description="Mensaje de respuesta")
    data: Optional[dict] = Field(None, description="Datos adicionales")


class AdminResponse(BaseModel):
    """Respuesta de operaciones admin (legacy - for backward compatibility)"""
    success: bool
    message: str
    data: Optional[dict] = None


# ============================================
# EXPORT LIST (for easy reference)
# ============================================

__all__ = [
    # V2.0 Models (New standard)
    "ProductoBaseV2",
    "ProductoV2",
    "ProductoListV2",
    "FamiliaStatsV2",
    "BC3DescripcionV2",

    # V1.0 Models (Backward compatibility)
    "ProductoBaseV1",
    "ProductoV1",

    # Admin Models
    "ProductoCreateV2",
    "ProductoUpdateV2",
    "ProductoPrecioUpdateV2",
    "AdminResponseV2",
    "AdminResponse",
]
