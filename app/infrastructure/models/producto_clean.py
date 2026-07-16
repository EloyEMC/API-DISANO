"""SQLAlchemy model using clean view

Uses productos_clean view with standard column names for
SQLAlchemy ORM compatibility.
."""

from sqlalchemy import Column, DateTime, Float, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.types import TypeDecorator, VARCHAR
import json

Base = declarative_base()


class ProductoModelClean(Base):
    """
    SQLAlchemy ORM model for productos_clean view.

    Uses clean column names (no brackets, no spaces) for
    SQLAlchemy compatibility. Based on view in SQLite database.
    ."""

    __tablename__ = "productos_clean"

    # ============================================
    # IDENTIFICATION FIELDS (clean names)
    # ============================================
    codigo = Column(String, primary_key=True, nullable=False)
    descripcion = Column(String, nullable=True)
    marca = Column(String, nullable=True)
    familia = Column(String, nullable=True)
    codigo_web = Column(String, nullable=True)  # ⭐ NUEVO
    referencia = Column(String, nullable=True)  # ⭐ NUEVO
    ean_13 = Column(Float, nullable=True)  # ⭐ SQLite almacena como REAL
    imagen = Column(String, nullable=True)  # ⭐ NUEVO
    img_url = Column(String, nullable=True)  # ⭐ NUEVO

    # ============================================
    # DESCRIPTION FIELDS
    # ============================================
    descripcion_corta = Column(String, nullable=True)

    # ============================================
    # PRICE FIELDS
    # ============================================
    pvp = Column(Float, nullable=True)

    # ============================================
    # BC3 SUITE INTEGRATION FIELDS
    # ============================================
    bc3_descripcion_corta = Column(String, nullable=True)
    bc3_descripcion_completa = Column(String, nullable=True)
    bc3_descripcion_larga = Column(String, nullable=True)  # ⭐ NUEVO
    bc3_product_type = Column(String, nullable=True)
    bc3_processed_at = Column(DateTime, nullable=True)

    def to_entity(self):
        """
        Convert SQLAlchemy model to Domain Entity.

        Returns:
            ProductoEntity: Domain entity with clean naming
        ."""
        from app.domain.entities.producto import ProductoEntity

        return ProductoEntity(
            codigo=self.codigo,
            descripcion=self.descripcion or "",
            marca=self.marca or "",
            familia=self.familia,
            pvp=self.pvp,
            bc3_descripcion_corta=self.bc3_descripcion_corta or self.descripcion_corta,
            bc3_product_type=self.bc3_product_type,
            bc3_descripcion_completa=self.bc3_descripcion_completa,
            # Nuevos campos de productos
            codigo_web=self.codigo_web,
            referencia=self.referencia,
            ean_13=str(self.ean_13) if self.ean_13 is not None else None,
            imagen=self.imagen,
            img_url=self.img_url,
            created_at=self.bc3_processed_at,
            updated_at=self.bc3_processed_at,
        )

    @classmethod
    def from_entity(cls, entity):
        """
        Create SQLAlchemy model from Domain Entity.

        Args:
            entity: ProductoEntity to convert

        Returns:
            ProductoModelClean: SQLAlchemy model with clean column names
        """
        return cls(
            codigo=entity.codigo,
            descripcion=entity.descripcion,
            marca=entity.marca,
            familia=entity.familia,
            pvp=entity.pvp,
            bc3_descripcion_corta=entity.bc3_descripcion_corta,
            bc3_product_type=entity.bc3_product_type,
            bc3_descripcion_completa=entity.bc3_descripcion_completa,
            bc3_processed_at=entity.updated_at or entity.created_at,
            # Nuevos campos de productos
            codigo_web=entity.codigo_web,
            referencia=entity.referencia,
            ean_13=entity.ean_13,
            imagen=entity.imagen,
            img_url=entity.img_url,
        )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<ProductoModelClean(codigo='{self.codigo}', descripcion='{self.descripcion[:20]}...')>"
