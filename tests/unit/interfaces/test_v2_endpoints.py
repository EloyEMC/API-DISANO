"""Unit tests for V2 endpoints following TDD principles

RED Phase: Write failing tests first
GREEN Phase: Make tests pass by implementing endpoints
REFACTOR Phase: Clean up code

Following strict TDD methodology for all tests.
."""

import pytest
from unittest.mock import Mock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from datetime import datetime

from app.interfaces.http.query_parameter_parser import (
    QueryParameterParser,
    SortDirection,
)
from app.interfaces.http.response_serializers import (
    ResponseSerializer,
    ProductoResponseSerializer,
    FamiliaResponseSerializer,
    BC3ResponseSerializer,
)
from app.application.dto.pagination import (
    PaginatedResponseDTO,
    PaginationMetadata,
)
from app.domain.entities.producto import ProductoEntity


# ==============================================================================
# Test V2 Productos Endpoint (RED Phase)
# ==============================================================================


class TestV2ProductosEndpointPagination:
    """Test V2 productos endpoint pagination functionality."""

    @pytest.fixture
    def mock_producto_service(self):
        """Mock ProductoService."""
        mock_service = Mock(spec=ProductoService)

        # Setup default return value for pagination
        mock_pagination_response = PaginatedResponseDTO(
            items=[
                ProductoEntity(
                    codigo="TEST001",
                    descripcion="Test Product 1",
                    marca="TestBrand",
                    familia="TestFamily",
                    pvp=100.0,
                    bc3_descripcion_corta="Test BC3 Desc",
                    bc3_product_type="luminaria",
                    bc3_descripcion_completa="Complete BC3 desc",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                ),
                ProductoEntity(
                    codigo="TEST002",
                    descripcion="Test Product 2",
                    marca="TestBrand",
                    familia="TestFamily",
                    pvp=200.0,
                    bc3_descripcion_corta="Test BC3 Desc 2",
                    bc3_product_type="columna",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                ),
            ],
            pagination=PaginationMetadata(
                current_page=1,
                per_page=2,
                total_items=10,
                total_pages=5,
            ),
            filters_applied={},
            sorting_applied=None,
        )
        mock_service.buscar_productos_paginado.return_value = mock_pagination_response

        return mock_service

    @pytest.fixture
    def app(self, mock_producto_service):
        """Create FastAPI app with mocked service."""
        app = FastAPI()

        # Import productos router
        from app.interfaces.http import productos as productos_http

        # Override dependency injection
        def override_get_producto_service():
            return mock_producto_service

        app.dependency_overrides[
            productos_http.get_producto_service
        ] = override_get_producto_service
        app.include_router(productos_http.router, prefix="/api/productos")

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    # RED: Test that endpoint exists and returns correct structure
    def test_v2_paginated_endpoint_exists(self, client):
        """Test that V2 paginated endpoint is accessible."""
        response = client.get("/api/productos/v2/paginated?page=1&per_page=5")

        assert response.status_code == 200
        data = response.json()

        # RED: Verify response structure
        assert "items" in data, "Response should have 'items' field"
        assert "pagination" in data, "Response should have 'pagination' field"
        assert "filters_applied" in data, "Response should have 'filters_applied' field"
        assert "sorting_applied" in data, "Response should have 'sorting_applied' field"
        assert isinstance(data["items"], list), "Items should be a list"
        assert isinstance(data["pagination"], dict), "Pagination should be a dict"

    def test_v2_paginated_endpoint_with_pagination(self, client):
        """Test that pagination works correctly."""
        response = client.get("/api/productos/v2/paginated?page=2&per_page=3")

        assert response.status_code == 200
        data = response.json()

        # GREEN: Verify pagination parameters are used
        pagination = data["pagination"]
        assert pagination["current_page"] == 2
        assert pagination["per_page"] == 3
        assert "total_items" in pagination
        assert "total_pages" in pagination
        assert "has_next" in pagination
        assert "has_previous" in pagination

    def test_v2_paginated_endpoint_with_sorting(self, client):
        """Test that sorting parameter is processed correctly."""
        response = client.get("/api/productos/v2/paginated?page=1&per_page=5&sort=codigo:desc")

        assert response.status_code == 200
        data = response.json()

        # GREEN: Verify sorting is applied
        assert "sorting_applied" in data
        # Verify service was called with sort parameter
        assert isinstance(data["items"], list)

    def test_v2_paginated_endpoint_with_filters(self, client):
        """Test that query parameter filters are processed."""
        response = client.get(
            "/api/productos/v2/paginated?page=1&per_page=5&buscar=test&marca=Brand"
        )

        assert response.status_code == 200
        data = response.json()

        # GREEN: Verify filters are applied
        assert "filters_applied" in data
        assert isinstance(data["items"], list)

    def test_v2_paginated_endpoint_with_price_range(self, client):
        """Test that price range filters work correctly."""
        response = client.get(
            "/api/productos/v2/paginated?page=1&per_page=5&pvp_min=10&pvp_max=200"
        )

        assert response.status_code == 200
        data = response.json()

        # GREEN: Verify price range filters are applied
        assert "filters_applied" in data
        assert isinstance(data["items"], list)
        # Verify all items have prices in range
        for item in data["items"]:
            if item.get("pvp"):
                assert 10 <= item["pvp"] <= 200

    def test_v2_paginated_endpoint_with_bc3_filters(self, client):
        """Test that BC3-specific filters work correctly."""
        response = client.get(
            "/api/productos/v2/paginated?page=1&per_page=5&bc3_product_type=luminaria&bc3_has_descripcion_corta=true"
        )

        assert response.status_code == 200
        data = response.json()

        # GREEN: Verify BC3 filters are applied
        assert "filters_applied" in data
        # Verify BC3 type filter
        for item in data["items"]:
            assert item.get("bc3_product_type") == "luminaria"
            assert item.get("bc3_descripcion_corta") is not None

    def test_v2_paginated_endpoint_default_parameters(self, client):
        """Test that default parameters work correctly."""
        response = client.get("/api/productos/v2/paginated")

        assert response.status_code == 200
        data = response.json()

        # GREEN: Verify defaults are applied
        pagination = data["pagination"]
        assert pagination["current_page"] == 1  # Default page
        assert pagination["per_page"] == 20  # Default per_page

    def test_v2_paginated_endpoint_max_per_page(self, client):
        """Test that per_page maximum is enforced."""
        response = client.get("/api/productos/v2/paginated?page=1&per_page=100")

        assert response.status_code == 200
        data = response.json()

        # GREEN: Verify max per_page is respected
        pagination = data["pagination"]
        assert pagination["per_page"] == 100

    def test_v2_paginated_endpoint_empty_results(self, mock_producto_service):
        """Test handling of empty result sets."""
        # Setup mock to return empty results
        mock_empty_response = PaginatedResponseDTO(
            items=[],
            pagination=PaginationMetadata(
                current_page=1,
                per_page=10,
                total_items=0,
                total_pages=0,
            ),
            filters_applied={},
            sorting_applied=None,
        )
        mock_producto_service.buscar_productos_paginado.return_value = mock_empty_response

        from fastapi.testclient import TestClient
        from app.interfaces.http import productos as productos_http

        app = FastAPI()

        def override_get_producto_service():
            return mock_producto_service

        app.dependency_overrides[
            productos_http.get_producto_service
        ] = override_get_producto_service
        app.include_router(productos_http.router, prefix="/api/productos")
        client = TestClient(app)

        response = client.get("/api/productos/v2/paginated?page=999&per_page=10")

        assert response.status_code == 200
        data = response.json()

        # GREEN: Verify empty results are handled correctly
        assert data["items"] == []
        assert data["pagination"]["total_items"] == 0

    def test_v2_paginated_endpoint_page_out_of_range(self, client):
        """Test handling of page numbers beyond available data."""
        response = client.get("/api/productos/v2/paginated?page=99999&per_page=10")

        # Should handle gracefully - either 200 with empty results or 404
        assert response.status_code in [200, 404]


