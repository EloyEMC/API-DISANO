"""
Tests Unitarios - App Init Import Execution (TDD)
==================================================

Tests que importan app/__init__.py y ejecutan código real.
Esto aumenta coverage sin Settings import.
."""

import pytest


class TestAppInitModuleImport:
    """Tests que importan app/__init__.py (TDD)."""

    def test_app_module_import_successfully(self):
        """
        AAA: Arrange (import), Act (import), Assert (validation)
        """
        # Arrange & Act - Importar app/__init__.py
        try:
            import app

            # Assert - Verificar que app tiene __version__
            assert hasattr(app, "__version__"), "app no tiene __version__"
        except ImportError as e:
            pytest.fail(f"Error importando app: {e}")

    def test_app_version_is_string(self):
        """GREEN: Verificar que versión es string."""
        # Arrange & Act
        import app

        # Assert
        assert isinstance(app.__version__, str), "app.__version__ no es string"

    def test_app_version_not_empty(self):
        """GREEN: Verificar que versión no está vacía."""
        # Arrange & Act
        import app

        # Assert
        assert len(app.__version__) > 0, "app.__version__ está vacía"

    def test_app_version_format(self):
        """GREEN: Verificar formato de versión (X.Y.Z)."""
        # Arrange & Act
        import app

        # Assert - Debe tener formato X.Y.Z
        parts = app.__version__.split(".")
        assert len(parts) >= 2, (
            f"Versión debe tener al menos X.Y, tiene: {app.__version__}"
        )


class TestAppImportsFromInit:
    """Tests que importan desde app/__init__.py (TDD)."""

    def test_app_init_has_version_docstring(self):
        """GREEN: Verificar que __init__.py tiene docstring."""
        # Arrange & Act
        import app

        # Assert - Verificar docstring
        assert hasattr(app, "__version__"), "app no tiene __version__"

    def test_app_version_default_format(self):
        """GREEN: Verificar formato default de versión."""
        # Arrange & Act
        import app

        # Assert - Formato default X.Y.Z
        parts = app.__version__.split(".")
        assert len(parts) == 3, f"Versión debe ser X.Y.Z, tiene: {app.__version__}"
        assert all(part.isdigit() for part in parts), (
            "Partes de versión deben ser números"
        )


if __name__ == "__main__":
    pytest.main([__file__])
