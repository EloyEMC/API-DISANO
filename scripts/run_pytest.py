#!/usr/bin/env python3
"""
Ejecutar pytest con entorno limpio para evitar pydantic-settings bloqueo
"""

import os
import subprocess
import sys

# Paso 0: Configurar variables de entorno LIMPIAS para testing (ANTES de limpiar)
os.environ["ENVIRONMENT"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key-32-chars-safe-testing"
os.environ["API_KEYS"] = "test-api-key-1,test-api-key-2"
os.environ["ADMIN_API_KEYS"] = "test-admin-key-1"
os.environ["DATABASE_URL"] = "testing/testing.db"  # Configurar database para tests
# Paso 1: Limpiar variables de problema EXCEPTO ADMIN_API_KEYS y DATABASE_URL
problematic_vars = [
    "CORS_ORIGINS",
    "REDIS_URL",
    "BC3_SUITE_URL",
    "BC3_SUITE_API_KEY",
    "ZAI_API_KEY",
    "ZAI_BASE_URL",
]
for var in problematic_vars:
    os.environ.pop(var, None)
print("🔧 Entorno configurado para testing:")
print(f"  ENVIRONMENT: {os.environ['ENVIRONMENT']}")
print(f"  API_KEYS: {os.environ['API_KEYS']}")
print(f"  ADMIN_API_KEYS: {os.environ['ADMIN_API_KEYS']}")
print()
# Paso 3: Ejecutar pytest con arguments
pytest_args = (
    sys.argv[1:]
    if len(sys.argv) > 1
    else [
        "tests/unit/test_fase1_fixes.py::TestRateLimitBugFixed::test_rate_limit_variable_correctly_named",
        "tests/unit/test_fase1_fixes.py::TestLegacyImportsMigrated::test_no_legacy_imports_in_routers",
        "tests/unit/test_fase1_fixes.py::TestSecurityHeadersAdded::test_content_security_policy_header_exists",
        "-v",
    ]
)
print(f"🚀 Ejecutando: pytest {' '.join(pytest_args)}")
print("=" * 60)
result = subprocess.run(
    ["python3", "-m", "pytest"] + pytest_args,
    cwd=os.getcwd(),
    capture_output=False,
)
print("=" * 60)
print(f"📋 Exit code: {result.returncode}")
sys.exit(result.returncode)
