# Tareas: Fase 2 - Testing Suite con TDD Real

## Resumen Ejecutivo

Tareas específicas de implementación para Testing Suite con TDD Real en API-DISANO, organizadas por módulo y prioridad, siguiendo patrones BC3-Suite (RED→GREEN→REFACTOR, AAA pattern, factories).

## Tareas por Módulo

### Módulo: app/config.py (72% → 100%)

**Objetivo:** 100% coverage
**Tests actuales:** 0
**Tests necesarios:** 5 tests de comportamiento
**Prioridad:** P1 (Alta)

#### Tarea: test_config_settings_001 - Settings secret_key required

- **Descripción:** Test que verifica Settings falla sin SECRET_KEY válido
- **Tipo:** Unit test
- **Pattern:** TDD (RED→GREEN→REFACTOR)
- **Estado:** Pending
- **Archivos:** tests/unit/test_config.py

```python
# TDD Cycle
# 1. RED: Escribir test que falla
def test_settings_secret_key_required():
    with pytest.raises(ValueError):
        Settings(secret_key="")

# 2. GREEN: Implementar field_validator en Settings
# 3. REFACTOR: Mejorar mensajes de error
```

**Criterio de aceptación:** Test pasa, coverage incrementado, behavior documentado

#### Tarea: test_config_settings_002 - Settings api_keys required

- **Descripción:** Test que verifica Settings falla sin API_KEYS válidos
- **Tipo:** Unit test
- **Pattern:** TDD (RED→GREEN→REFACTOR)
- **Estado:** Pending
- **Archivos:** tests/unit/test_config.py

```python
def test_settings_api_keys_required():
    with pytest.raises(ValueError):
        Settings(api_keys=[])
```

#### Tarea: test_config_settings_003 - Settings valid configuration

- **Descripción:** Test que verifica Settings válidos funcionan
- **Tipo:** Unit test
- **Pattern:** TDD (RED→GREEN→REFACTOR)
- **Estado:** Pending
- **Archivos:** tests/unit/test_config.py

```python
def test_settings_valid_configuration():
    settings = Settings(secret_key="test", api_keys=["key1"])
    assert settings.secret_key == "test"
```

#### Tarea: test_config_settings_004 - Settings redis_url has default

- **Descripción:** Test que verifica Redis URL tiene default razonable
- **Tipo:** Unit test
- **Pattern:** TDD (RED→GREEN→REFACTOR)
- **Estado:** Pending
- **Archivos:** tests/unit/test_config.py

```python
def test_settings_redis_url_has_default():
    settings = Settings(secret_key="test", api_keys=["key"])
    assert "redis://" in settings.redis_url
```

#### Tarea: test_config_settings_005 - Settings admin_api_keys field validator

- **Descripción:** Test que verifica admin_api_keys field validator funciona
- **Tipo:** Unit test
- **Pattern:** TDD (RED→GREEN→REFACTOR)
- **Estado:** Pending
- **Archivos:** tests/unit/test_config.py

```python
def test_settings_admin_api_keys_field_validator():
    settings = Settings(secret_key="test", api_keys=["key1", "key2"])
    assert len(settings.admin_api_keys) > 0
```

---

### Módulo: app/middleware.py (37% → 80%)

**Objetivo:** 80% coverage
**Tests actuales:** 19 tests (37% coverage)
**Tests necesarios:** 30 tests adicionales de comportamiento
**Prioridad:** P1 (Alta)

#### Tarea: test_middleware_rate_limit_001 - Blocks rate limit exceeded

- **Descripción:** Test que verifica middleware bloquea después de rate limit
- **Tipo:** Unit test
- **Pattern:** TDD (RED→GREEN→REFACTOR)
- **Estado:** Pending
- **Archivos:** tests/unit/test_middleware.py

```python
async def test_middleware_blocks_rate_limit_exceeded():
    # RED: Middleware debe bloquear después del límite
    middleware = SecurityMiddleware(app)
    request = RequestFactory(ip="127.0.0.1", endpoint="/api/v2/productos")

    responses = []
    for _ in range(100):
        response = await middleware(request)
        responses.append(response)

    assert any(r.status_code == 429 for r in responses)
```

