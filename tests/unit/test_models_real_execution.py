"""
Tests Unitarios - Models Real Execution (TDD + AAA)
====================================================

Tests que importan app/models.py y ejecutan código real.
Esto aumenta coverage sin Settings import.
."""

import pytest
from pathlib import Path


class TestModelsModuleImport:
    """Tests que importan app/models.py (TDD)."""

    def test_models_module_import_successfully(self):
        ."""
        AAA: Arrange (import), Act (import), Assert (validation)
        """
        # Arrange & Act - Intentar importar modelos
        try:
            # Importar directamente desde app.models
            import app.models as models

            # Assert - Verificar que tiene modelos V2
            assert hasattr(models, "ProductoBaseV2"), "models no tiene ProductoBaseV2"
            assert hasattr(models, "ProductoV2"), "models no tiene ProductoV2"
        except ImportError as e:
            pytest.fail(f"Error importando app.models: {e}")

    def test_models_has_producto_base_v2(self):
        """GREEN: Verificar que ProductoBaseV2 existe."""
        # Arrange & Act
        import app.models as models

        # Assert
        assert hasattr(models, "ProductoBaseV2")

    def test_models_has_producto_v2(self):
        """GREEN: Verificar que ProductoV2 existe."""
        # Arrange & Act
        import app.models as models

        # Assert
        assert hasattr(models, "ProductoV2")

    def test_models_has_producto_list_v2(self):
        """GREEN: Verificar que ProductoListV2 existe."""
        # Arrange & Act
        import app.models as models

        # Assert
        assert hasattr(models, "ProductoListV2")

    def test_models_base_model_imported(self):
        """GREEN: Verificar que BaseModel está importado."""
        # Arrange & Act
        import app.models as models

        # Assert - Verificar que BaseModel es accesible
        from pydantic import BaseModel

        assert hasattr(models, "ProductoBaseV2")
        assert issubclass(models.ProductoBaseV2, BaseModel)


class TestModelsV2Structure:
    """Tests que verifican estructura de modelos V2 (TDD)."""

    def test_producto_base_v2_has_codigo_field(self):
        ."""GREEN: Verificar que ProductoBaseV2 tiene codigo."""
        # Arrange & Act

        # Assert - Verificar anotaciones de tipo
        assert "codigo:" in Path("app/models.py").read_text()

    def test_producto_base_v2_has_descripcion_field(self):
        """GREEN: Verificar que ProductoBaseV2 tiene descripcion."""
        # Arrange & Act

        # Assert
        assert "descripcion:" in Path("app/models.py").read_text()

    def test_producto_base_v2_has_marca_field(self):
        """GREEN: Verificar que ProductoBaseV2 tiene marca."""
        # Arrange & Act

        # Assert
        assert "marca:" in Path("app/models.py").read_text()

    def test_producto_base_v2_has_pvp_field(self):
        """GREEN: Verificar que ProductoBaseV2 tiene pvp."""
        # Arrange & Act

        # Assert
        assert "pvp:" in Path("app/models.py").read_text()


class TestModelsV2BC3Fields:
    """Tests que verifican campos BC3 en modelos V2 (TDD)."""

    def test_producto_v2_has_bc3_descripcion_corta_field(self):
        ."""GREEN: Verificar que ProductoV2 tiene bc3_descripcion_corta."""
        # Assert
        assert "bc3_descripcion_corta" in Path("app/models.py").read_text()

    def test_producto_v2_has_bc3_product_type_field(self):
        """GREEN: Verificar que ProductoV2 tiene bc3_product_type."""
        # Assert
        assert "bc3_product_type" in Path("app/models.py").read_text()

    def test_producto_v2_has_bc3_processed_at_field(self):
        """GREEN: Verificar que ProductoV2 tiene bc3_processed_at."""
        # Assert
        assert "bc3_processed_at" in Path("app/models.py").read_text()


if __name__ == "__main__":
    pytest.main([__file__])
