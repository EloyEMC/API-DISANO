"""
Modelos de datos para la API
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProductoBase(BaseModel):
    """Modelo base de producto"""
    codigo: str = Field(..., alias="CÓDIGO")
    marca: Optional[str] = None
    referencia: Optional[str] = None
    descripcion: Optional[str] = Field(None, alias="DESCRIPCION")
    pvp: Optional[float] = Field(None, alias="PVP_26_01_26")
    imagen: Optional[str] = None
    img_url: Optional[str] = None
    url_ficha_tec: Optional[str] = None
    descontinuado: Optional[bool] = None
    familia_web: Optional[str] = Field(None, alias="Familia_WEB")
    descripcion_corta: Optional[str] = None
    raee_a: Optional[float] = Field(None, alias="RAEE_A")
    raee_l: Optional[float] = Field(None, alias="RAEE_L")

    class Config:
        populate_by_name = True


class Producto(ProductoBase):
    """Modelo completo de producto con BC3"""
    bc3_descripcion_corta: Optional[str] = None
    bc3_descripcion_larga: Optional[str] = None
    bc3_product_type: Optional[str] = None
    bc3_processed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


class ProductoList(BaseModel):
    """Modelo para lista de productos con paginación"""
    total: int
    page: int
    page_size: int
    items: list[Producto]


class FamiliaStats(BaseModel):
    """Estadísticas de familia"""
    familia: str
    total_productos: int
    con_bc3: int
    con_imagen: int
    descontinuados: int


class BC3Descripcion(BaseModel):
    """Descripción BC3"""
    codigo: str
    descripcion_corta: Optional[str] = None
    descripcion_larga: Optional[str] = None
    product_type: Optional[str] = None


# Modelos para endpoints de escritura (admin)
class ProductoCreate(BaseModel):
    """Modelo para crear un nuevo producto"""
    codigo: str = Field(..., min_length=1, max_length=50)
    marca: Optional[str] = None
    referencia: Optional[str] = None
    descripcion: str = Field(..., min_length=1)
    pvp: Optional[float] = Field(None, ge=0)
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


class ProductoUpdate(BaseModel):
    """Modelo para actualizar un producto existente"""
    marca: Optional[str] = None
    referencia: Optional[str] = None
    descripcion: Optional[str] = None
    pvp: Optional[float] = Field(None, ge=0)
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


class ProductoPrecioUpdate(BaseModel):
    """Modelo para actualizar solo el precio de un producto"""
    pvp: float = Field(..., ge=0, description="Nuevo PVP del producto")


class AdminResponse(BaseModel):
    """Respuesta de operaciones admin"""
    success: bool
    message: str
    data: Optional[dict] = None
