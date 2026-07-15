"""SQLAlchemy model for Producto

ORM model representing the productos table in SQLite.
Uses quoted names for columns with special characters (spaces, brackets).
."""

from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    DateTime,
)
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class ProductoModel(Base):
    """
    SQLAlchemy ORM model for productos table.

    Uses quoted_name for columns with special characters
    (spaces and brackets from legacy database schema).

    Primary key: '[CÓDIGO]' (column with brackets)
    ."""

    __tablename__ = "productos_clean"

    # ============================================
    # IDENTIFICATION FIELDS (legacy names with special chars)
    # ============================================
    MARCA = Column(String, nullable=True)

    # Primary key with brackets - SQLite requires brackets, not quotes
    CÓDIGO = Column(
        String,
        primary_key=True,
        name="[CÓDIGO]",
        nullable=False,
    )

    CÓDIGO_WEB = Column(
        String,
        name="[CÓDIGO WEB]",
        nullable=True,
    )

    REFERENCIA = Column(String, nullable=True)
    EAN_13 = Column(
        Float,
        name="[EAN 13]",
        nullable=True,
    )

    # ============================================
    # DESCRIPTION FIELDS
    # ============================================
    DESCRIPCION = Column(String, nullable=True)
    descripcion_corta = Column(String, nullable=True)

    # ============================================
    # UNIT FIELDS (legacy names with dots and spaces)
    # ============================================
    UP_LOG = Column(
        Float,
        name="[U.P.LOG]",
        nullable=True,
    )
    U_CAJA = Column(
        Integer,
        name="[U.CAJA]",
        nullable=True,
    )

    # ============================================
    # CLASSIFICATION FIELDS
    # ============================================
    DTO = Column(
        String,
        name="[DTO.]",
        nullable=True,
    )
    CLASE_ETIM = Column(
        String,
        name="[CLASE ETIM]",
        nullable=True,
    )

    # ============================================
    # ENERGY EFFICIENCY FIELDS (RAEE = Energy Label)
    # ============================================
    RAEE_A = Column(Float, nullable=True)
    RAEE_L = Column(Float, nullable=True)
    RAEE_T = Column(Float, nullable=True)

    # ============================================
    # DIMENSION FIELDS - WEIGHTS (legacy names with spaces)
    # ============================================
    peso_bruto_kg = Column(
        Float,
        name="[Peso bruto KG]",
        nullable=True,
    )
    peso_bruto_gr = Column(
        Float,
        name="[Peso bruto GR]",
        nullable=True,
    )
    peso_neto_kg = Column(
        Float,
        name="[Peso neto KG]",
        nullable=True,
    )
    peso_neto_gr = Column(
        Float,
        name="[Peso neto GR]",
        nullable=True,
    )

    # ============================================
    # DIMENSION FIELDS - LENGTH (legacy names with spaces)
    # ============================================
    longitud_m = Column(
        Float,
        name="[Longitud M]",
        nullable=True,
    )
    longitud_mm = Column(
        Float,
        name="[Longitud MM]",
        nullable=True,
    )

    # ============================================
    # DIMENSION FIELDS - WIDTH (legacy names with spaces)
    # ============================================
    ancho_m = Column(
        Float,
        name="[Ancho M]",
        nullable=True,
    )
    ancho_mm = Column(
        Float,
        name="[Ancho MM]",
        nullable=True,
    )

    # ============================================
    # DIMENSION FIELDS - HEIGHT (legacy names with spaces)
    # ============================================
    alto_m = Column(
        Float,
        name="[Alto M]",
        nullable=True,
    )
    altura_mm = Column(
        Float,
        name="[Altura MM]",
        nullable=True,
    )

    # ============================================
    # DIMENSION FIELDS - VOLUME
    # ============================================
    volumen_dm3 = Column(
        Float,
        name="[Volumen DM3]",
        nullable=True,
    )
    CM3 = Column(Float, nullable=True)

    # ============================================
    # CLASSIFICATION FIELDS - Families
    # ============================================
    serie_familia_1 = Column(String, nullable=True)
    Familia_WEB = Column(String, nullable=True)
    Familia_Catalogo = Column(String, nullable=True)
    Familia_Catalogo_PTL = Column(String, nullable=True)

    # ============================================
    # MEDIA FIELDS
    # ============================================
    imagen = Column(String, nullable=True)
    Url_ficha_tec = Column(String, nullable=True)
    img_url = Column(String, nullable=True)

    # ============================================
    # STATUS FIELDS
    # ============================================
    descontinuado = Column(Integer, nullable=True)

    # ============================================
    # PRICE FIELDS (legacy names with date in column name)
    # ============================================
    PVP_26_01_26 = Column(
        Float,
        name="[PVP_26_01_26]",
        nullable=True,
    )

    # ============================================
    # BC3 SUITE INTEGRATION FIELDS
    # ============================================
    bc3_descripcion_corta = Column(String, nullable=True)
    bc3_descripcion_larga = Column(String, nullable=True)
    bc3_descripcion_completa = Column(String, nullable=True)
    bc3_product_type = Column(String, nullable=True)
    bc3_processed_at = Column(DateTime, nullable=True)

    def to_entity(self):
        """
        Convert SQLAlchemy model to Domain Entity.

        Returns:
            ProductoEntity: Domain entity with clean naming
        ."""
        from app.domain.entities.producto import ProductoEntity

        # Map legacy column names to clean entity fields
        return ProductoEntity(
            codigo=self.CÓDIGO,
            descripcion=self.DESCRIPCION or "",
            marca=self.MARCA or "",
            familia=self.Familia_WEB or self.Familia_Catalogo,
            pvp=self.PVP_26_01_26,
            bc3_descripcion_corta=self.bc3_descripcion_corta or self.descripcion_corta,
            bc3_product_type=self.bc3_product_type,
            bc3_descripcion_completa=self.bc3_descripcion_completa
            or self.bc3_descripcion_larga,
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
            ProductoModel: SQLAlchemy model with legacy column names
        """
        return cls(
            CÓDIGO=entity.codigo,
            DESCRIPCION=entity.descripcion,
            MARCA=entity.marca,
            Familia_WEB=entity.familia,
            PVP_26_01_26=entity.pvp,
            bc3_descripcion_corta=entity.bc3_descripcion_corta,
            bc3_product_type=entity.bc3_product_type,
            bc3_descripcion_completa=entity.bc3_descripcion_completa,
            bc3_processed_at=entity.updated_at or entity.created_at,
        )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<ProductoModel(codigo='{self.CÓDIGO}', descripcion='{self.DESCRIPCION[:20]}...')>"
