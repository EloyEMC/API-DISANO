from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.application.dto.pagination import PaginatedResponseDTO, PaginationMetadata
from app.application.dto.producto import ProductoExternalResponse
from app.domain.entities.producto import ProductoEntity
from app.domain.exceptions.not_found import ProductoNotFoundException
from app.interfaces.http.productos import get_producto_service, router


CLIENT_FIELDS = set(ProductoExternalResponse.model_fields)
PUBLIC_FIELDS = {
    "codigo",
    "descripcion",
    "marca",
    "serie_familia_1",
    "familia_catalogo",
    "familia_catalogo_ptl",
    "url_ficha_tec",
    "bc3_descripcion_larga",
    "raee_a",
    "raee_l",
    "raee_t",
}


def test_external_contract_includes_raee_and_excludes_private_fields():
    response_fields = set(ProductoExternalResponse.model_fields)

    assert {"raee_a", "raee_l", "raee_t"} <= response_fields
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
        raee_a=1.1,
        raee_l=2.2,
        raee_t=3.3,
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


def test_public_list_returns_non_null_fields_and_pagination():
    service = PublicProductService()
    response = _client(service).get("/api/productos/v1?page=2&per_page=1&marca=Brand")

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert PUBLIC_FIELDS <= set(item) <= CLIENT_FIELDS
    assert item["bc3_descripcion_larga"] == "Long description"
    assert item["raee_a"] == 1.1
    assert "dto" not in item
    assert response.json()["pagination"] == {
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


def test_public_detail_returns_non_null_fields_and_404():
    client = _client(PublicProductService())

    response = client.get("/api/productos/v1/P-1")
    missing = client.get("/api/productos/v1/missing")

    assert response.status_code == 200
    assert PUBLIC_FIELDS <= set(response.json()) <= CLIENT_FIELDS
    assert response.json()["bc3_descripcion_larga"] == "Long description"
    assert missing.status_code == 404
    assert "missing" in missing.json()["detail"]


def _route_paths(routes, prefix=""):
    paths = set()
    for route in routes:
        path = getattr(route, "path", None)
        if isinstance(path, str):
            paths.add(f"{prefix}{path}")

        original_router = getattr(route, "original_router", None)
        if original_router is not None:
            include_context = getattr(route, "include_context", None)
            nested_prefix = prefix + getattr(include_context, "prefix", "")
            paths.update(_route_paths(original_router.routes, nested_prefix))
    return paths


def test_versioned_contract_list_and_detail_routes_are_registered():
    app = FastAPI()
    app.include_router(router, prefix="/api")
    paths = _route_paths(app.routes)

    assert {
        "/api/productos/v1",
        "/api/productos/v1/{codigo}",
        "/api/productos/v3",
    } <= paths


def test_openapi_exposes_public_routes_and_response_schema():
    document = _client().get("/openapi.json").json()

    assert {
        "/api/productos/v1",
        "/api/productos/v1/{codigo}",
        "/api/productos/v3",
    } <= set(document["paths"])
    assert (
        set(document["components"]["schemas"]["ProductoExternalResponse"]["properties"])
        == CLIENT_FIELDS
    )
