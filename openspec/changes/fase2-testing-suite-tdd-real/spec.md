# Especificación: Fase 2 - Testing Suite con TDD Real

## Resumen Ejecutivo

Especificación técnica detallada para implementar Testing Suite con TDD Real en API-DISANO, alcanzando ≥80% coverage con ≈250 tests automatizados que validan comportamiento real siguiendo patrones BC3-Suite.

## Stack Tecnológico

### Framework de Testing

- **pytest**: Framework de testing principal
- **pytest-cov**: Medición de coverage
- **pytest-mock**: Mocking de dependencias
- **pytest-asyncio**: Tests de funciones async

### Base de Datos de Testing

- **testing/testing.db**: SQLite con 8,288 productos (copia de producción)
- **pytest fixtures**: db_session para transacciones aisladas
- **transacciones rollback**: Cada test limpia su estado

### Factories BC3-Suite

- **ProductoFactory**: Crea productos de prueba consistentes
- **OTPFactory**: Crea OTPs de prueba con expiración
- **UserFactory**: Crea usuarios de prueba con roles
- **RequestFactory**: Crea requests HTTP de prueba

## Arquitectura de Tests

### Estructura de Tests

```
tests/
├── conftest.py                    # Fixtures globales
├── factories/
│   └── factories.py               # Factories BC3-Suite
├── unit/
│   ├── test_config.py             # Tests de configuración
│   ├── test_security.py           # Tests de seguridad
│   ├── test_rate_limiter.py       # Tests de rate limiting
│   ├── test_middleware.py         # Tests de middleware
│   └── test_models.py             # Tests de modelos
└── integration/
    ├── test_productos_v1.py       # Tests de productos V1
    ├── test_productos_v2.py       # Tests de productos V2
    ├── test_admin_crud.py         # Tests de admin CRUD
    └── test_auth_idor.py          # Tests de auth IDOR
```

### Patrones de Testing

#### TDD Cycle (RED→GREEN→REFACTOR)

1. **RED**: Escribir test que falla
2. **GREEN**: Implementar código mínimo para pasar
3. **REFACTOR**: Mejorar código manteniendo tests verdes

#### AAA Pattern (Arrange-Act-Assert)

```python
def test_producto_precio_valido():
    # Arrange
    producto = ProductoFactory(precio=100.00)

    # Act
    resultado = producto.calcular_iva()

    # Assert
    assert resultado == 21.00
```

#### Factories BC3-Suite

```python
class ProductoFactory(factory.Factory):
    class Meta:
        model = Producto

    codigo = factory.Sequence(lambda n: f"PROD-{n:04d}")
    descripcion = "Producto de prueba"
    pvp = factory.Faker('random_int', min=1, max=1000)
```

## Especificaciones Detalladas por Módulo

### app/config.py (72% coverage → 100%)

**Objetivo:** 100% coverage
**Tests actuales:** 0
**Tests necesarios:** 5 tests de comportamiento

```python
# Tests de comportamiento real
def test_settings_secret_key_required():
    """RED: Settings debe fallar sin SECRET_KEY"""
    with pytest.raises(ValueError):
        Settings(secret_key="")

def test_settings_api_keys_required():
    """RED: Settings debe fallar sin API_KEYS"""
    with pytest.raises(ValueError):
        Settings(api_keys=[])

def test_settings_valid():
    """GREEN: Settings válidos"""
    settings = Settings(secret_key="test", api_keys=["test"])
    assert settings.secret_key == "test"

def test_settings_redis_url_default():
    """GREEN: Redis URL tiene default"""
    settings = Settings(secret_key="test", api_keys=["test"])
    assert "redis://" in settings.redis_url

def test_settings_field_validators():
    """GREEN: Field validators funcionan"""
    settings = Settings(secret_key="test", api_keys=["test"])
    assert len(settings.admin_api_keys) > 0
```

### app/middleware.py (37% coverage → 80%)

