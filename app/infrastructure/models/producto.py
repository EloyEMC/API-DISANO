"""SQLAlchemy model for Producto.

ORM model representing the productos table in SQLite.
Uses quoted names for columns with special characters (spaces, brackets).
.
"""

from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    DateTime,
)
from sqlalchemy.orm import declarative_base, synonym


Base = declarative_base()


class ProductoModel(Base):
    """SQLAlchemy ORM model for productos table.

    Uses quoted_name for columns with special characters
    (spaces and brackets from legacy database schema).

    Primary key: '[CÓDIGO]' (column with brackets)
    .
    """

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

    # Clean aliases used by the repository while preserving legacy columns.
    codigo = synonym("CÓDIGO")
    descripcion = synonym("DESCRIPCION")
    marca = synonym("MARCA")
    familia = synonym("Familia_WEB")
    pvp = synonym("PVP_26_01_26")

    # Private BC3 fields retained for the internal contract.

    def to_entity(self):
        """Convert SQLAlchemy model to Domain Entity.

        Returns:
            ProductoEntity: Domain entity with clean naming
        .

        """
        from app.domain.entities.producto import ProductoEntity

        # Map legacy column names to clean entity fields
        return ProductoEntity(
            codigo=self.CÓDIGO,
            descripcion=self.DESCRIPCION or "",
            marca=self.MARCA or "",
            codigo_web=self.CÓDIGO_WEB,
            referencia=self.REFERENCIA,
            descripcion_corta=self.descripcion_corta,
            familia_web=self.Familia_WEB,
            serie_familia_1=self.serie_familia_1,
            familia_catalogo=self.Familia_Catalogo,
            familia_catalogo_ptl=self.Familia_Catalogo_PTL,
            url_ficha_tec=self.Url_ficha_tec,
            ean_13=str(self.EAN_13) if self.EAN_13 is not None else None,
            imagen=self.imagen,
            img_url=self.img_url,
            descontinuado=self.descontinuado,
            raee_a=self.RAEE_A,
            raee_l=self.RAEE_L,
            raee_t=self.RAEE_T,
            familia=self.Familia_WEB or self.Familia_Catalogo,
            pvp=self.PVP_26_01_26,
            bc3_descripcion_corta=self.bc3_descripcion_corta or self.descripcion_corta,
            bc3_product_type=self.bc3_product_type,
            bc3_descripcion_completa=self.bc3_descripcion_completa or self.bc3_descripcion_larga,
            created_at=self.bc3_processed_at,
            updated_at=self.bc3_processed_at,
            dto=self.DTO,
            up_log=self.UP_LOG,
            u_caja=self.U_CAJA,
            clase_etim=self.CLASE_ETIM,
            peso_bruto_kg=self.peso_bruto_kg,
            peso_bruto_gr=self.peso_bruto_gr,
            peso_neto_kg=self.peso_neto_kg,
            peso_neto_gr=self.peso_neto_gr,
            longitud_m=self.longitud_m,
            longitud_mm=self.longitud_mm,
            ancho_m=self.ancho_m,
            ancho_mm=self.ancho_mm,
            alto_m=self.alto_m,
            altura_mm=self.altura_mm,
            volumen_dm3=self.volumen_dm3,
            cm3=self.CM3,
        )

    @classmethod
    def from_entity(cls, entity):
        """Create SQLAlchemy model from Domain Entity.

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
            """Return a string representation for debugging."""
            return (
                f"<ProductoModel(codigo='{self.CÓDIGO}', descripcion='{self.DESCRIPCION[:20]}...')>"
            )


class ProductoRawModel(Base):
    """Read-only projection of the real ``productos`` table."""

    __tablename__ = "productos"

    codigo = Column("CÓDIGO", String, primary_key=True, nullable=False)
    marca = Column("MARCA", String, nullable=True)
    codigo_web = Column("CÓDIGO WEB", String, nullable=True)
    referencia = Column("REFERENCIA", String, nullable=True)
    ean_13 = Column("EAN 13", Float, nullable=True)
    descripcion = Column("DESCRIPCION", String, nullable=True)
    up_log = Column("U.P.LOG", Float, nullable=True)
    u_caja = Column("U.CAJA", Integer, nullable=True)
    dto = Column("DTO.", String, nullable=True)
    clase_etim = Column("CLASE ETIM", String, nullable=True)
    raee_a = Column("RAEE_A", Float, nullable=True)
    raee_l = Column("RAEE_L", Float, nullable=True)
    raee_t = Column("RAEE_T", Float, nullable=True)
    peso_bruto_kg = Column("Peso bruto KG", Float, nullable=True)
    peso_bruto_gr = Column("Peso bruto GR", Float, nullable=True)
    peso_neto_kg = Column("Peso neto KG", Float, nullable=True)
    peso_neto_gr = Column("Peso neto GR", Float, nullable=True)
    longitud_m = Column("Longitud M", Float, nullable=True)
    longitud_mm = Column("Longitud MM", Float, nullable=True)
    ancho_m = Column("Ancho M", Float, nullable=True)
    ancho_mm = Column("Ancho MM", Float, nullable=True)
    alto_m = Column("Alto M", Float, nullable=True)
    altura_mm = Column("Altura MM", Float, nullable=True)
    volumen_dm3 = Column("Volumen DM3", Float, nullable=True)
    cm3 = Column("CM3", Float, nullable=True)
    serie_familia_1 = Column("Serie_familia_1", String, nullable=True)
    familia_web = Column("Familia_WEB", String, nullable=True)
    familia_catalogo = Column("Familia_Catalogo", String, nullable=True)
    familia_catalogo_ptl = Column("Familia_Catalogo_PTL", String, nullable=True)
    imagen = Column("imagen", String, nullable=True)
    url_ficha_tec = Column("Url_ficha_tec", String, nullable=True)
    descontinuado = Column("descontinuado", Integer, nullable=True)
    descripcion_corta = Column("descripcion_corta", String, nullable=True)
    img_url = Column("img_url", String, nullable=True)
    pvp = Column("PVP_26_01_26", Float, nullable=True)
    bc3_descripcion_corta = Column("bc3_descripcion_corta", String, nullable=True)
    bc3_descripcion_larga = Column("bc3_descripcion_larga", String, nullable=True)
    bc3_product_type = Column("bc3_product_type", String, nullable=True)
    bc3_processed_at = Column("bc3_processed_at", DateTime, nullable=True)
    bc3_descripcion_completa = Column("bc3_descripcion_completa", String, nullable=True)

    def to_entity(self):
        """Map the raw row to the domain entity's stable field names."""
        from app.domain.entities.producto import ProductoEntity

        return ProductoEntity(
            codigo=self.codigo,
            descripcion=self.descripcion or "",
            marca=self.marca or "",
            familia=self.familia_web or self.familia_catalogo,
            pvp=self.pvp,
            descripcion_corta=self.descripcion_corta,
            familia_web=self.familia_web,
            serie_familia_1=self.serie_familia_1,
            familia_catalogo=self.familia_catalogo,
            familia_catalogo_ptl=self.familia_catalogo_ptl,
            url_ficha_tec=self.url_ficha_tec,
            codigo_web=self.codigo_web,
            referencia=self.referencia,
            ean_13=str(self.ean_13) if self.ean_13 is not None else None,
            imagen=self.imagen,
            img_url=self.img_url,
            descontinuado=self.descontinuado,
            bc3_descripcion_corta=self.bc3_descripcion_corta,
            bc3_product_type=self.bc3_product_type,
            bc3_descripcion_completa=self.bc3_descripcion_completa or self.bc3_descripcion_larga,
            created_at=self.bc3_processed_at,
            updated_at=self.bc3_processed_at,
            dto=self.dto,
            up_log=self.up_log,
            u_caja=self.u_caja,
            clase_etim=self.clase_etim,
            peso_bruto_kg=self.peso_bruto_kg,
            peso_bruto_gr=self.peso_bruto_gr,
            peso_neto_kg=self.peso_neto_kg,
            peso_neto_gr=self.peso_neto_gr,
            longitud_m=self.longitud_m,
            longitud_mm=self.longitud_mm,
            ancho_m=self.ancho_m,
            ancho_mm=self.ancho_mm,
            alto_m=self.alto_m,
            altura_mm=self.altura_mm,
            volumen_dm3=self.volumen_dm3,
            cm3=self.cm3,
            raee_a=self.raee_a,
            raee_l=self.raee_l,
            raee_t=self.raee_t,
        )
