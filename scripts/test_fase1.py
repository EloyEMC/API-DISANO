#!/usr/bin/env python3
"""
Script de prueba manual - Fase 1 Validations
=============================================

Verifica manualmente que las correcciones de Fase 1 funcionan sin instalar dependencias.
"""

from pathlib import Path
import sys


def test_bug_rate_limit_fixed():
    """Verificar que el bug RATE_LIMIT ha sido corregido."""
    print("✓ Test 1: Bug RATE_LIMIT corregido")

    middleware_path = Path(__file__).parent.parent / "app" / "middleware.py"
    content = middleware_path.read_text()

    # Buscar patrones de bug
    has_bug = "str(RATE_LIMIT)" in content
    has_fix = '"X-RateLimit-Limit": str(rate_limit)' in content

    if has_bug:
        print("  ❌ FAIL: Variable RATE_LIMIT incorrecta encontrada")
        return False

    if has_fix:
        print("  ✅ PASS: Variable rate_limit usada correctamente")
        return True

    print("  ⚠️  WARN: No se encontraron patrones de rate limiting")
    return False


def test_legacy_imports_migrated():
    """Verificar que los imports legacy han sido migrados."""
    print("✓ Test 2: Imports legacy migrados")

    productos_path = Path(__file__).parent.parent / "app" / "routers" / "productos.py"
    content = productos_path.read_text()

    has_legacy = "from app.security import verify_admin_api_key" in content
    has_new = "from app.security.api_key import verify_admin_api_key" in content

    if has_legacy:
        print("  ❌ FAIL: Import legacy aún existe")
        return False

    if has_new:
        print("  ✅ PASS: Import nuevo correcto")
        return True

    print("  ⚠️  WARN: No se encontró import nuevo")
    return False


def test_security_headers_added():
    """Verificar que los security headers han sido añadidos."""
    print("✓ Test 3: Security headers añadidos")

    middleware_path = Path(__file__).parent.parent / "app" / "middleware.py"
    content = middleware_path.read_text()

    headers_check = {
        "Content-Security-Policy": "Content-Security-Policy" in content,
        "X-Content-Type-Options": "X-Content-Type-Options" in content,
        "X-Frame-Options": "X-Frame-Options" in content,
        "X-XSS-Protection": "X-XSS-Protection" in content,
        "Referrer-Policy": "Referrer-Policy" in content,
    }

    all_present = all(headers_check.values())

    if all_present:
        print("  ✅ PASS: Todos los security headers presentes")
        for header, present in headers_check.items():
            print(f"    - {header}: {'✅' if present else '❌'}")
        return True

    print("  ❌ FAIL: Faltan security headers")
    for header, present in headers_check.items():
        if not present:
            print(f"    - {header}: ❌")
    return False


def test_required_env_vars_validation():
    """Verificar que se valida SECRET_KEY y API_KEYS en producción."""
    print("✓ Test 4: Validación de variables obligatorias")

    config_path = Path(__file__).parent.parent / "app" / "config.py"
    content = config_path.read_text()

    has_validate_method = "def validate_required(self)" in content
    has_secret_check = "SECRET_KEY" in content
    has_api_keys_check = "API_KEYS" in content
    has_production_check = "if self.is_production():" in content

    all_present = all(
        [
            has_validate_method,
            has_secret_check,
            has_api_keys_check,
            has_production_check,
        ]
    )

    if all_present:
        print("  ✅ PASS: Validación de variables obligatorias implementada")
        return True

    print("  ❌ FAIL: Faltan componentes de validación")
    return False


