"""Integration tests to verify legacy models removed

Tests that hexagonal entities are used instead of legacy models
."""

import inspect
import pytest


class TestLegacyModelsRemoval:
    """Tests to verify legacy models have been removed."""

    def test_legacy_app_models_removed(self):
        """Test that legacy app.models module is removed or not used."""
        try:
            import app.models

            # If it exists, check if it's still being used
            import app.main
            import app.interfaces.http.productos as productos_http
            import app.interfaces.http.familias as familias_http
            import app.interfaces.http.bc3 as bc3_http

            # Check main file
            main_source = inspect.getsource(app.main)
            assert "from app.models import" not in main_source, "main.py still imports app.models"

            # Check HTTP layers
            for module in [productos_http, familias_http, bc3_http]:
                source = inspect.getsource(module)
                assert (
                    "from app.models import" not in source
                ), f"{module.__name__} still imports app.models"
        except ImportError:
            # Best case: module doesn't exist
            pass

    def test_hexagonal_entities_used(self):
        """Test that hexagonal domain entities are used."""
        import app.domain.entities.producto as producto_entity
        import app.domain.entities.familia as familia_entity

        # Verify domain entities exist and have expected structure
        assert hasattr(
            producto_entity, "ProductoEntity"
        ), "ProductoEntity not found in domain.entities.producto"
        assert hasattr(
            familia_entity, "FamiliaEntity"
        ), "FamiliaEntity not found in domain.entities.familia"

        # Verify ProductoEntity has BC3 fields
        producto_source = inspect.getsource(producto_entity.ProductoEntity)
        assert (
            "bc3_descripcion_corta" in producto_source
            or "bc3_descripcion_completa" in producto_source
        ), "ProductoEntity doesn't have BC3 fields"

    def test_infrastructure_uses_sqlalchemy_models(self):
        """Test that infrastructure uses SQLAlchemy models instead of legacy models."""
        import app.infrastructure.repositories.producto as producto_repo
        import app.infrastructure.repositories.familia as familia_repo

        for module in [producto_repo, familia_repo]:
            source = inspect.getsource(module)
            # Should use infrastructure models
            assert (
                "from app.infrastructure.models" in source
                or "import app.infrastructure.models" in source
            ), f"{module.__name__} doesn't use infrastructure models"

    def test_no_legacy_model_imports_in_domain(self):
        """Test that domain layer doesn't use legacy models."""
        import app.domain.services.producto as producto_service
        import app.domain.services.familia as familia_service

        for module in [producto_service, familia_service]:
            source = inspect.getsource(module)
            assert (
                "from app.models import" not in source
            ), f"{module.__name__} still imports legacy app.models"

    def test_dto_layer_present(self):
        """Test that DTO layer is present for hexagonal architecture."""
        try:
            from app.application.dto.producto import (
                ProductoResponseDTO,
                ProductoSearchDTO,
                ProductoCreateDTO,
            )

            # DTOs exist
            assert True
        except ImportError:
            pytest.fail("DTO layer not found in app.application.dto.producto")