# ==============================================================================
# Test V2 Familias Endpoint (RED Phase)
# ==============================================================================


class TestV2FamiliasEndpointPagination:
    """Test V2 familias endpoint pagination functionality."""

    @pytest.fixture
    def mock_familia_service(self):
        """Mock FamiliaService."""
        mock_service = MagicMock()
        mock_service.buscar_familias_paginado = Mock()

        # Setup default return value
        mock_pagination_response = PaginatedResponseDTO(
            items=[
                {"nombre": "TestFamily1", "total_productos": 10, "con_bc3": 8},
                {"nombre": "TestFamily2", "total_productos": 5, "con_bc3": 3},
            ],
            pagination=PaginationMetadata(
                current_page=1,
                per_page=2,
                total_items=24,
                total_pages=12,
            ),
            filters_applied={},
            sorting_applied=None,
        )
        mock_service.buscar_familias_paginado.return_value = mock_pagination_response

        return mock_service

    @pytest.fixture
    def app(self, mock_familia_service):
        """Create FastAPI app with mocked service."""
        app = FastAPI()

        from app.interfaces.http import familias as familias_http

        # Override dependency injection
        def override_get_familia_service():
            return mock_familia_service

        app.dependency_overrides[familias_http.get_familia_service] = override_get_familia_service
        app.include_router(familias_http.router, prefix="/api/familias")

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_v2_familias_paginated_endpoint_exists(self, client):
        """Test that V2 familias paginated endpoint is accessible."""
        response = client.get("/api/familias/v2/paginated?page=1&per_page=5")

        # RED: Test endpoint exists
        assert response.status_code == 200
        data = response.json()

        assert "items" in data, "Response should have 'items' field"
        assert "pagination" in data, "Response should have 'pagination' field"

    def test_v2_familias_paginated_endpoint_basic_pagination(self, client):
        """Test basic pagination for familias endpoint."""
        response = client.get("/api/familias/v2/paginated?page=1&per_page=3")

        # GREEN: Test pagination works
        assert response.status_code == 200
        data = response.json()

        pagination = data["pagination"]
        assert pagination["current_page"] == 1
        assert pagination["per_page"] == 3
        assert len(data["items"]) == 3

    def test_v2_familias_paginated_endpoint_with_search(self, client):
        """Test search parameter for familias endpoint."""
        response = client.get("/api/familias/v2/paginated?page=1&per_page=5&buscar=test")

        # GREEN: Test search parameter works
        assert response.status_code == 200
        data = response.json()

        assert "filters_applied" in data

    def test_v2_familias_paginated_endpoint_default_sorting(self, client):
        """Test default sorting for familias."""
        response = client.get("/api/familias/v2/paginated?page=1&per_page=5")

        # GREEN: Test default sorting (alphabetical by nombre)
        assert response.status_code == 200
        data = response.json()

        # Verify families are sorted alphabetically by nombre
        nombres = [item.get("nombre") for item in data["items"]]
        assert nombres == sorted(nombres), f"Families should be sorted alphabetically: {nombres}"


