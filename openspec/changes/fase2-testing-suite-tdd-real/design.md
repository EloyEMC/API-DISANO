# Diseño: Fase 2 - Testing Suite con TDD Real

## Resumen Ejecutivo

Diseño arquitectónico para implementar Testing Suite con TDD Real en API-DISANO, definiendo estructura, patrones, factories y workflows para alcanzar ≥80% coverage con ≈250 tests de comportamiento real.

## Arquitectura de Tests

### Estructura de Directorios

```
tests/
├── __init__.py
├── conftest.py                    # Fixtures globales pytest
├── factories/
│   ├── __init__.py
│   ├── factories.py               # Factories BC3-Suite
│   ├── producto_factory.py        # ProductoFactory
│   ├── otp_factory.py             # OTPFactory
│   ├── user_factory.py            # UserFactory
│   └── request_factory.py         # RequestFactory
├── unit/
│   ├── __init__.py
│   ├── test_config.py             # Tests de configuración (5 tests)
│   ├── test_security.py           # Tests de seguridad (20 tests)
│   ├── test_rate_limiter.py       # Tests de rate limiting (10 tests)
│   ├── test_middleware.py         # Tests de middleware (30 tests)
│   ├── test_otp_service.py        # Tests de OTP service (10 tests)
│   └── test_models.py             # Tests de modelos (15 tests)
└── integration/
    ├── __init__.py
    ├── test_productos_v1.py       # Tests de productos V1 (20 tests)
    ├── test_productos_v2.py       # Tests de productos V2 (30 tests)
    ├── test_admin_crud.py         # Tests de admin CRUD (30 tests)
    ├── test_auth_idor.py          # Tests de auth IDOR (20 tests)
    └── test_end_to_end.py         # Tests e2e simples (20 tests)
```

## Patrones de Diseño

### TDD Cycle (RED→GREEN→REFACTOR)

```python
# Ejemplo: TDD para producto_precio_valido

# 1. RED: Test que falla ( código NO existe aún)
def test_producto_precio_valido():
    """RED: Producto debe validar precio positivo"""
    producto = ProductoFactory(precio=-10.00)
    with pytest.raises(ValueError):
        producto.validar_precio()

# 2. GREEN: Implementación mínima para pasar
def validar_precio(self):
    if self.precio < 0:
        raise ValueError("Precio debe ser positivo")
    return True

# 3. REFACTOR: Mejorar código manteniendo tests verdes
def validar_precio(self):
    """Valida que el precio sea positivo"""
    if self.precio <= 0:
        raise ValueError(f"Precio debe ser positivo: {self.precio}")
    return self.precio
```

### AAA Pattern (Arrange-Act-Assert)

```python
def test_producto_precio_iva_calculado():
    """
    AAA: Test de cálculo de IVA
    Arrange: Preparar datos de prueba
    Act: Ejecutar lógica a probar
    Assert: Verificar resultado esperado
    """
    # Arrange
    producto = ProductoFactory(precio=100.00)

    # Act
    resultado = producto.calcular_iva()

    # Assert
    assert resultado == 21.00  # 21% IVA
```

### Factories BC3-Suite

```python
import factory
from factory.fuzzy import FuzzyDecimal, FuzzyInteger
from app.models import Producto

class ProductoFactory(factory.Factory):
    """Factory BC3-Suite para crear productos de prueba consistentes"""

    class Meta:
        model = Producto
        sqlalchemy_session_persistence = "commit"

    # Datos consistentes y realistas
    codigo = factory.Sequence(lambda n: f"PROD-{n:04d}")
    descripcion = factory.Faker("sentence", nb_words=4)
    marca = factory.Faker("company")
    pvp = FuzzyDecimal(1.00, 1000.00, 2)

    # BC3 Suite integration fields
    bc3_descripcion_corta = factory.Faker("word")
    bc3_descripcion_larga = factory.Faker("text", max_nb_chars=200)
    bc3_product_type = factory.Faker("word")
    bc3_descripcion_completa = factory.Faker("text", max_nb_chars=500)
```

## Fixtures pytest

### Fixtures Globales (conftest.py)

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base
from app.models import Producto

# Database de testing
TEST_DB_URL = "sqlite:///testing/testing.db"

