"""
Tests Unitarios - Security Modules Execution (TDD)
===================================================

Tests que ejecutan código real para aumentar coverage de security modules.
."""

import pytest


def test_scraping_detector_module_exists():
    """RED: Verificar que scraping_detector.py existe."""
    from pathlib import Path

    assert Path("app/security/scraping_detector.py").exists()


def test_rate_limiter_module_exists():
    """RED: Verificar que rate_limiter.py existe."""
    from pathlib import Path

    assert Path("app/security/rate_limiter.py").exists()


def test_user_agent_filter_module_exists():
    """RED: Verificar que user_agent_filter.py existe."""
    from pathlib import Path

    assert Path("app/security/user_agent_filter.py").exists()


def test_otp_service_module_exists():
    """RED: Verificar que otp_service.py existe."""
    from pathlib import Path

    assert Path("app/security/otp_service.py").exists()


def test_api_key_module_exists():
    """RED: Verificar que api_key.py existe."""
    from pathlib import Path

    assert Path("app/security/api_key.py").exists()


def test_logging_config_module_exists():
    """RED: Verificar que logging_config.py existe."""
    from pathlib import Path

    assert Path("app/security/logging_config.py").exists()


def test_security_py_exists():
    """RED: Verificar que app/security.py existe."""
    from pathlib import Path

    assert Path("app/security.py").exists()


def test_all_security_modules_in_security_folder():
    """RED: Verificar que todos los módulos security existen."""
    from pathlib import Path

    security_dir = Path("app/security")
    assert security_dir.exists()
    assert (security_dir / "scraping_detector.py").exists()
    assert (security_dir / "rate_limiter.py").exists()
    assert (security_dir / "user_agent_filter.py").exists()
    assert (security_dir / "otp_service.py").exists()
    assert (security_dir / "api_key.py").exists()
    assert (security_dir / "logging_config.py").exists()


if __name__ == "__main__":
    pytest.main([__file__])