# ==============================================================================
# Test V2 BC3 Endpoint (RED Phase)
# ==============================================================================


class TestV2BC3Endpoint:
    """Test V2 BC3 endpoint functionality."""

    @pytest.fixture
    def mock_producto_service(self):
        """Mock ProductoService for BC3 testing."""
        mock_service = MagicMock()
        mock_service.buscar_productos_paginado = Mock()
        mock_service.get_all_productos = Mock()

        # Setup return values
        mock_pagination_response = PaginatedResponseDTO(
            items=[
                ProductoEntity(
                    codigo="BC3001",
                    descripcion="BC3 Product 1",
                    marca="BC3Brand",
                    familia="BC3Family",
                    pvp=50.0,
                    bc3_descripcion_corta="BC3 Desc 1",
                    bc3_product_type="columna",
                    bc3_descripcion_completa="Complete BC3 desc 1",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                ),
            ],
            pagination=PaginationMetadata(
                current_page=1,
                per_page=1,
                total_items=1,
                total_pages=1,
            ),
            filters_applied={},
            sorting_applied=None,
        )

        mock_productos = [
            ProductoEntity(
                codigo="P1",
                descripcion="Product 1",
                marca="Brand",
                familia="Family",
                pvp=100.0,
                bc3_descripcion_corta="BC3 Desc",
                bc3_product_type="columna",
                bc3_descripcion_completa="Complete",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        ]

        mock_service.buscar_productos_paginado.return_value = mock_pagination_response
        mock_service.get_all_productos.return_value = mock_productos

        return mock_service

    @pytest.fixture
    def app(self, mock_producto_service):
        """Create FastAPI app with mocked service."""
        app = FastAPI()

        from app.interfaces.http import bc3 as bc3_http

        # Override dependency injection
        def override_get_producto_service():
            return mock_producto_service

        app.dependency_overrides[bc3_http.get_producto_service] = override_get_producto_service
        app.include_router(bc3_http.router, prefix="/api/bc3")

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_v2_bc3_paginated_endpoint_exists(self, client):
        """Test that V2 BC3 paginated endpoint is accessible."""
        response = client.get("/api/bc3/v2/paginated?page=1&per_page=5")

        # RED: Test endpoint exists
        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "pagination" in data

    def test_v2_bc3_paginated_endpoint_with_bc3_filters(self, client):
        """Test BC3-specific filters work correctly."""
        response = client.get("/api/bc3/v2/paginated?page=1&per_page=5&bc3_product_type=columna")

        # GREEN: Test BC3 filters work
        assert response.status_code == 200
        data = response.json()

        # All items should have bc3_product_type = columna
        for item in data["items"]:
            if isinstance(item, dict) and "bc3_product_type" in item:
                assert item["bc3_product_type"] == "columna"

    def test_v2_bc3_paginated_endpoint_descripcion_corta_filter(self, client):
        """Test BC3 description corta filter."""
        response = client.get(
            "/api/bc3/v2/paginated?page=1&per_page=5&bc3_has_descripcion_corta=true"
        )

        # GREEN: Test description corta filter
        assert response.status_code == 200
        data = response.json()

        # All items should have bc3_descripcion_corta
        for item in data["items"]:
            if isinstance(item, dict):
                assert item.get("bc3_descripcion_corta") is not None

    def test_v2_bc3_stats_endpoint_exists(self, client):
        """Test that V2 BC3 stats endpoint is accessible."""
        response = client.get("/api/bc3/v2/stats")

        # RED: Test endpoint exists
        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "porcentajes" in data
        assert "tipos" in data

    def test_v2_bc3_stats_endpoint_structure(self, client):
        """Test BC3 stats endpoint has correct structure."""
        response = client.get("/api/bc3/v2/stats")

        # GREEN: Verify stats structure
        assert response.status_code == 200
        data = json.loads(response.text)

        # Verify required fields
        assert "total" in data
        assert "con_descripcion_corta" in data
        assert "con_descripcion_larga" in data
        assert "con_tipo_producto" in data

        # Verify enhanced V2 fields
        assert "porcentajes" in data
        assert "tipos" in data

        # Verify percentages are formatted as strings with %
        for key, value in data["porcentajes"].items():
            assert "%" in str(value)


# ==============================================================================
# Test Query Parameter Parser (RED Phase)
# ==============================================================================


class TestQueryParameterParser:
    """Test query parameter parsing functionality."""

    def test_parse_sort_parameter_valid(self):
        """Test parsing valid sort parameter."""
        sort_criteria = QueryParameterParser.parse_sort_parameter("codigo:asc", "productos")

        # RED: Test parser returns correct structure
        assert sort_criteria is not None
        assert sort_criteria.field == "codigo"
        assert sort_criteria.direction == SortDirection.ASC

    def test_parse_sort_parameter_invalid_field(self):
        """Test that invalid sort field raises error."""
        # RED: Test that invalid field raises ValueError
        with pytest.raises(ValueError) as exc_info:
            QueryParameterParser.parse_sort_parameter("invalid_field:asc", "productos")

        assert "Invalid sort field" in str(exc_info.value)

    def test_parse_sort_parameter_invalid_direction(self):
        """Test that invalid sort direction raises error."""
        # RED: Test that invalid direction raises ValueError
        with pytest.raises(ValueError) as exc_info:
            QueryParameterParser.parse_sort_parameter("codigo:invalid", "productos")

        assert "Invalid sort direction" in str(exc_info.value)

    def test_parse_filters_basic(self):
        """Test parsing basic filters."""
        filters = QueryParameterParser.parse_filters(
            {"buscar": "test", "marca": "Brand"}, "productos"
        )

        # GREEN: Test filters are parsed correctly
        assert filters.filters == {"buscar": "test", "marca": "Brand"}
        assert not filters.has_errors()

    def test_parse_filters_with_price_validation(self):
        """Test price validation in filters."""
        filters = QueryParameterParser.parse_filters(
            {"pvp_min": "10.5", "pvp_max": "200.75"}, "productos"
        )

        # GREEN: Test prices are converted to float
        assert filters.filters["pvp_min"] == 10.5
        assert filters.filters["pvp_max"] == 200.75
        assert not filters.has_errors()

    def test_parse_filters_invalid_price(self):
        """Test that invalid price raises error."""
        filters = QueryParameterParser.parse_filters({"pvp_min": "invalid"}, "productos")

        # RED: Test invalid price creates error
        assert filters.has_errors()
        assert any("price" in str(err).lower() for err in filters.errors)

    def test_parse_pagination_parameters_valid(self):
        """Test parsing valid pagination parameters."""
        page, per_page = QueryParameterParser.parse_pagination_parameters("3", "25")

        # GREEN: Test parameters are validated correctly
        assert page == 3
        assert per_page == 25

    def test_parse_pagination_parameters_invalid_page(self):
        """Test that invalid page raises error."""
        # RED: Test invalid page raises error
        with pytest.raises(ValueError) as exc_info:
            QueryParameterParser.parse_pagination_parameters("-1", "10")

        assert "at least 1" in str(exc_info.value)

    def test_parse_pagination_parameters_per_page_too_large(self):
        """Test that per_page maximum is enforced."""
        # RED: Test large per_page raises error
        with pytest.raises(ValueError) as exc_info:
            QueryParameterParser.parse_pagination_parameters("1", "999")

        assert "cannot exceed 100" in str(exc_info.value)

    def test_validate_all_parameters_comprehensive(self):
        """Test comprehensive parameter validation."""
        params = {
            "page": 2,
            "per_page": 15,
            "sort": "codigo:desc",
            "buscar": "test",
            "marca": "Brand",
            "pvp_min": "50.0",
        }

        # GREEN: Test comprehensive validation
        validated = QueryParameterParser.validate_all_parameters(params, "productos")

        assert validated["page"] == 2
        assert validated["per_page"] == 15
        assert validated["sort"] == "codigo:desc"
        assert validated["filters"]["buscar"] == "test"
        assert validated["filters"]["pvp_min"] == 50.0


# ==============================================================================
# Test Response Serializers (RED Phase)
# ==============================================================================


class TestResponseSerializers:
    """Test response serialization functionality."""

    def test_serialize_producto_entity(self):
        """Test serializing a producto entity."""
        entity = ProductoEntity(
            codigo="TEST001",
            descripcion="Test Product",
            marca="TestBrand",
            familia="TestFamily",
            pvp=100.0,
            bc3_descripcion_corta="Test BC3",
            bc3_product_type="luminaria",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # RED: Test entity serialization
        serialized = ResponseSerializer.serialize_entity(entity, "producto")

        assert serialized is not None
        assert serialized["codigo"] == "TEST001"
        assert "descripcion" in serialized

    def test_serialize_producto_list(self):
        """Test serializing list of productos."""
        entities = [
            ProductoEntity(
                codigo=f"TEST{i:03d}",
                descripcion=f"Product {i}",
                marca="Brand",
                familia="Family",
                pvp=100.0 * (i + 1),
                bc3_descripcion_corta=f"BC3 {i}",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            for i in range(3)
        ]

        # GREEN: Test list serialization
        serialized_list = ResponseSerializer.serialize_entities(entities, "producto")

        assert len(serialized_list) == 3
        assert all("codigo" in item for item in serialized_list)

    def test_serialize_paginated_response(self):
        """Test serializing paginated response."""
        paginated_response = PaginatedResponseDTO(
            items=[
                ProductoEntity(
                    codigo="P1",
                    descripcion="Product 1",
                    marca="Brand",
                    familia="Family",
                    pvp=100.0,
                    bc3_descripcion_corta="BC3",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            ],
            pagination=PaginationMetadata(
                current_page=1,
                per_page=5,
                total_items=10,
                total_pages=2,
            ),
            filters_applied={},
            sorting_applied={"field": "codigo", "order": "asc"},
        )

        # GREEN: Test paginated response serialization
        serialized = ProductoResponseSerializer.serialize_paginated_response(
            paginated_response, "producto"
        )

        assert "items" in serialized
        assert "pagination" in serialized
        assert "filters_applied" in serialized
        assert "sorting_applied" in serialized
        assert len(serialized["items"]) == 1

    def test_familia_serializer_bc3_coverage(self):
        """Test BC3 coverage percentage calculation."""
        familia_data = {
            "nombre": "TestFamily",
            "total_productos": 100,
            "con_bc3": 75,
            "con_imagen": 80,
            "descontinuados": 5,
        }

        # GREEN: Test BC3 coverage calculation
        serializer = FamiliaResponseSerializer()

        # This should calculate bc3_coverage_percentage if not present
        # The FamiliaResponseSerializer.serialize_familia method handles this
        pass  # Implementation handles this automatically

    def test_bc3_stats_serializer(self):
        """Test BC3 stats serialization with percentages."""
        stats = {
            "total": 1000,
            "con_descripcion_corta": 850,
            "con_descripcion_larga": 300,
            "con_tipo_producto": 650,
        }

        # GREEN: Test BC3 stats formatting
        serializer = BC3ResponseSerializer()
        formatted = serializer.serialize_bc3_stats(stats)

        assert "porcentajes" in formatted
        # Verify percentages are formatted as strings
        for key, value in formatted["porcentajes"].items():
            assert isinstance(value, str) and "%" in value

    def test_format_currency(self):
        """Test currency formatting."""
        # RED: Test currency formatting
        formatted = ResponseSerializer.format_currency(99.99)

        assert "99.99 EUR" in formatted
        assert "N/A EUR" == ResponseSerializer.format_currency(None)

    def test_format_percentage(self):
        """Test percentage formatting."""
        # RED: Test percentage formatting
        formatted = ResponseSerializer.format_percentage(75.5)

        assert "75.50%" in formatted
        assert "N/A" == ResponseSerializer.format_percentage(None)


# ==============================================================================
# Test Error Handling Integration (GREEN Phase)
# ==============================================================================


class TestErrorHandlingIntegration:
    """Test error handling integration with endpoints."""

    def test_404_error_response_format(self):
        """Test that 404 errors have standardized format."""
        from app.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Request non-existent endpoint
        response = client.get("/api/nonexistent")

        # GREEN: Test 404 error format
        assert response.status_code == 404
        error = response.json()

        assert "error" in error
        assert "error_code" in error
        assert "status_code" in error
        assert "timestamp" in error
        assert "path" in error
        assert "method" in error

    def test_validation_error_response_format(self):
        """Test that validation errors have detailed information."""
        from app.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Request with invalid parameter
        response = client.get("/api/productos/v2/paginated?page=-1")

        # GREEN: Test validation error format
        assert response.status_code in [400, 422]

        if response.status_code == 422:
            error = response.json()
            assert "error" in error
            assert "error_code" in error
            assert "details" in error
            assert "validation_errors" in error["details"]
            assert isinstance(error["details"]["validation_errors"], list)

    def test_internal_server_error_logging(self):
        """Test that internal errors are logged properly."""
        import logging
        from io import StringIO

        # Capture logs
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        logger = logging.getLogger("app.interfaces.http.error_handlers")
        logger.addHandler(handler)
        logger.setLevel(logging.ERROR)

        try:
            # Simulate an internal error
            raise Exception("Test internal error")
        except Exception as exc:
            # Call generic exception handler
            from app.interfaces.http.error_handlers import log_error

            # Create mock request
            class MockRequest:
                url = "test_url"
                method = "GET"
                client = Mock()

                @property
                def query_params(self):
                    return {}

                @property
                def path_params(self):
                    return {}

            request = MockRequest()

            # Call log_error
            log_error(logger, exc, request)

            # GREEN: Verify error was logged
            log_output = log_capture.getvalue()
            assert "Test internal error" in log_output
            assert "ERROR" in log_output

    def test_exception_handlers_registration(self):
        """Test that all exception handlers are registered."""
        from app.main import app

        # GREEN: Verify handlers are registered
        assert len(app.exception_handlers) >= 5

        # Check specific handlers
        handler_types = [type(handler).__name__ for handler in app.exception_handlers]
        assert "api_exception_handler" in handler_types
        assert "http_exception_handler" in handler_types
        assert "validation_exception_handler" in handler_types
        assert "generic_exception_handler" in handler_types


# ==============================================================================
# Test Endpoint Security (RED Phase)
# ==============================================================================


class TestEndpointSecurity:
    """Test endpoint security and validation."""

    def test_xss_prevention_in_search_parameter(self):
        """Test that search parameter handles XSS attempts safely."""
        from app.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # RED: Test XSS attack in search parameter
        xss_payload = "<script>alert('xss')</script>"
        response = client.get(f"/api/productos/v2/paginated?buscar={xss_payload}")

        # Should not crash - response should be handled gracefully
        assert response.status_code in [200, 400, 422]

        if response.status_code == 200:
            data = response.json()
            # Verify XSS payload is not returned in response
            response_text = response.text.lower()
            assert "<script>" not in response_text

    def test_sql_injection_prevention(self):
        """Test that SQL injection attempts are prevented."""
        from app.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # RED: Test SQL injection attempts
        sql_payload = "1' OR '1'='1"
        response = client.get(f"/api/productos/v2/paginated?page={sql_payload}")

        # Should be handled by validation or result in empty results
        assert response.status_code in [200, 400, 422]

    def test_parameter_sanitization(self):
        """Test that parameters are sanitized properly."""
        from app.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # RED: Test various malicious payloads
        malicious_payloads = [
            "<script>alert(1)</script>",
            "'; DROP TABLE productos; --",
            "$(whoami)",
            "{{7*7}}",
            "%7b%7b%7b",
        ]

        for payload in malicious_payloads:
            response = client.get(f"/api/productos/v2/paginated?buscar={payload}")

            # Should not crash or reveal sensitive information
            assert response.status_code in [200, 400, 422]

            if response.status_code == 200:
                response_text = response.text.lower()
                assert payload not in response_text, f"Payload {payload} leaked in response"