def test_otp_service_exists():
    """Verificar que el servicio OTP existe y tiene estructura correcta."""
    print("✓ Test 5: Servicio OTP implementado")

    otp_service_path = (
        Path(__file__).parent.parent / "app" / "security" / "otp_service.py"
    )
    if not otp_service_path.exists():
        print("  ❌ FAIL: Archivo otp_service.py no existe")
        return False

    content = otp_service_path.read_text()

    has_class = "class OTPService" in content
    has_generate = "def generate_otp" in content
    has_verify = "def verify_otp" in content
    has_constants = "otp_expiry_minutes = 10" in content
    has_max_attempts = "max_attempts = 3" in content
    has_otp_length = "otp_length = 6" in content

    all_present = all(
        [
            has_class,
            has_generate,
            has_verify,
            has_constants,
            has_max_attempts,
            has_otp_length,
        ]
    )

    if all_present:
        print("  ✅ PASS: Servicio OTP completo con constantes correctas")
        return True

    print("  ❌ FAIL: Faltan componentes del servicio OTP")
    for component, present in {
        "class OTPService": has_class,
        "generate_otp": has_generate,
        "verify_otp": has_verify,
        "10 min expiry": has_constants,
        "3 max attempts": has_max_attempts,
        "6-digit OTP": has_otp_length,
    }.items():
        if not present:
            print(f"    - {component}: ❌")
    return False


def test_logging_configured():
    """Verificar que el logging está configurado."""
    print("✓ Test 6: Logging estructurado configurado")

    main_path = Path(__file__).parent.parent / "app" / "main.py"
    content = main_path.read_text()

    has_import = "from app.security.logging_config import setup_logging" in content
    has_call = "setup_logging()" in content

    if has_import and has_call:
        print("  ✅ PASS: Logging estructurado configurado")
        return True

    print("  ❌ FAIL: Logging no configurado")
    return False


def test_redis_middleware_exists():
    """Verificar que el middleware Redis existe."""
    print("✓ Test 7: Middleware Redis creado")

    redis_middleware_path = Path(__file__).parent.parent / "app" / "middleware_redis.py"
    if not redis_middleware_path.exists():
        print("  ❌ FAIL: Archivo middleware_redis.py no existe")
        return False

    content = redis_middleware_path.read_text()

    has_class = "class RedisRateLimitMiddleware" in content
    has_redis_docs = "# Rate Limiting Middleware with Redis" in content
    has_fallback = "rate_limit_store" in content  # In-memory fallback

    all_present = all([has_class, has_redis_docs, has_fallback])

    if all_present:
        print("  ✅ PASS: Middleware Redis creado con fallback in-memory")
        return True

    print("  ❌ FAIL: Faltan componentes del middleware Redis")
    return False


def test_env_production_template_exists():
    """Verificar que existe el template de .env.production."""
    print("✓ Test 8: Plantilla .env.production existe")

    env_template_path = Path(__file__).parent.parent / ".env.production.example"
    if not env_template_path.exists():
        print("  ❌ FAIL: Archivo .env.production.example no existe")
        return False

    content = env_template_path.read_text()

    required_vars = [
        "SECRET_KEY=",
        "API_KEYS=",
        "ADMIN_API_KEYS=",
        "REDIS_HOST=",
        "DATABASE_URL=postgresql://",
        "MAIL_SERVER=",
        "OTP_2FA_ENABLED=true",
    ]

    missing = [var for var in required_vars if var not in content]

    if not missing:
        print("  ✅ PASS: Plantilla completa con todas las variables requeridas")
        return True

    print(f"  ❌ FAIL: Faltan variables: {', '.join(missing)}")
    return False


def main():
    """Ejecutar todas las pruebas de Fase 1."""
    print("=" * 60)
    print("FASE 1 - VALIDACIÓN MANUAL")
    print("=" * 60)
    print()

    tests = [
        test_bug_rate_limit_fixed,
        test_legacy_imports_migrated,
        test_security_headers_added,
        test_required_env_vars_validation,
        test_otp_service_exists,
        test_logging_configured,
        test_redis_middleware_exists,
        test_env_production_template_exists,
    ]

    results = [test() for test in tests]

    print()
    print("=" * 60)
    print(f"RESULTADOS: {sum(results)}/{len(results)} tests pasaron")
    print("=" * 60)

    if all(results):
        print("✅ FASE 1 COMPLETADA - Todos los tests pasaron")
        return 0
    else:
        print("❌ FASE 1 INCOMPLETA - Algunos tests fallaron")
        return 1


if __name__ == "__main__":
    sys.exit(main())
