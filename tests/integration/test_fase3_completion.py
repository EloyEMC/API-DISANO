"""Final verification tests for Fase 3 completion

Comprehensive verification that all Fase 3 objectives are met
"""


class TestFase3Completion:
    """Comprehensive verification tests for Fase 3 completion"""

    def test_hexagonal_architecture_structure(self):
        """Test that hexagonal architecture is properly structured"""
        import os

        # Verify hexagonal structure exists
        hexagonal_paths = [
            "app/interfaces/http",
            "app/application/dto",
            "app/domain/entities",
            "app/domain/repositories",
            "app/domain/services",
            "app/infrastructure/database",
            "app/infrastructure/models",
            "app/infrastructure/repositories",
        ]

        for path in hexagonal_paths:
            assert os.path.exists(path), f"Hexagonal path missing: {path}"

    def test_no_legacy_files_exist(self):
        """Test that all legacy files have been removed"""
        import os

        legacy_files = [
            "app/routers/productos.py",
            "app/routers/familias.py",
            "app/routers/bc3.py",
            "app/database.py",
            "app/models.py",
        ]

        for file in legacy_files:
            assert not os.path.exists(file), f"Legacy file still exists: {file}"

    def test_hexagonal_routers_work(self, client):
        """Test that all hexagonal routers are functional"""
        # Productos
        productos_response = client.get("/api/productos/")
        assert productos_response.status_code == 200

        # Familias
        familias_response = client.get("/api/familias/")
        assert familias_response.status_code == 200

        # BC3
        bc3_response = client.get("/api/bc3/stats")
        assert bc3_response.status_code == 200

    def test_backward_compatibility_maintained(self, client):
        """Test that backward compatibility is maintained"""
        # V1 endpoints should still work
        v1_response = client.get("/api/productos/?limit=10")
        assert v1_response.status_code == 200

        # V2 endpoints should also work
        v2_response = client.get("/api/productos/v2/list?buscar=test&limit=5")
        assert v2_response.status_code == 200

    def test_tdd_methodology_applied(self):
        """Test that TDD methodology was applied (tests exist)"""
        import os

        # Verify test files exist for all major components
        test_files = [
            "tests/unit/domain/test_producto_service.py",
            "tests/unit/domain/test_familia_service.py",
            "tests/integration/test_v2_endpoints.py",
            "tests/integration/test_v1_backward_compatibility.py",
            "tests/integration/test_di_integration.py",
            "tests/integration/test_legacy_removal.py",
            "tests/integration/test_legacy_db_removal.py",
            "tests/integration/test_legacy_models_removal.py",
        ]

        for file in test_files:
            assert os.path.exists(file), f"Test file missing: {file}"

    def test_documentation_updated(self):
        """Test that documentation has been updated"""
        import os

        # Verify hexagonal architecture documentation exists
        docs = ["docs/HEXAGONAL_ARCHITECTURE.md"]

        for doc in docs:
            assert os.path.exists(doc), f"Documentation missing: {doc}"

    def test_dependency_injection_used(self):
        """Test that dependency injection is properly used"""
        import inspect
        import app.interfaces.http.productos as productos_http
        import app.interfaces.http.familias as familias_http
        import app.interfaces.http.bc3 as bc3_http

        # Check that HTTP layers use DI patterns
        for module in [productos_http, familias_http, bc3_http]:
            source = inspect.getsource(module)
            # Should use Depends or DI patterns
            has_di = "Depends" in source or "def get_" in source
            assert has_di, f"{module.__name__} doesn't use dependency injection"

    def test_no_sqlite3_in_hexagonal_code(self):
        """Test that hexagonal code doesn't use sqlite3 directly"""
        import inspect
        import app.domain.services.producto as producto_service
        import app.domain.services.familia as familia_service

        # Domain services should not use sqlite3
        for module in [producto_service, familia_service]:
            source = inspect.getsource(module)
            assert "sqlite3" not in source.lower(), (
                f"{module.__name__} uses sqlite3 directly"
            )

    def test_domain_entities_exist(self):
        """Test that domain entities exist and are properly structured"""
        from app.domain.entities.producto import ProductoEntity
        from app.domain.entities.familia import FamiliaEntity

        # Verify entities have required attributes
        producto = ProductoEntity(
            codigo="TEST", descripcion="Test", marca="Test", pvp=99.99
        )
        assert producto.codigo == "TEST"
        assert producto.descripcion == "Test"

        familia = FamiliaEntity(
            nombre="Test Familia",
            total_productos=100,
            con_bc3=50,
            con_imagen=40,
            descontinuados=10,
        )
        assert familia.nombre == "Test Familia"
        assert familia.get_bc3_coverage_percentage() == 50.0

    def test_all_phases_complete(self):
        """Test that all Fase 3 phases are complete"""
        import os

        # Verify artifacts from all phases exist
        artifacts = [
            # Phase 3.4: DI Setup
            "tests/unit/test_main_di_setup.py",
            "tests/unit/interfaces/test_http_productos.py",
            "tests/integration/test_v2_endpoints.py",
            "tests/integration/test_v1_backward_compatibility.py",
            "tests/integration/test_bc3_compatibility.py",
            # Phase 3.5: Testing Migration
            "tests/integration/test_di_integration.py",
            "tests/performance/performance_test.py",
            # Phase 3.6: Migrate remaining routers
            "tests/unit/domain/test_familia_service.py",
            "tests/integration/test_familias_endpoints.py",
            "tests/integration/test_bc3_endpoints.py",
            # Phase 3.7: Cleanup
            "tests/integration/test_legacy_removal.py",
            "tests/integration/test_legacy_db_removal.py",
            "tests/integration/test_legacy_models_removal.py",
        ]

        for artifact in artifacts:
            assert os.path.exists(artifact), f"Artifact missing: {artifact}"
