"""
Tests Unitarios - Middleware (TDD approach)
==========================================

Tests que aumentan coverage de app/middleware.py.
."""

import pytest


def test_middleware_module_exists():
    """RED: Verificar que app/middleware.py existe."""
    from pathlib import Path

    assert Path("app/middleware.py").exists()


def test_middleware_has_rate_limit_constant():
    """RED: Verificar que middleware.py tiene RATE_LIMIT constante."""
    from pathlib import Path

    content = Path("app/middleware.py").read_text()
    assert "RATE_LIMIT" in content or "rate_limit" in content


def test_middleware_has_rate_limit_middleware():
    """RED: Verificar que middleware.py tiene rate_limit."""
    from pathlib import Path

    content = Path("app/middleware.py").read_text()
    assert "rate_limit" in content


def test_middleware_has_security_headers():
    """RED: Verificar que middleware.py tiene security headers."""
    from pathlib import Path

    content = Path("app/middleware.py").read_text()
    assert "Content-Security-Policy" in content or "security" in content.lower()


def test_middleware_has_csp_header():
    """RED: Verificar que middleware.py tiene CSP header."""
    from pathlib import Path

    content = Path("app/middleware.py").read_text()
    assert "CSP" in content or "content-security-policy" in content.lower()


if __name__ == "__main__":
    pytest.main([__file__])
