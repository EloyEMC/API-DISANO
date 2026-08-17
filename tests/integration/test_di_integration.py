"""Integration tests for HTTP -> DI -> service -> repository flow."""

from app.infrastructure.database import connection
from app.infrastructure.repositories.producto import SQLAlchemyProductoRepository
from app.domain.services.producto import ProductoService


def test_http_to_service_to_repository_flow(client):
    response = client.get("/api/productos/v2/list?buscar=test&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert {"codigo", "descripcion", "marca", "familia"}.issubset(data[0])


def test_service_input_validation_is_exposed_as_422(client):
    assert client.get("/api/productos/v2/list?buscar=&limit=5").status_code == 200
    assert client.get("/api/productos/v2/list?buscar=test&limit=1000").status_code == 422


def test_repository_uses_configured_infrastructure_session(test_db_path):
    session = connection.SessionLocal()
    try:
        service = ProductoService(SQLAlchemyProductoRepository(session))
        productos = service.get_all_productos(skip=0, limit=5)
        assert isinstance(productos, list)
        if productos:
            assert productos[0].codigo
            assert productos[0].descripcion
    finally:
        session.close()


def test_invalid_pagination_is_rejected(client):
    assert client.get("/api/productos/v2/list?buscar=test&limit=0").status_code == 422
    assert client.get("/api/productos/v2/list?buscar=xyznonexistent&limit=5").status_code == 200


def test_dependency_injection_applies_filters(client):
    response = client.get("/api/productos/v2/list?buscar=test&limit=5&marca=disano")
    assert response.status_code == 200
    for producto in response.json():
        assert producto["marca"].lower() == "disano"


def test_v1_backward_compatibility_contract_remains_available(client):
    response = client.get("/api/productos/?limit=5")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_repeated_requests_reuse_the_configured_database(client):
    for _ in range(5):
        assert client.get("/api/productos/v2/list?buscar=test&limit=5").status_code == 200
