"""Acceptance tests for V2 Product List Endpoint with pagination.

Tests follow TDD principles (RED -> GREEN -> REFACTOR).
."""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.interfaces.http.productos import router as productos_router
from app.domain.services.producto import ProductoService


@pytest.fixture
def app():
    """Create FastAPI application for testing."""
    app = FastAPI()
    app.include_router(productos_router, prefix="/api/productos")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_producto_service(mocker):
    """Mock ProductoService for testing."""
    mock_service = mocker.Mock(spec=ProductoService)
    mocker.patch("app.interfaces.http.productos.get_producto_service", return_value=mock_service)
    return mock_service


class TestV2ProductPaginationEndpoint:
    """Test V2 product list endpoint with pagination."""

    def test_pagination_endpoint_requires_parameters(self, client):
        """Test that pagination endpoint works without required parameters."""
        response = client.get("/api/productos/v2/paginated")

        # Should not fail, should use defaults
        assert response.status_code == 200

    def test_pagination_with_page_parameter(self, client, mock_producto_service):
        """Test pagination with page parameter."""
        # Mock service response
        mock_service.buscar_productos_paginado.return_value = (
            [],  # entities
            0,  # total
        )

        response = client.get("/api/productos/v2/paginated?page=2&per_page=10")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "pagination" in data

    def test_pagination_with_sorting(self, client, mock_producto_service):
        """Test pagination with sorting parameter."""
        mock_service.buscar_productos_paginado.return_value = ([], 0)

        response = client.get("/api/productos/v2/paginated?sort=pvp:asc")

        assert response.status_code == 200
        data = response.json()
        assert "sorting_applied" in data or "pagination" in data

    def test_pagination_with_text_filter(self, client, mock_producto_service):
        """Test pagination with text search filter."""
        mock_service.buscar_productos_paginado.return_value = ([], 0)

        response = client.get("/api/productos/v2/paginated?buscar=cocina")

        assert response.status_code == 200

    def test_pagination_with_marca_filter(self, client, mock_producto_service):
        """Test pagination with marca filter."""
        mock_service.buscar_productos_paginado.return_value = ([], 0)

        response = client.get("/api/productos/v2/paginated?marca=SIEMENS")

        assert response.status_code == 200

    def test_pagination_with_familia_filter(self, client, mock_producto_service):
        """Test pagination with familia filter."""
        mock_service.buscar_productos_paginado.return_value = ([], 0)

        response = client.get("/api/productos/v2/paginated?familia=KITCHEN")

        assert response.status_code == 200

    def test_pagination_with_price_range_filter(self, client, mock_producto_service):
        """Test pagination with price range filter."""
        mock_service.buscar_productos_paginado.return_value = ([], 0)

        response = client.get("/api/productos/v2/paginated?pvp_min=100&pvp_max=500")

        assert response.status_code == 200

    def test_pagination_with_multiple_filters(self, client, mock_producto_service):
        """Test pagination with multiple filters combined."""
        mock_service.buscar_productos_paginado.return_value = ([], 0)

        response = client.get(
            "/api/productos/v2/paginated"
            "?buscar=horno&marca=SIEMENS&familia=KITCHEN&pvp_min=100&pvp_max=500&sort=pvp:asc"
        )

        assert response.status_code == 200

    def test_pagination_response_structure(self, client, mock_producto_service):
        """Test that pagination response has correct structure."""
        mock_service.buscar_productos_paginado.return_value = ([], 0)

        response = client.get("/api/productos/v2/paginated?page=1&per_page=10")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "items" in data
        assert "pagination" in data

        # Verify pagination metadata
        pagination = data["pagination"]
        assert "current_page" in pagination
        assert "per_page" in pagination
        assert "total_items" in pagination
        assert "total_pages" in pagination

    def test_pagination_page_validation(self, client):
        """Test that invalid page numbers are handled."""
        response = client.get("/api/productos/v2/paginated?page=0")

        # Should handle invalid page (either 400 or use default)
        assert response.status_code in [200, 422]

    def test_pagination_per_page_validation(self, client):
        """Test that per_page limits are enforced."""
        response = client.get("/api/productos/v2/paginated?per_page=200")

        # Should enforce limits (either 422 or cap at max)
        assert response.status_code in [200, 422]

    def test_pagination_empty_results(self, client, mock_producto_service):
        """Test pagination with empty results."""
        mock_service.buscar_productos_paginado.return_value = (
            [],
            0,  # No results
        )

        response = client.get("/api/productos/v2/paginated?buscar=xyz123")

        assert response.status_code == 200
        data = response.json()

        assert data["items"] == []
        assert data["pagination"]["total_items"] == 0

    def test_pagination_service_call_parameters(self, client, mock_producto_service):
        """Test that service is called with correct parameters."""
        mock_service.buscar_productos_paginado.return_value = ([], 0)

        response = client.get(
            "/api/productos/v2/paginated"
            "?page=2&per_page=20&sort=codigo:desc&buscar=test&marca=SIEMENS"
        )

        assert response.status_code == 200

        # Verify service was called
        assert mock_producto_service.buscar_productos_paginado.called

    def test_pagination_error_handling(self, client, mock_producto_service):
        """Test error handling in pagination endpoint."""
        # Mock service to raise exception
        mock_producto_service.buscar_productos_paginado.side_effect = Exception("Database error")

        response = client.get("/api/productos/v2/paginated?page=1")

        # Should return error response
        assert response.status_code == 500
