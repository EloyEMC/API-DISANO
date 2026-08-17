"""Integration tests for the currently published product HTTP contracts."""

import inspect

import pytest
from fastapi.testclient import TestClient

from app.interfaces.http import productos as productos_module
from app.interfaces.http.productos import (
    buscar_productos_list_v2,
    buscar_productos_paginado,
    get_producto,
    list_products_v1,
    list_products_v3,
)
from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_v2_list_endpoint_returns_current_item_contract(client):
    response = client.get("/api/productos/v2/list?buscar=test&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert {"codigo", "descripcion"}.issubset(data[0])


@pytest.mark.parametrize(
    "query",
    ["limit=0", "limit=101", "limit=5&page=0"],
)
def test_v2_list_endpoint_validates_pagination(client, query):
    assert client.get(f"/api/productos/v2/list?buscar=test&{query}").status_code == 422


def test_v2_paginated_endpoint_returns_pagination_contract(client):
    response = client.get("/api/productos/v2/paginated?buscar=test&per_page=5")
    assert response.status_code == 200
    data = response.json()
    assert {"items", "pagination"}.issubset(data)
    assert isinstance(data["items"], list)


def test_current_v1_and_v3_routes_are_available(client):
    for path in ("/api/productos/v1?per_page=1", "/api/productos/v3?per_page=1"):
        response = client.get(path)
        assert response.status_code == 200
        assert {"items", "pagination"}.issubset(response.json())


def test_current_product_detail_route_uses_v1_contract(client):
    response = client.get("/api/productos/v1/UNKNOWN_PRODUCT")
    assert response.status_code == 404
    assert "no encontrado" in response.text.lower() or "not found" in response.text.lower()


def test_current_product_endpoints_use_service_dependency():
    endpoints = (
        buscar_productos_list_v2,
        buscar_productos_paginado,
        list_products_v1,
        list_products_v3,
        get_producto,
    )
    for endpoint in endpoints:
        parameter = inspect.signature(endpoint).parameters["service"]
        assert parameter.default is not inspect.Parameter.empty


def test_product_http_interface_has_no_direct_database_queries():
    source = inspect.getsource(productos_module)
    assert "sqlite3" not in source.lower()
    assert "cursor.execute" not in source