#### Tarea: test_middleware_cors_001 - CORS headers present

- **Descripción:** Test que verifica CORS headers están presentes
- **Tipo:** Unit test
- **Pattern:** TDD (RED→GREEN→REFACTOR)
- **Estado:** Pending
- **Archivos:** tests/unit/test_middleware.py

```python
async def test_middleware_cors_headers_present():
    # GREEN: CORS headers están presentes
    middleware = SecurityMiddleware(app)
    request = RequestFactory(origin="http://localhost:3000")
    response = await middleware(request)

    assert response.headers.get("Access-Control-Allow-Origin") == "*"
```

#### Tarea: test_middleware_scraping_001 - Scraping detection blocks

- **Descripción:** Test que verifica middleware bloquea scrapers
- **Tipo:** Unit test
- **Pattern:** TDD (RED→GREEN→REFACTOR)
- **Estado:** Pending
- **Archivos:** tests/unit/test_middleware.py

```python
async def test_middleware_scraping_detection_blocks():
    # GREEN: Bloquea requests de scrapers
    middleware = SecurityMiddleware(app)
    request = RequestFactory(
        user_agent="Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    )
    response = await middleware(request)

    assert response.status_code == 403
```

#### Tarea: test_middleware_valid_001 - Valid request passes

- **Descripción:** Test que verifica requests válidos pasan
- **Tipo:** Unit test
- **Pattern:** TDD (RED→GREEN→REFACTOR)
- **Estado:** Pending
- **Archivos:** tests/unit/test_middleware.py

```python
async def test_middleware_valid_request_passes():
    # GREEN: Requests válidos pasan
    middleware = SecurityMiddleware(app)
    request = RequestFactory(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        ip="192.168.1.100"
    )
    response = await middleware(request)

    assert response.status_code not in [403, 429]
```

*(26 additional middleware tasks omitted for brevity)*

---

### Módulo: app/security.py (0% → 70%)

**Objetivo:** 70% coverage
**Tests actuales:** 0 tests
**Tests necesarios:** 20 tests de comportamiento
**Prioridad:** P1 (Alta)

#### Tarea: test_security_api_key_001 - Verify admin API key valid

- **Descripción:** Test que verifica API key válido pasa
- **Tipo:** Unit test
- **Pattern:** TDD (RED→GREEN→REFACTOR)
- **Estado:** Pending
- **Archivos:** tests/unit/test_security.py

```python
def test_verify_admin_api_key_valid():
    # RED: API key válido debe pasar
    request = RequestFactory(headers={"X-API-Key": "admin-test-key"})
    result = verify_admin_api_key(request)
    assert result is True
```

#### Tarea: test_security_api_key_002 - Verify admin API key invalid

- **Descripción:** Test que verifica API key inválido falla
- **Tipo:** Unit test
- **Pattern:** TDD (RED→GREEN→REFACTOR)
- **Estado:** Pending
- **Archivos:** tests/unit/test_security.py

```python
def test_verify_admin_api_key_invalid():
    # RED: API key inválido debe fallar
    request = RequestFactory(headers={"X-API-Key": "invalid-key"})

    with pytest.raises(HTTPException) as exc_info:
        verify_admin_api_key(request)

    assert exc_info.value.status_code == 401
```

#### Tarea: test_security_api_key_003 - Verify admin API key missing

- **Descripción:** Test que verifica API key faltante falla
- **Tipo:** Unit test
- **Pattern:** TDD (RED→GREEN→REFACTOR)
- **Estado:** Pending
- **Archivos:** tests/unit/test_security.py

```python
def test_verify_admin_api_key_missing():
    # RED: API key faltante debe fallar
    request = RequestFactory(headers={})

    with pytest.raises(HTTPException) as exc_info:
        verify_admin_api_key(request)

    assert exc_info.value.status_code == 401
```

#### Tarea: test_security_otp_001 - OTP generation format valid

- **Descripción:** Test que verifica OTP tiene formato válido
- **Tipo:** Unit test
- **Pattern:** TDD (RED→GREEN→REFACTOR)
- **Estado:** Pending
- **Archivos:** tests/unit/test_otp_service.py

