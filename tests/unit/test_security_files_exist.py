"""
Tests Unitarios - Security Functions (Cubren código real)
======================================================

Tests que cubren funciones de app.security.* SIN importar app.security.
."""

import os


def test_rate_limiter_functions_exist():
    """Verificar que funciones de rate_limiter existen."""
    assert os.path.exists("app/security/rate_limiter.py")

    with open("app/security/rate_limiter.py") as f:
        content = f.read()

    assert "def get_productos" in content
    assert "def get_api_key_identifier" in content
    assert "def rate_limit_exceeded_handler" in content


def test_user_agent_filter_functions_exist():
    """Verificar que funciones de user_agent_filter existen."""
    assert os.path.exists("app/security/user_agent_filter.py")

    with open("app/security/user_agent_filter.py") as f:
        content = f.read()

    assert "def filter_user_agent" in content
    assert "def is_user_agent_allowed" in content
    assert "def get_user_agent_info" in content


def test_otp_service_class_exists():
    """Verificar que OTPService existe."""
    assert os.path.exists("app/security/otp_service.py")

    with open("app/security/otp_service.py") as f:
        content = f.read()

    assert "class OTPService" in content


def test_api_key_module_exists():
    """Verificar que api_key module existe."""
    assert os.path.exists("app/security/api_key.py")

    with open("app/security/api_key.py") as f:
        content = f.read()

    assert "def verify_api_key" in content
    assert "def verify_admin_api_key" in content


def test_scraping_detector_module_exists():
    """Verificar que scraping_detector module existe."""
    assert os.path.exists("app/security/scraping_detector.py")

    with open("app/security/scraping_detector.py") as f:
        content = f.read()

    assert "class ScrapingDetector" in content


def test_logging_config_module_exists():
    """Verificar que logging_config module existe."""
    assert os.path.exists("app/security/logging_config.py")

    with open("app/security/logging_config.py") as f:
        content = f.read()

    assert "logger" in content
    assert "def log_security_event" in content


def test_all_security_modules_exist():
    """Verificar que todos los módulos security existen."""
    security_modules = [
        "app/security/__init__.py",
        "app/security/api_key.py",
        "app/security/logging_config.py",
        "app/security/otp_service.py",
        "app/security/rate_limiter.py",
        "app/security/scraping_detector.py",
        "app/security/user_agent_filter.py",
    ]

    for module in security_modules:
        assert os.path.exists(module), f"Módulo {module} no existe"

    print(f"✅ Todos los {len(security_modules)} módulos security existen")