**Objetivo:** 80% coverage
**Tests actuales:** 19 tests (37% coverage)
**Tests necesarios:** 30 tests adicionales de comportamiento

```python
# Tests de comportamiento real
def test_middleware_rate_limit_blocks_excess_requests():
    """RED: Middleware debe bloquear después del límite"""
    # Arrange
    middleware = SecurityMiddleware(app)
    request = RequestFactory(ip="127.0.0.1", endpoint="/api/v2/productos")

    # Act
    responses = []
    for _ in range(100):  # Exceder rate limit
        response = await middleware(request)

    # Assert
    assert any(r.status_code == 429 for r in responses)

def test_middleware_cors_headers_present():
    """GREEN: CORS headers están presentes"""
    # Arrange
    middleware = SecurityMiddleware(app)
    request = RequestFactory(origin="http://localhost:3000")

    # Act
    response = await middleware(request)

    # Assert
    assert response.headers.get("Access-Control-Allow-Origin") == "*"

def test_middleware_scraping_detection():
    """GREEN: Bloquea requests de scrapers"""
    # Arrange
    middleware = SecurityMiddleware(app)
    request = RequestFactory(
        user_agent="Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    )

    # Act
    response = await middleware(request)

    # Assert
    assert response.status_code == 403
```

### app/security.py (0% coverage → 70%)

**Objetivo:** 70% coverage
**Tests actuales:** 0 tests
**Tests necesarios:** 20 tests de comportamiento

```python
# Tests de comportamiento real
def test_verify_admin_api_key_valid():
    """RED: API key válido debe pasar"""
    # Arrange
    request = RequestFactory(headers={"X-API-Key": "valid-key"})

    # Act
    result = verify_admin_api_key(request)

    # Assert
    assert result == True

def test_verify_admin_api_key_invalid():
    """RED: API key inválido debe fallar"""
    # Arrange
    request = RequestFactory(headers={"X-API-Key": "invalid-key"})

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        verify_admin_api_key(request)

    assert exc_info.value.status_code == 401

def test_otp_generation_valid_format():
    """GREEN: OTP tiene 6 dígitos"""
    # Act
    otp = generate_otp("user@test.com")

    # Assert
    assert len(otp.code) == 6
    assert otp.code.isdigit()

def test_otp_expiration_10_minutes():
    """GREEN: OTP expira en 10 minutos"""
    # Arrange
    otp = generate_otp("user@test.com")

    # Act
    from datetime import datetime, timedelta
    expired_at = otp.created_at + timedelta(minutes=10)
    assert expired_at > datetime.now()
```

### app/routers/productos.py (0% coverage → 60%)

**Objetivo:** 60% coverage
**Tests actuales:** 0 tests
**Tests necesarios:** 40 tests de comportamiento (V1 + V2)