```python
def test_otp_generation_format_valid():
    # GREEN: OTP tiene formato válido
    otp = generate_otp("user@test.com")
    assert len(otp.code) == 6
    assert otp.code.isdigit()
```

#### Tarea: test_security_otp_002 - OTP expiration 10 minutes

- **Descripción:** Test que verifica OTP expira en 10 minutos
- **Tipo:** Unit test
- **Pattern:** TDD (RED→GREEN→REFACTOR)
- **Estado:** Pending
- **Archivos:** tests/unit/test_otp_service.py

```python
def test_otp_expiration_10_minutes():
    # GREEN: OTP expira en 10 minutos
    otp = generate_otp("user@test.com")
    from datetime import datetime, timedelta
    expired_at = otp.created_at + timedelta(minutes=10)
    assert expired_at > datetime.now()
```

*(15 additional security tasks omitted for brevity)*

---

### Módulo: app/routers/productos.py (0% → 60%)

**Objetivo:** 60% coverage
**Tests actuales:** 0 tests
**Tests necesarios:** 40 tests de comportamiento (V1 + V2)
**Prioridad:** P1 (Alta)

#### Tarea: test_productos_v1_001 - Get productos returns data from testing.db

- **Descripción:** Test que verifica get_productos V1 retorna datos de testing.db
- **Tipo:** Integration test
- **Pattern:** TDD (RED→GREEN→REFACTOR)
- **Estado:** Pending
- **Archivos:** tests/integration/test_productos_v1.py

```python
def test_get_productos_returns_data_from_testing_db():
    # RED: get_productos V1 retorna datos de testing.db
    client = TestClient(app)
    db_session.add(ProductoFactory(
        codigo="PROD-0001",
        descripcion="Producto de prueba"
    ))
    db_session.commit()

    response = client.get("/api/productos?skip=0&limit=10")

    assert response.status_code == 200
    assert len(response.json()) <= 10
    assert any(p["codigo"] == "PROD-0001" for p in response.json())
```

#### Tarea: test_productos_v1_002 - Get producto by codigo exists

- **Descripción:** Test que verifica get_producto V1 retorna producto por código
- **Tipo:** Integration test
- **Pattern:** TDD (RED→GREEN→REFACTOR)
- **Estado:** Pending
- **Archivos:** tests/integration/test_productos_v1.py

```python
def test_get_producto_by_codigo_exists():
    # GREEN: get_producto V1 retorna producto por código
    client = TestClient(app)
    db_session.add(ProductoFactory(
        codigo="PROD-TEST",
        descripcion="Test producto"
    ))
    db_session.commit()

    response = client.get("/api/productos/PROD-TEST")

    assert response.status_code == 200
    assert response.json()["codigo"] == "PROD-TEST"
```

#### Tarea: test_productos_v1_003 - Get producto by codigo not exists

- **Descripción:** Test que verifica get_producto V1 retorna 404 si no existe
- **Tipo:** Integration test
- **Pattern:** TDD (RED→GREEN→REFACTOR)
- **Estado:** Pending
- **Archivos:** tests/integration/test_productos_v1.py

```python
def test_get_producto_by_codigo_not_exists():
    # GREEN: get_producto V1 retorna 404 si no existe
    client = TestClient(app)
    response = client.get("/api/productos/NOEXISTE")
    assert response.status_code == 404
```

#### Tarea: test_productos_v2_001 - Create producto valid

- **Descripción:** Test que verifica create_producto V2 crea producto en testing.db
- **Tipo:** Integration test
- **Pattern:** TDD (RED→GREEN→REFACTOR)
- **Estado:** Pending
- **Archivos:** tests/integration/test_productos_v2.py

```python
def test_create_producto_valid():
    # RED: create_producto V2 crea producto en testing.db
    client = TestClient(app)
    producto_data = {
        "codigo": "PROD-NEW",
        "descripcion": "Nuevo producto",
        "pvp": 100.00,
        "marca": "Test"
    }

    response = client.post(
        "/api/v2/productos",
        json=producto_data,
        headers=admin_headers
    )

    assert response.status_code == 201
    assert response.json()["codigo"] == "PROD-NEW"
```

#### Tarea: test_productos_v2_002 - Create producto duplicate codigo

