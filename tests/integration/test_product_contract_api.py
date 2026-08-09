"""API-DISANO release module.

This module is part of the reviewed BC3/PostgreSQL release.
"""

from datetime import datetime

from fastapi import FastAPI

from app.application.dto.producto import ProductoBC3Response, ProductoExternalResponse
from app.domain.entities.producto import ProductoEntity
from app.interfaces.http.productos import _contract_item, router


CLIENT_FIELDS = {
    "codigo",
    "descripcion",
    "marca",
    "familia",
    "pvp",
    "codigo_web",
    "referencia",
    "ean_13",
    "imagen",
    "img_url",
    "descontinuado",
    "descripcion_corta",
    "raee_a",
    "raee_l",
    "raee_t",
    "serie_familia_1",
    "familia_web",
    "familia_catalogo",
    "familia_catalogo_ptl",
    "url_ficha_tec",
    "bc3_descripcion_corta",
    "bc3_descripcion_completa",
    "bc3_descripcion_larga",
    "bc3_product_type",
    "bc3_processed_at",
}


def test_external_contract_includes_database_fields_except_discount_and_logistics():
    """Test."""
    response_fields = set(ProductoExternalResponse.model_fields)

    assert CLIENT_FIELDS <= response_fields
    assert {"dto", "up_log", "u_caja", "clase_etim", "cm3"}.isdisjoint(response_fields)
    assert not any(field.startswith("peso_") for field in response_fields)
    assert not any(field.endswith("_mm") or field.endswith("_m") for field in response_fields)


def test_private_bc3_contract_uses_stable_snake_case_names():
    """Test."""
    response = ProductoBC3Response.model_validate(
        {
            "codigo": "P-1",
            "descripcion": "Product",
            "marca": "Brand",
            "dto": "15%",
            "up_log": 2.5,
            "u_caja": 4,
            "clase_etim": "EC000000",
            "cm3": 12.0,
            "bc3_processed_at": datetime(2024, 1, 1),
        }
    )

    data = response.model_dump()
    assert data["dto"] == "15%"
    assert data["up_log"] == 2.5
    assert data["u_caja"] == 4
    assert data["clase_etim"] == "EC000000"
    assert data["cm3"] == 12.0
    assert not {"DTO", "UP_LOG", "U_CAJA", "CLASE_ETIM", "CM3"} & data.keys()


def test_explicit_mapping_supports_entity_detail_for_both_contracts():
    """Test."""
    entity = ProductoEntity(
        codigo="P-1",
        descripcion="Product",
        marca="Brand",
        dto="15%",
        up_log=2.5,
        u_caja=4,
        clase_etim="EC000000",
        cm3=12.0,
        serie_familia_1="S1",
        familia_catalogo="CAT",
        familia_catalogo_ptl="PTL",
        url_ficha_tec="https://example.test/ficha",
    )

    external = _contract_item(entity, private=False)
    private = _contract_item(entity, private=True)
    assert external["serie_familia_1"] == "S1"
    assert "dto" not in external
    assert private["dto"] == "15%"
    assert private["cm3"] == 12.0


def test_versioned_contract_list_and_detail_routes_are_registered():
    """Test."""
    app = FastAPI()
    app.include_router(router, prefix="/api")
    paths = {route.path for route in app.routes}

    assert "/api/productos/v1" in paths
    assert "/api/productos/v1/{codigo}" in paths
    assert "/api/productos/v3" in paths
    assert "/api/productos/bc3/v1" in paths
    assert "/api/productos/bc3/v1/{codigo}" in paths