```python
# Tests de comportamiento real (V1)
def test_get_productos_v1_returns_data():
    """RED: get_productos V1 retorna datos de testing.db"""
    # Arrange
    client = TestClient(app)
    db_session.create_producto(codigo="PROD-0001", descripcion="Test")

    # Act
    response = client.get("/api/productos?skip=0&limit=10")

    # Assert
    assert response.status_code == 200
    assert len(response.json()) <= 10

def test_get_producto_v1_codigo_existe():
    """GREEN: get_producto V1 retorna producto por código"""
    # Arrange
    client = TestClient(app)
    db_session.create_producto(codigo="PROD-0001", descripcion="Test")

    # Act
    response = client.get("/api/productos/PROD-0001")

    # Assert
    assert response.status_code == 200
    assert response.json()["codigo"] == "PROD-0001"

def test_get_producto_v1_codigo_no_existe():
    """GREEN: get_producto V1 retorna 404 si no existe"""
    # Arrange
    client = TestClient(app)

    # Act
    response = client.get("/api/productos/NOEXISTE")

    # Assert
    assert response.status_code == 404

# Tests de comportamiento real (V2)
def test_create_producto_v2_valid():
    """RED: create_producto V2 crea producto en testing.db"""
    # Arrange
    client = TestClient(app)
    producto_data = {
        "codigo": "PROD-NEW",
        "descripcion": "Nuevo producto",
        "pvp": 100.00
    }

    # Act
    response = client.post(
        "/api/v2/productos",
        json=producto_data,
        headers={"X-API-Key": "admin-key"}
    )

    # Assert
    assert response.status_code == 201
    assert response.json()["codigo"] == "PROD-NEW"

def test_update_producto_v2_valid():
    """GREEN: update_producto V2 actualiza producto en testing.db"""
    # Arrange
    client = TestClient(app)
    db_session.create_producto(codigo="PROD-0001", descripcion="Original")

    # Act
    response = client.put(
        "/api/v2/productos/PROD-0001",
        json={"descripcion": "Actualizado"},
        headers={"X-API-Key": "admin-key"}
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["descripcion"] == "Actualizado"

def test_delete_producto_v2_valid():
    """GREEN: delete_producto V2 elimina producto de testing.db"""
    # Arrange
    client = TestClient(app)
    db_session.create_producto(codigo="PROD-0001", descripcion="Test")

    # Act
    response = client.delete(
        "/api/v2/productos/PROD-0001",
        headers={"X-API-Key": "admin-key"}
    )

    # Assert
    assert response.status_code == 204

    # Assert - Verificar que fue eliminado
    response = client.get("/api/v2/productos/PROD-0001")
    assert response.status_code == 404
```

## Métricas y Métricas de Éxito

### Coverage por Módulo (Objetivos)

| Módulo | Current | Objetivo | Tests necesarios |
|--------|---------|----------|------------------|
| app/config.py | 72% | 100% | 5 tests |
| app/middleware.py | 37% | 80% | 30 tests |
| app/security.py | 0% | 70% | 20 tests |
| app/routers/productos.py | 0% | 60% | 40 tests |
| app/main.py | 0% | 50% | 10 tests |
| **TOTAL** | 22% | **≥80%** | **≈250 tests** |

### Métricas de Calidad

- **Tests de comportamiento**: 100% (no tests de estructura)
- **TDD Cycle aplicado**: 100%
- **Factories BC3-Suite**: 100%
- **testing.db usado**: 100%
- **production.db NO tocado**: 100%

## Configuración pytest

### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --tb=short
    -v
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
```

### scripts/run_pytest.py

```python
#!/usr/bin/env python3
"""Wrapper script para resolver bloqueo pydantic-settings"""

import os
import sys

# Configurar ADMIN_API_KEYS ANTES de limpiar variables
os.environ["ADMIN_API_KEYS"] = "test-key-1,test-key-2"

# Limpiar variables problemáticas
for key in ["SECRET_KEY", "API_KEYS", "DATABASE_URL"]:
    os.environ.pop(key, None)

# Importar y ejecutar pytest
import pytest
sys.exit(pytest.main(sys.argv[1:]))
```

## Entregables

### Entregables de Código

- tests/structure completa (unit/, integration/, factories/)
- conftest.py con fixtures globales
- factories.py con factories BC3-Suite
- ≈250 tests de comportamiento real
- pytest.ini configurado

### Entregables de Documentación

- Documentación de fixtures
- Documentación de factories
- Guía de TDD para el proyecto
- README de tests

### Entregables de Métricas

- Coverage report (html)
- Test report (xml)
- Métricas de calidad

## Dependencias Externas

- pytest (testing framework)
- pytest-cov (coverage measurement)
- pytest-mock (mocking)
- pytest-asyncio (async tests)
- factory_boy (factories)

## Siguientes Pasos

1. **Design**: Diseñar arquitectura de tests en detalle
2. **Tasks**: Crear tareas de implementación específicas
3. **Apply**: Implementar con TDD real (RED→GREEN→REFACTOR)
4. **Verify**: Validar ≥80% coverage y ≈250 tests
5. **Archive**: Cerrar Fase 2 y pasar a Fase 3