@pytest.fixture(scope="session")
def db_engine():
    """Engine de database para tests (session scope)"""
    engine = create_engine(TEST_DB_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()

@pytest.fixture
def db_session(db_engine):
    """Session de database para tests (function scope, rollback)"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client():
    """TestClient de FastAPI para tests de integración"""
    return TestClient(app)

@pytest.fixture
def admin_headers():
    """Headers con API key de admin"""
    return {"X-API-Key": "admin-test-key"}

@pytest.fixture
def user_headers():
    """Headers con API key de usuario"""
    return {"X-API-Key": "user-test-key"}
```

### Fixtures de Factories

```python
@pytest.fixture
def producto_factory(db_session):
    """Factory para crear productos en testing.db"""
    def create_producto(**kwargs):
        producto = ProductoFactory(**kwargs)
        db_session.add(producto)
        db_session.commit()
        return producto

    return create_producto

@pytest.fixture
def otp_factory(db_session):
    """Factory para crear OTPs en testing.db"""
    def create_otp(**kwargs):
        otp = OTPFactory(**kwargs)
        db_session.add(otp)
        db_session.commit()
        return otp

    return create_otp
```

## Workflows de Testing

### Workflow Unit Tests

```
1. RED: Escribir test que falla
   - Definir comportamiento esperado
   - Crear test AAA pattern
   - Ejecutar pytest → FAIL

2. GREEN: Implementar código mínimo
   - Escribir implementación mínima
   - Ejecutar pytest → PASS

3. REFACTOR: Mejorar código
   - Optimizar sin cambiar comportamiento
   - Ejecutar pytest → PASS
   - Verificar coverage incrementó
```

### Workflow Integration Tests

```
1. RED: Escribir test de endpoint que falla
   - Crear datos con factories
   - Hacer request con TestClient
   - Verificar response esperado
   - Ejecutar pytest → FAIL

2. GREEN: Implementar endpoint mínimo
   - Crear/actualizar endpoint
   - Hacer request con TestClient
   - Verificar response esperado
   - Ejecutar pytest → PASS

3. REFACTOR: Mejorar endpoint
   - Optimizar sin cambiar comportamiento
   - Verificar docs API
   - Ejecutar pytest → PASS
```

## Arquitectura de Tests por Módulo

### app/config.py Tests

```python
class TestConfigSettings:
    """Tests de comportamiento real para app/config.py"""

    def test_settings_secret_key_required():
        """RED: Settings debe fallar sin SECRET_KEY"""
        with pytest.raises(ValueError):
            Settings(secret_key="")

    def test_settings_api_keys_required():
        """RED: Settings debe fallar sin API_KEYS"""
        with pytest.raises(ValueError):
            Settings(api_keys=[])

    def test_settings_valid_configuration():
        """GREEN: Settings válidos funcionan"""
        settings = Settings(
            secret_key="test-secret",
            api_keys=["key1", "key2"]
        )
        assert settings.secret_key == "test-secret"

    def test_settings_redis_url_has_default():
        """GREEN: Redis URL tiene default razonable"""
        settings = Settings(
            secret_key="test",
            api_keys=["key"]
        )
        assert "redis://" in settings.redis_url

    def test_settings_admin_api_keys_field_validator():
        """GREEN: admin_api_keys field validator funciona"""
        settings = Settings(
            secret_key="test",
            api_keys=["key1", "key2"]
        )
        assert len(settings.admin_api_keys) > 0
```

### app/middleware.py Tests

```python
class TestSecurityMiddleware:
    """Tests de comportamiento real para app/middleware.py"""

    def test_middleware_blocks_rate_limit_exceeded(self):
        """RED: Bloquea requests después de rate limit"""
        # Arrange
        middleware = SecurityMiddleware(app)
        request = RequestFactory(
            ip="127.0.0.1",
            endpoint="/api/v2/productos"
        )

        # Act
        responses = []
        for _ in range(100):  # Exceder rate limit
            response = await middleware(request)
            responses.append(response)

        # Assert
        assert any(r.status_code == 429 for r in responses)

    def test_middleware_cors_headers_present(self):
        """GREEN: CORS headers están presentes"""
        # Arrange
        middleware = SecurityMiddleware(app)
        request = RequestFactory(origin="http://localhost:3000")

        # Act
        response = await middleware(request)

        # Assert
        assert response.headers.get("Access-Control-Allow-Origin") == "*"

    def test_middleware_scraping_detection_blocks(self):
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

    def test_middleware_valid_request_passes(self):
        """GREEN: Requests válidos pasan"""
        # Arrange
        middleware = SecurityMiddleware(app)
        request = RequestFactory(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            ip="192.168.1.100"
        )

        # Act
        response = await middleware(request)

        # Assert
        assert response.status_code not in [403, 429]
```

### app/security.py Tests

```python
class TestSecurityFunctions:
    """Tests de comportamiento real para app/security.py"""

    def test_verify_admin_api_key_valid(self):
        """RED: API key válido debe pasar"""
        # Arrange
        request = RequestFactory(
            headers={"X-API-Key": "admin-test-key"}
        )

        # Act
        result = verify_admin_api_key(request)

        # Assert
        assert result is True

    def test_verify_admin_api_key_invalid(self):
        """RED: API key inválido debe fallar"""
        # Arrange
        request = RequestFactory(
            headers={"X-API-Key": "invalid-key"}
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            verify_admin_api_key(request)

        assert exc_info.value.status_code == 401

    def test_verify_admin_api_key_missing(self):
        """RED: API key faltante debe fallar"""
        # Arrange
        request = RequestFactory(headers={})

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            verify_admin_api_key(request)

        assert exc_info.value.status_code == 401

    def test_otp_generation_format_valid(self):
        """GREEN: OTP tiene formato válido"""
        # Act
        otp = generate_otp("user@test.com")

        # Assert
        assert len(otp.code) == 6
        assert otp.code.isdigit()

    def test_otp_expiration_10_minutes(self):
        """GREEN: OTP expira en 10 minutos"""
        # Arrange
        otp = generate_otp("user@test.com")

        # Act
        from datetime import datetime, timedelta
        expired_at = otp.created_at + timedelta(minutes=10)

        # Assert
        assert expired_at > datetime.now()
```

### app/routers/productos.py Tests (Integration)

```python
class TestProductosV1Integration:
    """Tests de integración para productos V1"""

    def test_get_productos_returns_data_from_testing_db(self):
        """RED: get_productos V1 retorna datos de testing.db"""
        # Arrange
        client = TestClient(app)
        db_session.add(ProductoFactory(
            codigo="PROD-0001",
            descripcion="Producto de prueba"
        ))
        db_session.commit()

        # Act
        response = client.get("/api/productos?skip=0&limit=10")

        # Assert
        assert response.status_code == 200
        assert len(response.json()) <= 10
        assert any(p["codigo"] == "PROD-0001" for p in response.json())

    def test_get_producto_by_codigo_exists(self):
        """GREEN: get_producto V1 retorna producto por código"""
        # Arrange
        client = TestClient(app)
        db_session.add(ProductoFactory(
            codigo="PROD-TEST",
            descripcion="Test producto"
        ))
        db_session.commit()

        # Act
        response = client.get("/api/productos/PROD-TEST")

        # Assert
        assert response.status_code == 200
        assert response.json()["codigo"] == "PROD-TEST"

    def test_get_producto_by_codigo_not_exists(self):
        """GREEN: get_producto V1 retorna 404 si no existe"""
        # Arrange
        client = TestClient(app)

        # Act
        response = client.get("/api/productos/NOEXISTE")

        # Assert
        assert response.status_code == 404
```

class TestProductosV2Integration:
    """Tests de integración para productos V2"""

    def test_create_producto_valid(self):
        """RED: create_producto V2 crea producto en testing.db"""
        # Arrange
        client = TestClient(app)
        producto_data = {
            "codigo": "PROD-NEW",
            "descripcion": "Nuevo producto",
            "pvp": 100.00,
            "marca": "Test"
        }

        # Act
        response = client.post(
            "/api/v2/productos",
            json=producto_data,
            headers=admin_headers
        )

        # Assert
        assert response.status_code == 201
        assert response.json()["codigo"] == "PROD-NEW"

    def test_create_producto_duplicate_codigo(self):
        """RED: create_producto V2 rechaza código duplicado"""
        # Arrange
        client = TestClient(app)
        db_session.add(ProductoFactory(codigo="PROD-DUP"))
        db_session.commit()

        producto_data = {
            "codigo": "PROD-DUP",
            "descripcion": "Duplicado",
            "pvp": 100.00
        }

        # Act
        response = client.post(
            "/api/v2/productos",
            json=producto_data,
            headers=admin_headers
        )

        # Assert
        assert response.status_code == 400

    def test_update_producto_valid(self):
        """GREEN: update_producto V2 actualiza producto"""
        # Arrange
        client = TestClient(app)
        db_session.add(ProductoFactory(
            codigo="PROD-UPDATE",
            descripcion="Original"
        ))
        db_session.commit()

        # Act
        response = client.put(
            "/api/v2/productos/PROD-UPDATE",
            json={"descripcion": "Actualizado"},
            headers=admin_headers
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["descripcion"] == "Actualizado"

    def test_delete_producto_valid(self):
        """GREEN: delete_producto V2 elimina producto"""
        # Arrange
        client = TestClient(app)
        db_session.add(ProductoFactory(
            codigo="PROD-DELETE",
            descripcion="A eliminar"
        ))
        db_session.commit()

        # Act
        response = client.delete(
            "/api/v2/productos/PROD-DELETE",
            headers=admin_headers
        )

        # Assert
        assert response.status_code == 204

        # Assert - Verificar que fue eliminado
        response = client.get("/api/v2/productos/PROD-DELETE")
        assert response.status_code == 404

class TestAuthIDOR:
    """Tests de Auth IDOR (Insecure Direct Object Reference)"""

    def test_user_cannot_access_admin_endpoints(self):
        """RED: Usuario no puede acceder a admin endpoints"""
        # Arrange
        client = TestClient(app)

        # Act
        response = client.post(
            "/api/v2/productos",
            json={"codigo": "PROD-NEW", "descripcion": "Test"},
            headers=user_headers  # NO admin_headers
        )

        # Assert
        assert response.status_code == 403

    def test_admin_can_access_admin_endpoints(self):
        """GREEN: Admin puede acceder a admin endpoints"""
        # Arrange
        client = TestClient(app)

        # Act
        response = client.post(
            "/api/v2/productos",
            json={"codigo": "PROD-NEW", "descripcion": "Test"},
            headers=admin_headers  # admin_headers
        )

        # Assert
        assert response.status_code in [201, 400]  # 201 si OK, 400 si duplicado

```

## Métricas de Diseño

### Coverage por Módulo

| Módulo | Current | Target | Tests necesarios | Strategy |
|--------|---------|--------|------------------|----------|
| app/config.py | 72% | 100% | 5 tests | Unit tests simples |
| app/middleware.py | 37% | 80% | 30 tests | Rate limiting, CORS, scraping |
| app/security.py | 0% | 70% | 20 tests | API key validation, OTP |
| app/routers/productos.py | 0% | 60% | 40 tests | Integration tests con client |
| app/main.py | 0% | 50% | 10 tests | Startup, root endpoint |
| **TOTAL** | 22% | **≥80%** | **≈250 tests** | Unit + Integration |

### Tests por Categoría

| Categoría | Tests | Coverage target |
|-----------|-------|-----------------|
| Unit tests | 90 | 100% (internal logic) |
| Integration tests | 150 | 60% (external deps) |
| Auth IDOR tests | 10 | 100% (security critical) |
| **TOTAL** | **250** | **≥80%** |

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
    --cov-report=html:htmlcov
    --cov-report=term-missing
    --tb=short
    -v
    --strict-markers
markers =
    unit: Unit tests (internal logic)
    integration: Integration tests (external dependencies)
    auth_idor: Security tests (IDOR prevention)
    slow: Slow tests (skip in CI)
asyncio_mode = auto
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

## Workflows de Implementación

### Workflow Unit Tests

```python
# 1. RED: Escribir test que falla
def test_producto_precio_negativo_rejects():
    """RED: Producto debe rechazar precio negativo"""
    producto = ProductoFactory(precio=-10.00)
    with pytest.raises(ValueError):
        producto.validar_precio()

# Ejecutar: pytest tests/unit/test_models.py -k test_producto_precio_negativo_rejects
# Resultado: FAIL (método validar_precio NO existe aún)

# 2. GREEN: Implementar código mínimo
class Producto:
    def validar_precio(self):
        if self.precio < 0:
            raise ValueError("Precio debe ser positivo")
        return True

# Ejecutar: pytest tests/unit/test_models.py -k test_producto_precio_negativo_rejects
# Resultado: PASS

# 3. REFACTOR: Mejorar código
class Producto:
    def validar_precio(self):
        """Valida que el precio sea positivo"""
        if self.precio <= 0:
            raise ValueError(f"Precio debe ser positivo: {self.precio}")
        return self.precio

# Ejecutar: pytest tests/unit/test_models.py -k test_producto_precio_negativo_rejects
# Resultado: PASS (mejor código, mismo comportamiento)
```

### Workflow Integration Tests

```python
# 1. RED: Escribir test de endpoint que falla
def test_create_producto_integration():
    """RED: create_producto endpoint debe crear producto"""
    # Arrange
    client = TestClient(app)
    producto_data = {
        "codigo": "PROD-NEW",
        "descripcion": "Test",
        "pvp": 100.00
    }

    # Act
    response = client.post(
        "/api/v2/productos",
        json=producto_data,
        headers=admin_headers
    )

    # Assert
    assert response.status_code == 201

# Ejecutar: pytest tests/integration/test_productos_v2.py -k test_create_producto_integration
# Resultado: FAIL (endpoint NO existe o lógica incompleta)

# 2. GREEN: Implementar endpoint mínimo
@router.post("/productos", dependencies=[Depends(verify_admin_api_key)])
async def create_producto(producto: ProductoCreateV2):
    """Crea producto en database"""
    # Crear producto en database
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO productos (codigo, descripcion, pvp) VALUES (?, ?, ?)",
        (producto.codigo, producto.descripcion, producto.pvp)
    )
    db.commit()
    return {"status": "created", "codigo": producto.codigo}

# Ejecutar: pytest tests/integration/test_productos_v2.py -k test_create_producto_integration
# Resultado: PASS

# 3. REFACTOR: Mejorar endpoint
@router.post("/productos", dependencies=[Depends(verify_admin_api_key)])
async def create_producto(producto: ProductoCreateV2, request: Request):
    """
    Crea producto en database
    - Valida datos de entrada
    - Maneja códigos duplicados
    - Retorna response HTTP apropiado
    """
    db = get_db_connection()

    # Validar código duplicado
    cursor = db.cursor()
    cursor.execute("SELECT 1 FROM productos WHERE codigo = ?", (producto.codigo,))
    if cursor.fetchone():
        raise HTTPException(
            status_code=400,
            detail=f"Producto con código {producto.codigo} ya existe"
        )

    # Crear producto
    cursor.execute(
        "INSERT INTO productos (codigo, descripcion, pvp) VALUES (?, ?, ?)",
        (producto.codigo, producto.descripcion, producto.pvp)
    )
    db.commit()

    return {"status": "created", "codigo": producto.codigo}

# Ejecutar: pytest tests/integration/test_productos_v2.py -k test_create_producto_integration
# Resultado: PASS (mejor código, maneja duplicados)
```

## Entregables de Diseño

### Entregables Técnicos

- tests/structure completa (unit/, integration/, factories/)
- conftest.py con fixtures globales
- factories.py con factories BC3-Suite
- ≈250 tests de comportamiento real
- pytest.ini configurado

### Entregables de Documentación

- Documentación de fixtures (docstrings)
- Documentación de factories (ejemplos)
- Guía de TDD para el proyecto
- README de tests (cómo ejecutar, interpretar resultados)

### Entregables de Métricas

- Coverage report (htmlcov/)
- Test report (xml, json)
- Métricas de calidad por módulo

## Siguientes Pasos

1. **Tasks**: Crear tareas de implementación específicas
2. **Apply**: Implementar con TDD real (RED→GREEN→REFACTOR)
3. **Verify**: Validar ≥80% coverage y ≈250 tests
4. **Archive**: Cerrar Fase 2 y pasar a Fase 3
