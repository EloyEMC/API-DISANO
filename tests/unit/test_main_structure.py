"""
Tests Unitarios - Main Module Structure (TDD + AAA)
====================================================

Tests que verifican estructura de app/main.py.
Sin Settings import - solo estructura.
."""

import pytest
from pathlib import Path


class TestMainModule:
    """Tests que verifican estructura de app/main.py (TDD)."""

    def test_main_module_exists(self):
        ."""GREEN: Verificar que main.py existe."""
        # Arrange & Act
        main_path = Path("app/main.py")

        # Assert
        assert main_path.exists()

    def test_main_module_has_root_function(self):
        """GREEN: Verificar que main.py tiene root endpoint."""
        # Arrange
        content = Path("app/main.py").read_text()

        # Assert
        assert "async def root" in content

    def test_main_module_has_health_check(self):
        """GREEN: Verificar que main.py tiene health_check."""
        # Arrange
        content = Path("app/main.py").read_text()

        # Assert
        assert "async def health_check" in content or "health" in content

    def test_main_module_imports_fastapi(self):
        """GREEN: Verificar que main.py importa FastAPI."""
        # Arrange
        content = Path("app/main.py").read_text()

        # Assert
        assert "from fastapi import" in content

    def test_main_module_imports_routers(self):
        """GREEN: Verificar que main.py importa routers."""
        # Arrange
        content = Path("app/main.py").read_text()

        # Assert
        assert "from app.routers import" in content

    def test_main_module_imports_middleware(self):
        """GREEN: Verificar que main.py importa middleware."""
        # Arrange
        content = Path("app/main.py").read_text()

        # Assert
        assert "from app.middleware import" in content

    def test_main_module_has_cors_middleware(self):
        """GREEN: Verificar que main.py usa CORS middleware."""
        # Arrange
        content = Path("app/main.py").read_text()

        # Assert
        assert "CORSMiddleware" in content or "cors" in content.lower()

    def test_main_module_creates_app(self):
        """GREEN: Verificar que main.py crea FastAPI app."""
        # Arrange
        content = Path("app/main.py").read_text()

        # Assert
        assert "app = FastAPI" in content

    def test_main_module_has_logging_setup(self):
        """GREEN: Verificar que main.py configura logging."""
        # Arrange
        content = Path("app/main.py").read_text()

        # Assert
        assert "setup_logging" in content

    def test_main_module_size(self):
        """GREEN: Verificar que main.py tiene tamaño razonable."""
        # Arrange
        main_path = Path("app/main.py")

        # Assert - Debe tener al menos 1000 bytes
        assert main_path.stat().st_size > 1000, "main.py debe tener ≥1000 bytes"


if __name__ == "__main__":
    pytest.main([__file__])
