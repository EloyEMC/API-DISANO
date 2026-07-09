#!/usr/bin/env python3
"""
Wrapper script para ejecutar pytest con entorno configurado
Evita bloqueo pydantic-settings configurando variables de entorno correctamente
"""

import os
import sys
import subprocess

# Paso 1: Limpiar variables de entorno problemáticas
problematic_vars = ['SECRET_KEY', 'API_KEYS', 'ADMIN_API_KEYS', 'ENVIRONMENT']
for var in problematic_vars:
    os.environ.pop(var, None)

# Paso 2: Configurar variables de entorno para testing
os.environ['ENVIRONMENT'] = 'testing'
os.environ['SECRET_KEY'] = 'test-secret-key-32-chars-safe-testing'
os.environ['API_KEYS'] = 'test-api-key-1,test-api-key-2'
os.environ['ADMIN_API_KEYS'] = 'test-admin-key-1'

# Paso 3: Ejecutar pytest con arguments pasados
pytest_args = sys.argv[1:] if len(sys.argv) > 1 else [
    "tests/unit/test_fase1_fixes.py::TestRateLimitBugFixed::test_rate_limit_variable_correctly_named",
    "tests/unit/test_fase1_fixes.py::TestLegacyImportsMigrated::test_no_legacy_imports_in_routers",
    "tests/unit/test_fase1_fixes.py::TestSecurityHeadersAdded::test_content_security_policy_header_exists",
    "-v"
]

print(f"🚀 Ejecutando pytest con entorno configurado...")
print(f"📋 Comando: pytest {' '.join(pytest_args)}")
print()

result = subprocess.run(
    ["source", ".venv/bin/activate", "&&", "python3", "-m", "pytest"] + pytest_args,
    shell=True,
    capture_output=False
)

sys.exit(result.returncode)