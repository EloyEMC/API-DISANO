from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.application.dto.pagination import PaginatedResponseDTO, PaginationMetadata
from app.application.dto.producto import ProductoExternalResponse
from app.domain.exceptions.not_found import ProductoNotFoundException
from app.domain.entities.producto import ProductoEntity
from app.interfaces.http.productos import get_producto_service, router


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
    response_fields = set(ProductoExternalResponse.model_fields)

    assert CLIENT_FIELDS <= response_fields
    assert {"dto", "up_log", "u_caja", "clase_etim", "cm3"}.isdisjoint(response_fields)
    assert not any(field.startswith("peso_") for field in response_fields)
    assert not any(field.endswith("_mm") or field.endswith("_m") for field in response_fields)


def _public_entity() -> ProductoEntity:
    return ProductoEntity(
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
        bc3_descripcion_larga="Long description",
    )


class PublicProductService:
    def __init__(self) -> None:
        self.pagination_request = None
        self.filters = None

    def buscar_productos_paginado(self, request, filters):
        self.pagination_request = request
        self.filters = filters
        return PaginatedResponseDTO(
            items=[_public_entity()],
            pagination=PaginationMetadata.from_query(
                total_items=3, current_page=request.page, per_page=request.per_page
            ),
            filters_applied=filters,
            sorting_applied=None,
        )

    def obtener_producto(self, codigo: str) -> ProductoEntity:
        if codigo == "missing":
            raise ProductoNotFoundException(codigo)
        return _public_entity()


def _client(service: PublicProductService | None = None) -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api")
    if service is not None:
        app.dependency_overrides[get_producto_service] = lambda: service
    return TestClient(app)


def test_public_list_returns_promised_fields_and_pagination():
    service = PublicProductService()
    response = _client(service).get("/api/productos/v1?page=2&per_page=1&marca=Brand")

    assert response.status_code == 200
    body = response.json()
    assert set(body["items"][0]) == CLIENT_FIELDS
    assert body["items"][0]["bc3_descripcion_larga"] == "Long description"
    assert body["items"][0]["serie_familia_1"] == "S1"
    assert "dto" not in body["items"][0]
    assert body["pagination"] == {
        "total_items": 3,
        "total_pages": 3,
        "current_page": 2,
        "per_page": 1,
        "has_next": True,
        "has_previous": True,
    }
    assert service.pagination_request.page == 2
    assert service.pagination_request.per_page == 1
    assert service.filters == {"marca": "Brand"}


def test_public_detail_returns_promised_fields_and_404():
    client = _client(PublicProductService())

    response = client.get("/api/productos/v1/P-1")
    missing = client.get("/api/productos/v1/missing")

    assert response.status_code == 200
    assert set(response.json()) == CLIENT_FIELDS
    assert response.json()["bc3_descripcion_larga"] == "Long description"
    assert missing.status_code == 404
    assert "missing" in missing.json()["detail"]


def test_versioned_contract_list_and_detail_routes_are_registered():
    app = FastAPI()
    app.include_router(router, prefix="/api")
    paths = {route.path for route in app.routes}

    assert "/api/productos/v1" in paths
    assert "/api/productos/v1/{codigo}" in paths
    assert "/api/productos/v3" in paths


def test_openapi_exposes_public_routes_and_response_schemas():
    document = _client().get("/openapi.json").json()

    assert "/api/productos/v1" in document["paths"]
    assert "/api/productos/v1/{codigo}" in document["paths"]
    assert "/api/productos/v3" in document["paths"]
    schemas = document["components"]["schemas"]
    assert set(schemas["ProductoExternalResponse"]["properties"]) == CLIENT_FIELDS
    assert (
        document["paths"]["/api/productos/v1"]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["schema"]["$ref"]
        == "#/components/schemas/ProductoExternalPage"
    )
    assert (
        document["paths"]["/api/productos/v1/{codigo}"]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["schema"]["$ref"]
        == "#/components/schemas/ProductoExternalResponse"
    )