- **Descripción:** Test que verifica create_producto V2 rechaza código duplicado
- **Tipo:** Integration test
- **Pattern:** TDD (RED→GREEN→REFACTOR)
- **Estado:** Pending
- **Archivos:** tests/integration/test_productos_v2.py

```python
def test_create_producto_duplicate_codigo():
    # RED: create_producto V2 rechaza código duplicado
    client = TestClient(app)
    db_session.add(ProductoFactory(codigo="PROD-DUP"))
    db_session.commit()

    producto_data = {
        "codigo": "PROD-DUP",
        "descripcion": "Duplicado",
        "pvp": 100.00
    }

    response = client.post(
        "/api/v2/productos",
        json=producto_data,
        headers=admin_headers
    )

    assert response.status_code == 400
```

#### Tarea: test_productos_v2_003 - Update producto valid

- **Descripción:** Test que verifica update_producto V2 actualiza producto
- **Tipo:** Integration test
- **Pattern:** TDD (RED→GREEN→REFACTOR)
- **Estado:** Pending
- **Archivos:** tests/integration/test_productos_v2.py

```python
def test_update_producto_valid():
    # GREEN: update_producto V2 actualiza producto
    client = TestClient(app)
    db_session.add(ProductoFactory(
        codigo="PROD-UPDATE",
        descripcion="Original"
    ))
    db_session.commit()

    response = client.put(
        "/api/v2/productos/PROD-UPDATE",
        json={"descripcion": "Actualizado"},
        headers=admin_headers
    )

    assert response.status_code == 200
    assert response.json()["descripcion"] == "Actualizado"
```

#### Tarea: test_productos_v2_004 - Delete producto valid

- **Descripción:** Test que verifica delete_producto V2 elimina producto
- **Tipo:** Integration test
- **Pattern:** TDD (RED→GREEN→REFACTOR)
- **Estado:** Pending
- **Archivos:** tests/integration/test_productos_v2.py

```python
def test_delete_producto_valid():
    # GREEN: delete_producto V2 elimina producto
    client = TestClient(app)
    db_session.add(ProductoFactory(
        codigo="PROD-DELETE",
        descripcion="A eliminar"
    ))
    db_session.commit()

    response = client.delete(
        "/api/v2/productos/PROD-DELETE",
        headers=admin_headers
    )

    assert response.status_code == 204

    # Assert - Verificar que fue eliminado
    response = client.get("/api/v2/productos/PROD-DELETE")
    assert response.status_code == 404
```

*(34 additional productos tasks omitted for brevity)*

---

### Módulo: app/main.py (0% → 50%)

**Objetivo:** 50% coverage
**Tests actuales:** 0 tests
**Tests necesarios:** 10 tests de comportamiento
**Prioridad:** P2 (Media)

#### Tarea: test_main_startup_001 - App startup initializes logging

- **Descripción:** Test que verifica app startup inicializa logging
- **Tipo:** Unit test
- **Pattern:** TDD (RED→GREEN→REFACTOR)
- **Estado:** Pending
- **Archivos:** tests/unit/test_main.py

```python
def test_main_app_startup_initializes_logging():
    # RED: App startup inicializa logging
    from app.main import app
    assert hasattr(app, "startup_handler")
```

#### Tarea: test_main_root_001 - Root endpoint returns 200

- **Descripción:** Test que verifica root endpoint retorna 200
- **Tipo:** Integration test
- **Pattern:** TDD (RED→GREEN→REFACTOR)
- **Estado:** Pending
- **Archivos:** tests/integration/test_main.py

```python
def test_main_root_endpoint_returns_200():
    # GREEN: Root endpoint retorna 200
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
```

*(8 additional main tasks omitted for brevity)*

---

### Módulo: Auth IDOR Tests (Security Critical)

**Objetivo:** 100% coverage de auth logic
**Tests actuales:** 0 tests
**Tests necesarios:** 10 tests de seguridad
**Prioridad:** P0 (Crítica - security)

#### Tarea: test_auth_idor_001 - User cannot access admin endpoints

- **Descripción:** Test que verifica usuario NO puede acceder a admin endpoints
- **Tipo:** Integration test
- **Pattern:** TDD (RED→GREEN→REFACTOR)
- **Estado:** Pending
- **Archivos:** tests/integration/test_auth_idor.py

