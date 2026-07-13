"""
TDD Tests for TASK-3.4.2: HTTP Interface Layer Created

RED Phase: These tests should FAIL initially if the HTTP layer is not correct.
"""

import pytest
import inspect

try:
    from app.main import app
    from app.interfaces.http.productos import get_producto_service
    from app.domain.repositories.producto import ProductoRepositoryInterface
except ImportError as e:
    pytest.skip(f"Cannot import required modules: {e}", allow_module_level=True)


class TestHTTPInterfaceLayer:
    """Tests for HTTP Interface Layer (TASK-3.4.2)"""

    def test_http_layer_file_exists(self):
        """
        TASK-3.4.2: Test file exists at app/interfaces/http/productos.py
        Acceptance Criteria: File exists at app/interfaces/http/productos.py
        """
        from pathlib import Path

        file_path = Path("app/interfaces/http/productos.py")
        assert file_path.exists(), (
            "HTTP layer file should exist at app/interfaces/http/productos.py"
        )

    def test_http_layer_contains_di_functions(self):
        """
        TASK-3.4.2: Test contains DI functions (get_producto_service, etc.)
        Acceptance Criteria: Contains DI functions (get_producto_service, etc.)
        """
        import app.interfaces.http.productos as productos_module

        # Check DI function exists
        assert hasattr(productos_module, "get_producto_service"), (
            "HTTP layer should have get_producto_service DI function"
        )

        # Check function is callable
        assert callable(get_producto_service), "get_producto_service should be callable"

    def test_http_layer_no_sqlite3_imports(self):
        """
        TASK-3.4.2: Test no sqlite3 imports in HTTP layer
        Acceptance Criteria: No sqlite3 imports in HTTP layer
        """
        import app.interfaces.http.productos as productos_module

        source = inspect.getsource(productos_module)
        assert "sqlite3" not in source.lower(), (
            "HTTP layer should NOT import sqlite3 (should use repository interface)"
        )

    def test_http_layer_only_interface_imports(self):
        """
        TASK-3.4.2: Test HTTP layer follows hexagonal architecture principles
        Acceptance Criteria: HTTP layer uses services, not direct DB access
        """
        import app.interfaces.http.productos as productos_module

        source = inspect.getsource(productos_module)

        # Should use ProductoService (domain layer)
        assert "ProductoService" in source, "HTTP layer should use ProductoService"

        # Should NOT have direct sqlite3 usage
        assert "sqlite3" not in source.lower(), (
            "HTTP layer should NOT use sqlite3 directly"
        )

        # Endpoints should use service dependency injection
        # Check that endpoint functions have service parameter
        lines = source.split("\n")
        endpoints_with_service = 0

        for i, line in enumerate(lines):
            if (
                "@router.get(" in line
                or "@router.post(" in line
                or "@router.put(" in line
            ):
                # Check next ~10 lines for service dependency
                for j in range(i, min(i + 10, len(lines))):
                    if (
                        "service: ProductoService = Depends(get_producto_service)"
                        in lines[j]
                    ):
                        endpoints_with_service += 1
                        break

        # Should have at least V2 (4) + V1 (2) = 6 endpoints with service DI
        assert endpoints_with_service >= 4, (
            f"At least 4 endpoints should use service DI, found {endpoints_with_service}"
        )

    def test_v2_endpoints_exist(self):
        """
        TASK-3.4.2: Test contains V2 endpoints (4 endpoints) with service dependencies
        Acceptance Criteria: Contains V2 endpoints (4 endpoints) with service dependencies
        """
        import app.interfaces.http.productos as productos_module

        source = inspect.getsource(productos_module)

        # Check V2 endpoints exist
        v2_endpoints = [
            '@router.get("/v2/list"',
            '@router.get("/v2/{codigo}"',
            '@router.get("/v2/marca/{marca}"',
            '@router.get("/v2/familia/{familia}"',
        ]

        for endpoint in v2_endpoints:
            assert endpoint in source, f"HTTP layer should have V2 endpoint: {endpoint}"

    def test_v1_endpoints_exist(self):
        """
        TASK-3.4.2: Test contains V1 endpoints (2 endpoints) for backward compatibility
        Acceptance Criteria: Contains V1 endpoints (2 endpoints) for backward compatibility
        """
        import app.interfaces.http.productos as productos_module

        source = inspect.getsource(productos_module)

        # Check V1 endpoints exist
        v1_endpoints = [
            '@router.get("/"',
            '@router.get("/{codigo}"',
        ]

        for endpoint in v1_endpoints:
            assert endpoint in source, f"HTTP layer should have V1 endpoint: {endpoint}"

    def test_v2_endpoints_use_service_dependency(self):
        """
        TASK-3.4.2: Test V2 endpoints use service dependencies
        Acceptance Criteria: V2 endpoints use service dependencies
        """
        import app.interfaces.http.productos as productos_module

        source = inspect.getsource(productos_module)

        # Check that V2 endpoints have service dependency injection
        # Find lines with @router.get("/v2/ and check next lines for Depends
        lines = source.split("\n")
        has_service_dependency = False

        for i, line in enumerate(lines):
            if '@router.get("/v2/' in line:
                # Check next ~10 lines for service dependency
                for j in range(i, min(i + 10, len(lines))):
                    if (
                        "service: ProductoService = Depends(get_producto_service)"
                        in lines[j]
                    ):
                        has_service_dependency = True
                        break

        assert has_service_dependency, (
            "V2 endpoints should use service dependency injection"
        )

    def test_v1_endpoints_use_service_dependency(self):
        """
        TASK-3.4.2: Test V1 endpoints use service dependencies
        Acceptance Criteria: V1 endpoints use service dependencies
        """
        import app.interfaces.http.productos as productos_module

        source = inspect.getsource(productos_module)

        # Check that V1 endpoints have service dependency injection
        lines = source.split("\n")
        has_service_dependency = False

        for i, line in enumerate(lines):
            if '@router.get("/"' in line or '@router.get("/{codigo}"' in line:
                # Check next ~10 lines for service dependency
                for j in range(i, min(i + 10, len(lines))):
                    if (
                        "service: ProductoService = Depends(get_producto_service)"
                        in lines[j]
                    ):
                        has_service_dependency = True
                        break

        assert has_service_dependency, (
            "V1 endpoints should use service dependency injection"
        )

    def test_di_function_creates_service(self):
        """
        TASK-3.4.2: Test DI function creates ProductoService
        Acceptance Criteria: DI function creates ProductoService
        """
        from app.domain.services.producto import ProductoService

        service = get_producto_service()
        assert isinstance(service, ProductoService), (
            "get_producto_service should return ProductoService instance"
        )

    def test_service_has_repository(self):
        """
        TASK-3.4.2: Test service has repository dependency injected
        Acceptance Criteria: Service receives correct repository implementation
        """
        from app.domain.repositories.producto import ProductoRepositoryInterface

        service = get_producto_service()
        assert hasattr(service, "repository"), (
            "Service should have repository attribute"
        )

        assert isinstance(service.repository, ProductoRepositoryInterface), (
            "Service repository should implement ProductoRepositoryInterface"
        )
