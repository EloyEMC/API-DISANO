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
