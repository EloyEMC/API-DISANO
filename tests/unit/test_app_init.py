"""
Tests Unitarios - App Init Execution (TDD)
=========================================

Tests que importan y ejecutan código real de app/__init__.py.
"""

import pytest


def test_app_init_version_exists():
    """GREEN: Verificar que app/__init__.py tiene versión."""
    try:
        import app

        assert hasattr(app, "__version__"), "app no tiene __version__"
    except ImportError as e:
        pytest.fail(f"Error importando app: {e}")


def test_app_init_version_is_string():
    """GREEN: Verificar que versión es string."""
    try:
        import app

        assert isinstance(app.__version__, str), "app.__version__ no es string"
    except ImportError as e:
        pytest.fail(f"Error importando app: {e}")


def test_app_init_version_not_empty():
    """GREEN: Verificar que versión no está vacía."""
    try:
        import app

        assert len(app.__version__) > 0, "app.__version__ está vacía"
    except ImportError as e:
        pytest.fail(f"Error importando app: {e}")


if __name__ == "__main__":
    pytest.main([__file__])
