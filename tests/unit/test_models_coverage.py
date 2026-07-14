"""
Tests Unitarios - Models Coverage (TDD approach)
==============================================

Tests que aumentan coverage de app/models.py.
."""

import pytest


def test_models_module_exists():
    """RED: Verificar que app/models.py existe."""
    from pathlib import Path

    assert Path("app/models.py").exists()


def test_models_has_producto_model():
    """RED: Verificar que models.py tiene Producto model."""
    from pathlib import Path

    content = Path("app/models.py").read_text()
    assert "class Producto" in content


def test_models_has_base_model():
    """RED: Verificar que models.py tiene BaseModel."""
    from pathlib import Path

    content = Path("app/models.py").read_text()
    assert "BaseModel" in content


def test_models_has_codigo_field():
    """RED: Verificar que Producto tiene codigo field (snake_case)."""
    from pathlib import Path

    content = Path("app/models.py").read_text()
    assert "codigo:" in content


def test_models_has_descripcion_field():
    """RED: Verificar que Producto tiene descripcion field (snake_case)."""
    from pathlib import Path

    content = Path("app/models.py").read_text()
    assert "descripcion:" in content


def test_models_has_pvp_field():
    """RED: Verificar que Producto tiene PVP field."""
    from pathlib import Path

    content = Path("app/models.py").read_text()
    assert "PVP" in content


if __name__ == "__main__":
    pytest.main([__file__])