```python
def test_user_cannot_access_admin_endpoints():
    # RED: Usuario no puede acceder a admin endpoints
    client = TestClient(app)

    response = client.post(
        "/api/v2/productos",
        json={"codigo": "PROD-NEW", "descripcion": "Test"},
        headers=user_headers  # NO admin_headers
    )

    assert response.status_code == 403
```

#### Tarea: test_auth_idor_002 - Admin can access admin endpoints

- **Descripción:** Test que verifica admin puede acceder a admin endpoints
- **Tipo:** Integration test
- **Pattern:** TDD (RED→GREEN→REFACTOR)
- **Estado:** Pending
- **Archivos:** tests/integration/test_auth_idor.py

```python
def test_admin_can_access_admin_endpoints():
    # GREEN: Admin puede acceder a admin endpoints
    client = TestClient(app)

    response = client.post(
        "/api/v2/productos",
        json={"codigo": "PROD-NEW", "descripcion": "Test"},
        headers=admin_headers  # admin_headers
    )

    assert response.status_code in [201, 400]  # 201 si OK, 400 si duplicado
```

*(8 additional auth IDOR tasks omitted for brevity)*

---

## Tareas de Infraestructura

### Tarea: infrastructure_pytest_001 - Create pytest.ini

- **Descripción:** Crear pytest.ini con configuración completa
- **Tipo:** Infraestructura
- **Pattern:** N/A
- **Estado:** Pending
- **Archivos:** pytest.ini

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

### Tarea: infrastructure_fixtures_001 - Update conftest.py with fixtures

- **Descripción:** Actualizar conftest.py con fixtures globales (db_session, client, admin_headers, etc.)
- **Tipo:** Infraestructura
- **Pattern:** N/A
- **Estado:** Pending
- **Archivos:** tests/conftest.py

### Tarea: infrastructure_factories_001 - Create factories.py

- **Descripción:** Crear factories.py con factories BC3-Suite (ProductoFactory, OTPFactory, UserFactory, RequestFactory)
- **Tipo:** Infraestructura
- **Pattern:** N/A
- **Estado:** Pending
- **Archivos:** tests/factories/factories.py

### Tarea: infrastructure_wrapper_001 - Update run_pytest.py

- **Descripción:** Actualizar scripts/run_pytest.py con configuración pydantic-settings arreglada
- **Tipo:** Infraestructura
- **Pattern:** N/A
- **Estado:** Pending
- **Archivos:** scripts/run_pytest.py

---

## Resumen de Tareas

### Tareas por Prioridad

| Prioridad | Cantidad | Módulos |
|-----------|----------|---------|
| P0 (Crítica - Security) | 10 | Auth IDOR |
| P1 (Alta) | 125 | config, middleware, security, productos |
| P2 (Media) | 10 | main |
| P3 (Baja - Infraestructura) | 4 | pytest, fixtures, factories, wrapper |
| **TOTAL** | **≈250** | |

### Tareas por Tipo

| Tipo | Cantidad | |
|------|----------|---|
| Unit tests | 90 | Internal logic |
| Integration tests | 150 | External dependencies |
| Infraestructura | 4 | Setup |
| **TOTAL** | **≈250** | |

### Criterios de Éxito

- [ ] ≥80% coverage (medido con pytest-cov)
- [ ] ≈250 tests automatizados
- [ ] 100% tests de comportamiento real (no tests de estructura)
- [ ] TDD Cycle aplicado (RED→GREEN→REFACTOR)
- [ ] Factories BC3-Suite implementadas
- [ ] testing/testing.db usado para tests (NO producción)
- [ ] Todos los tests pasan (pytest)

## Siguientes Pasos

1. **Implementar tareas P0 (Auth IDOR)** - Security critical, 10 tests
2. **Implementar tareas P1 (config, middleware, security, productos)** - 125 tests
3. **Implementar tareas P2 (main)** - 10 tests
4. **Implementar tareas P3 (infraestructura)** - 4 tasks
5. **Ejecutar pytest --cov=app** y validar ≥80% coverage
6. **Documentar métricas y resultados**
7. **Archivar Fase 2 y pasar a Fase 3**
