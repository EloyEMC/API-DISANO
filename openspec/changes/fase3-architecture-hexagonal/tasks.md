# Fase 3 - Architecture Hexagonal Migration: Tasks

## Implementation Tasks

**Change ID:** fase3-architecture-hexagonal  
**Phase:** Fase 3.4 + 3.5 (DI Setup + Testing Migration)  
**Version:** 1.0  
**TDD Methodology:** RED → GREEN → REFACTOR

---

## Phase 3.4: Dependency Injection Setup

### TASK-3.4.1: DI Configuration in main.py

**Description:** Configure FastAPI application with dependency injection for database sessions, repositories, and services.

**Acceptance Criteria:**

- [ ] main.py imports hexagonal router instead of legacy router
- [ ] Application starts successfully (< 2s)
- [ ] No dependency injection errors in logs
- [ ] V1 endpoints still accessible (backward compatibility)
- [ ] V2 endpoints accessible through new router

**TDD Approach:**

**Step 1: RED - Write failing test**

```python
# tests/unit/test_main_di_setup.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_application_starts_with_di():
    """Test that application starts with DI configuration"""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code in [200, 404]  # App started
```

**Step 2: GREEN - Implement DI configuration**

```python
# app/main.py
from fastapi import FastAPI
from app.interfaces.http import productos  # NEW
from app.routers import familias, bc3      # Legacy

app = FastAPI()

# Hexagonal architecture router
app.include_router(productos.router, prefix="/api/productos", tags=["productos"])

# Legacy routers (to migrate later)
app.include_router(familias.router, prefix="/api/familias", tags=["familias"])
app.include_router(bc3.router, prefix="/api/bc3", tags=["bc3"])
```

**Step 3: REFACTOR - Optimize**

- Add docstrings
- Organize imports
- Add startup event handler

**Test Fixtures Needed:**

- TestClient (FastAPI)

**Dependencies:** None (can start immediately)

**Estimated Time:** 30 minutes

**Verification Command:**

```bash
pytest tests/unit/test_main_di_setup.py -v
python app/main.py  # Should start without errors
```

---

### TASK-3.4.2: HTTP Interface Layer Created

**Description:** Create `app/interfaces/http/productos.py` with hexagonal architecture pattern using DI.

**Acceptance Criteria:**

- [ ] File exists at app/interfaces/http/productos.py
- [ ] Contains DI functions (get_producto_service, etc.)
- [ ] Contains V2 endpoints (4 endpoints) with service dependencies
- [ ] Contains V1 endpoints (2 endpoints) for backward compatibility
- [ ] No sqlite3 imports in HTTP layer
- [ ] Only repository interface imports (no concrete repository)

**TDD Approach:**

**Step 1: RED - Write failing tests**

```python
# tests/unit/interfaces/test_http_productos.py
import pytest
from unittest.mock import Mock, patch
from app.interfaces.http.productos import (
    get_producto_service,
    get_producto_repository,
    get_db_session,
)
from app.domain.repositories.producto import ProductoRepositoryInterface

def test_get_producto_service_creates_service():
    """Test that DI function creates ProductoService"""
    with patch('app.interfaces.http.productos.get_producto_repository') as mock_get_repo:
        mock_repo = Mock(spec=ProductoRepositoryInterface)
        mock_get_repo.return_value = mock_repo
        
        service = get_producto_service()
        
        assert service.repository == mock_repo
        mock_get_repo.assert_called_once()

def test_get_producto_repository_creates_repository():
    """Test that DI function creates SQLAlchemy repository"""
    with patch('app.interfaces.http.productos.get_db_session') as mock_get_session:
        mock_session = Mock()
        mock_get_session.return_value = mock_session
        
        from app.infrastructure.repositories.producto import SQLAlchemyProductoRepository
        repo = get_producto_repository()
        
        assert isinstance(repo, SQLAlchemyProductoRepository)
        mock_get_session.assert_called_once()

def test_http_layer_no_sqlite3_imports():
    """Test that HTTP layer does not import sqlite3"""
    import app.interfaces.http.productos as productos_module
    import inspect
    
    source = inspect.getsource(productos_module)
    assert 'sqlite3' not in source.lower()
```

**Step 2: GREEN - Implement HTTP layer**

```python
# app/interfaces/http/productos.py
from fastapi import APIRouter, Depends, HTTPException, Query
from app.domain.services.producto import ProductoService
from app.domain.repositories.producto import ProductoRepositoryInterface
from app.application.dto.producto import (
    ProductoSearchDTO,
    ProductoResponseDTO,
)
from app.infrastructure.database.connection import SessionLocal
from app.infrastructure.repositories.producto import SQLAlchemyProductoRepository

router = APIRouter()

# DI Functions
def get_producto_service() -> ProductoService:
    return ProductoService(SQLAlchemyProductoRepository(SessionLocal()))

# V2 Endpoints
@router.get("/v2/list", response_model=list[ProductoResponseDTO])
async def buscar_productos_v2(
    buscar: str = Query(..., min_length=1, description="Search term"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
    marca: str = Query("", max_length=50, description="Filter by brand"),
    familia: str = Query("", max_length=50, description="Filter by family"),
    service: ProductoService = Depends(get_producto_service),
):
    try:
        dto = ProductoSearchDTO(buscar=buscar, limit=limit, marca=marca, familia=familia)
        entities = service.buscar_productos(dto)
        return [ProductoResponseDTO.from_entity(e) for e in entities]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# V1 Endpoints (backward compatible)
@router.get("/")
async def get_productos_v1(
    buscar: str = Query(None, description="Search term"),
    limit: int = Query(10, ge=1, le=500, description="Max results"),
):
    try:
        dto = ProductoSearchDTO(buscar=buscar or "", limit=limit, marca="", familia="")
        entities = service.buscar_productos(dto)
        return [e.model_dump() for e in entities]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
```

**Step 3: REFACTOR - Optimize**

- Extract common error handling into decorator
- Add comprehensive docstrings
- Optimize DI function (use context manager for session)

**Test Fixtures Needed:**

- Mock repository
- Mock service

**Dependencies:** None (can start immediately)

**Estimated Time:** 2 hours

**Verification Command:**

```bash
pytest tests/unit/interfaces/test_http_productos.py -v
python -c "from app.interfaces.http.productos import router; print('Router created successfully')"
```

---

### TASK-3.4.3: V2 Endpoints Migrated

**Description:** Migrate V2 endpoints to use Product Services with DTOs (4 endpoints).

**Acceptance Criteria:**

- [ ] GET /api/productos/v2/list returns ProductoResponseDTO[]
- [ ] GET /api/productos/v2/{codigo} returns ProductoResponseDTO
- [ ] GET /api/productos/v2/marca/{marca} returns ProductoResponseDTO[]
- [ ] GET /api/productos/v2/familia/{familia} returns ProductoResponseDTO[]
- [ ] All V2 endpoints use ProductoService (no direct DB access)
- [ ] Pydantic validation errors for invalid input (400 Bad Request)
- [ ] Response time degradation < 100ms

**TDD Approach:**

**Step 1: RED - Write failing tests**

```python
# tests/integration/test_v2_endpoints.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_v2_list_endpoint_success():
    """Test V2 list endpoint returns products"""
    response = client.get("/api/productos/v2/list?buscar=test&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5
    assert all("codigo" in item for item in data)
    assert all("descripcion" in item for item in data)

def test_v2_list_endpoint_validation_error():
    """Test V2 list endpoint validates input"""
    response = client.get("/api/productos/v2/list?limit=0")  # Invalid: limit < 1
    assert response.status_code == 422  # Pydantic validation error

def test_v2_detail_endpoint_success():
    """Test V2 detail endpoint returns product"""
    response = client.get("/api/productos/v2/TEST001")
    assert response.status_code == 200
    data = response.json()
    assert data["codigo"] == "TEST001"
    assert "descripcion" in data

def test_v2_detail_endpoint_not_found():
    """Test V2 detail endpoint returns 404 for non-existent product"""
    response = client.get("/api/productos/v2/NONEXISTENT")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_v2_marca_endpoint_success():
    """Test V2 marca endpoint returns products by brand"""
    response = client.get("/api/productos/v2/marca/TestBrand?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5

def test_v2_familia_endpoint_success():
    """Test V2 familia endpoint returns products by family"""
    response = client.get("/api/productos/v2/familia/Electrónica?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5
```

**Step 2: GREEN - Implement V2 endpoints** (Already done in TASK-3.4.2)

**Step 3: REFACTOR - Optimize**

- Add query parameter documentation
- Add response examples
- Optimize DTO validation (add custom validators if needed)

**Test Fixtures Needed:**

- TestClient (FastAPI)
- Test database with productos_clean view

**Dependencies:** TASK-3.4.2 (HTTP layer created)

**Estimated Time:** 2 hours

**Verification Command:**

```bash
pytest tests/integration/test_v2_endpoints.py -v
pytest tests/integration/test_v2_endpoints.py::test_v2_list_endpoint_success --benchmark-only
```

---

### TASK-3.4.4: V1 Endpoints Backward Compatibility

**Description:** Maintain V1 endpoints for backward compatibility while using hexagonal architecture internally.

**Acceptance Criteria:**

- [ ] GET /api/productos/ returns legacy format (dict[], not ProductoResponseDTO[])
- [ ] GET /api/productos/{codigo} returns legacy format (dict, not ProductoResponseDTO)
- [ ] BC3 Suite App continues working with V1 endpoints
- [ ] No breaking changes for existing clients
- [ ] HTTP 200 OK for valid requests
- [ ] HTTP 404 for non-existent products

**TDD Approach:**

**Step 1: RED - Write failing tests**

```python
# tests/integration/test_v1_backward_compatibility.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_v1_list_endpoint_legacy_format():
    """Test V1 list endpoint returns legacy format"""
    response = client.get("/api/productos/?buscar=test&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Legacy format: dict with raw keys, not ProductoResponseDTO
    assert all(isinstance(item, dict) for item in data)
    # Should match old router format
    assert all("codigo" in item for item in data)
    assert all("descripcion" in item for item in data)

def test_v1_detail_endpoint_legacy_format():
    """Test V1 detail endpoint returns legacy format"""
    response = client.get("/api/productos/TEST001")
    assert response.status_code == 200
    data = response.json()
    # Legacy format: dict with raw keys, not ProductoResponseDTO
    assert isinstance(data, dict)
    assert "codigo" in data
    assert "descripcion" in data

def test_v1_bc3_suite_compatibility():
    """Test BC3 Suite App continues working with V1 endpoints"""
    # Simulate BC3 Suite App request
    response = client.get("/api/productos/?limit=100")
    assert response.status_code == 200
    data = response.json()
    # BC3 Suite expects list format
    assert isinstance(data, list)
    assert len(data) <= 100
```

**Step 2: GREEN - Implement V1 endpoints** (Already done in TASK-3.4.2)

**Step 3: REFACTOR - Optimize**

- Add deprecation notice in docs
- Document migration path to V2

**Test Fixtures Needed:**

- TestClient (FastAPI)
- Test database with productos_clean view

**Dependencies:** TASK-3.4.2 (HTTP layer created)

**Estimated Time:** 1 hour

**Verification Command:**

```bash
pytest tests/integration/test_v1_backward_compatibility.py -v
# Manual test with BC3 Suite App
```

---

### TASK-3.4.5: BC3 Suite Compatibility

**Description:** Ensure BC3 Suite integration works with hexagonal architecture.

**Acceptance Criteria:**

- [ ] BC3 fields present in V2 responses (bc3_descripcion_corta, bc3_product_type, bc3_descripcion_completa)
- [ ] BC3 fields present in V1 responses (legacy format preserved)
- [ ] 8,288 products accessible through V2 endpoints
- [ ] 8,288 products accessible through V1 endpoints
- [ ] BC3 Suite tests passing (all integration tests)
- [ ] Performance benchmarks met (response time < 500ms)

**TDD Approach:**

**Step 1: RED - Write failing tests**

```python
# tests/integration/test_bc3_compatibility.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_bc3_fields_present_in_v2_response():
    """Test BC3 fields present in V2 responses"""
    response = client.get("/api/productos/v2/list?limit=1")
    assert response.status_code == 200
    data = response.json()
    if len(data) > 0:
        product = data[0]
        # BC3 fields should be present
        assert "bc3_descripcion_corta" in product
        assert "bc3_product_type" in product
        assert "bc3_descripcion_completa" in product

def test_bc3_fields_present_in_v1_response():
    """Test BC3 fields present in V1 responses (legacy format)"""
    response = client.get("/api/productos/?limit=1")
    assert response.status_code == 200
    data = response.json()
    if len(data) > 0:
        product = data[0]
        # BC3 fields should be present in legacy format
        assert "bc3_descripcion_corta" in product
        assert "bc3_product_type" in product
        assert "bc3_descripcion_completa" in product

def test_all_products_accessible():
    """Test that all 8,288 products are accessible"""
    response = client.get("/api/productos/v2/list?limit=10000")
    assert response.status_code == 200
    data = response.json()
    # Should have all products (or as many as limit allows)
    assert len(data) >= 1  # At least some products

def test_bc3_performance_benchmark():
    """Test BC3 endpoints meet performance benchmarks"""
    import time
    start = time.time()
    response = client.get("/api/productos/v2/list?buscar=test&limit=10")
    elapsed = time.time() - start
    assert response.status_code == 200
    assert elapsed < 0.5  # < 500ms
```

**Step 2: GREEN - Ensure BC3 compatibility** (Already implemented in DTOs and entities)

**Step 3: REFACTOR - Optimize**

- Add BC3 field validation
- Add BC3-specific tests

**Test Fixtures Needed:**

- TestClient (FastAPI)
- Test database with productos_clean view (8,288 records)

**Dependencies:** TASK-3.4.2 (HTTP layer created), TASK-3.4.3 (V2 endpoints), TASK-3.4.4 (V1 endpoints)

**Estimated Time:** 1 hour

**Verification Command:**

```bash
pytest tests/integration/test_bc3_compatibility.py -v
# Manual test with BC3 Suite App
```

---

## Phase 3.5: Testing Migration

### TASK-3.5.1: Service Tests Fixing

**Description:** Fix 14/14 failing service tests to pass with proper imports and mocks.

**Acceptance Criteria:**

- [ ] All 14 service tests in tests/unit/domain/test_producto_service.py pass
- [ ] ProductoRepositoryInterface properly imported
- [ ] Test entities include all required fields (created_at, updated_at)
- [ ] Mock repositories configured correctly
- [ ] TDD cycle followed (RED → GREEN → REFACTOR)
- [ ] Coverage report shows service methods covered

**TDD Approach:**

**Step 1: RED - Verify tests are failing**

```bash
pytest tests/unit/domain/test_producto_service.py -v  # Should show 14 failures
```

**Step 2: GREEN - Fix imports and test entities**

```python
# tests/unit/domain/test_producto_service.py
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from app.domain.entities.producto import ProductoEntity
from app.domain.exceptions.not_found import (
    ProductoNotFoundException,
    ProductoYaExisteException,
    ValidationException,
)
from app.domain.repositories.producto import ProductoRepositoryInterface
from app.domain.services.producto import ProductoService

class TestProductoService:
    """Tests for ProductoService business logic"""

    def test_crear_producto_success(self):
        """Test creating product successfully"""
        # Arrange
        mock_repo = Mock(spec=ProductoRepositoryInterface)
        mock_repo.get_by_codigo.side_effect = ProductoNotFoundException("TEST001")
        mock_repo.save.return_value = ProductoEntity(
            codigo="TEST001",
            descripcion="Test Product",
            marca="TestBrand",
            pvp=99.99,
            bc3_descripcion_corta="Short",
            bc3_product_type="TYPE_01",
            bc3_descripcion_completa="Full description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        service = ProductoService(mock_repo)
        from app.application.dto.producto import ProductoCreateDTO
        dto = ProductoCreateDTO(
            codigo="TEST001",
            descripcion="Test Product",
            marca="TestBrand",
            pvp=99.99,
            bc3_descripcion_corta="Short",
            bc3_product_type="TYPE_01",
            bc3_descripcion_completa="Full description",
        )

        # Act
        result = service.crear_producto(dto)

        # Assert
        assert result.codigo == "TEST001"
        assert result.descripcion == "Test Product"
        mock_repo.save.assert_called_once()

    # ... (13 more tests with proper imports and entities)
```

**Step 3: REFACTOR - Optimize**

- Extract common test fixtures
- Add parametrized tests
- Improve test documentation

**Test Fixtures Needed:**

- Mock repository (Mock(spec=ProductoRepositoryInterface))
- Mock service

**Dependencies:** None (can start immediately)

**Estimated Time:** 1 hour

**Verification Command:**

```bash
pytest tests/unit/domain/test_producto_service.py -v  # Should show 14/14 passed
pytest tests/unit/domain/test_producto_service.py --cov=app/domain/services/producto --cov-report=term-missing
```

---

### TASK-3.5.2: Coverage Maintenance

**Description:** Maintain or improve code coverage baseline during migration (>= 39%).

**Acceptance Criteria:**

- [ ] Overall coverage >= 39% (maintain baseline)
- [ ] Domain layer coverage >= 90% (TDD target)
- [ ] Infrastructure layer coverage >= 80%
- [ ] Application/HTTP layer coverage >= 70%
- [ ] New code (HTTP layer) coverage >= 80%
- [ ] Critical paths (service, repository) coverage >= 90%
- [ ] pytest-cov report shows no uncovered critical paths
- [ ] Coverage diff shows improvement, not regression

**TDD Approach:**

**Step 1: RED - Measure current coverage**

```bash
pytest --cov=app --cov-report=term-missing --cov-report=html
# Note current coverage baseline
```

**Step 2: GREEN - Add tests for uncovered code**

```python
# tests/unit/interfaces/test_http_dto_validation.py
import pytest
from app.application.dto.producto import ProductoSearchDTO

def test_producto_search_dto_validation():
    """Test ProductoSearchDTO validation"""
    # Valid
    dto = ProductoSearchDTO(buscar="test", limit=10, marca="", familia="")
    assert dto.buscar == "test"
    assert dto.limit == 10
    
    # Invalid: limit < 1
    with pytest.raises(ValueError):
        ProductoSearchDTO(buscar="test", limit=0, marca="", familia="")
    
    # Invalid: limit > 100
    with pytest.raises(ValueError):
        ProductoSearchDTO(buscar="test", limit=101, marca="", familia="")

def test_producto_response_dto_from_entity():
    """Test ProductoResponseDTO from_entity conversion"""
    from app.domain.entities.producto import ProductoEntity
    from app.application.dto.producto import ProductoResponseDTO
    from datetime import datetime
    
    entity = ProductoEntity(
        codigo="TEST001",
        descripcion="Test Product",
        marca="TestBrand",
        pvp=99.99,
        bc3_descripcion_corta="Short",
        bc3_product_type="TYPE_01",
        bc3_descripcion_completa="Full description",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    dto = ProductoResponseDTO.from_entity(entity)
    assert dto.codigo == "TEST001"
    assert dto.descripcion == "Test Product"
    assert dto.pvp == 99.99
```

**Step 3: REFACTOR - Optimize**

- Add parametrized tests
- Add edge case tests
- Improve test documentation

**Test Fixtures Needed:**

- Standard pytest fixtures
- Coverage report

**Dependencies:** TASK-3.4.2 (HTTP layer created), TASK-3.4.3 (V2 endpoints), TASK-3.4.4 (V1 endpoints)

**Estimated Time:** 2 hours

**Verification Command:**

```bash
pytest --cov=app --cov-report=term-missing --cov-report=html
# Verify:
# - Overall coverage >= 39%
# - Domain >= 90%
# - Infrastructure >= 80%
# - Application/HTTP >= 70%
# - No uncovered critical paths
```

---

### TASK-3.5.3: Integration Tests for DI Flow

**Description:** Add integration tests that verify dependency injection flow from HTTP to database.

**Acceptance Criteria:**

- [ ] Integration tests verify HTTP → Depends → Service → Repository → Database → Response
- [ ] Integration tests verify service layer business logic validation
- [ ] Integration tests verify repository ORM operations with real database
- [ ] Integration tests verify DTO validation in both directions
- [ ] Integration tests verify error handling and HTTP status codes
- [ ] All integration tests passing
- [ ] Database transactions committed/rolled back correctly
- [ ] HTTP status codes validated

**TDD Approach:**

**Step 1: RED - Write failing integration tests**

```python
# tests/integration/test_di_flow.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture
def db_session():
    """Test database session"""
    from app.infrastructure.database.connection import SessionLocal
    db = SessionLocal()
    yield db
    db.close()

def test_di_flow_http_to_database(db_session):
    """Test HTTP → Depends → Service → Repository → Database → Response"""
    # Act
    response = client.get("/api/productos/v2/list?buscar=test&limit=5")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5
    
    # Verify data structure (DTO conversion worked)
    if len(data) > 0:
        product = data[0]
        assert "codigo" in product
        assert "descripcion" in product
        assert "marca" in product

def test_service_layer_validation(db_session):
    """Test service layer business logic validation"""
    from app.domain.services.producto import ProductoService
    from app.infrastructure.repositories.producto import SQLAlchemyProductoRepository
    from app.application.dto.producto import ProductoCreateDTO, ProductoSearchDTO
    from app.domain.exceptions.not_found import ValidationException
    
    service = ProductoService(SQLAlchemyProductoRepository(db_session))
    
    # Test validation: descripcion too short
    with pytest.raises(ValidationException):
        dto = ProductoCreateDTO(
            codigo="TEST001",
            descripcion="A",  # Too short (min 2 chars)
            marca="Test",
        )
        service.crear_producto(dto)

def test_repository_orm_operations(db_session):
    """Test repository ORM operations with real database"""
    from app.infrastructure.repositories.producto import SQLAlchemyProductoRepository
    from app.domain.entities.producto import ProductoEntity
    from datetime import datetime
    
    repo = SQLAlchemyProductoRepository(db_session)
    
    # Test ORM query
    entity = repo.get_by_codigo("TEST001")
    assert entity is not None
    assert isinstance(entity, ProductoEntity)
    
    # Test ORM filtering
    entities = repo.buscar_productos(termino="test", limit=5, marca="", familia="")
    assert isinstance(entities, list)
    assert len(entities) <= 5

def test_dto_validation(db_session):
    """Test DTO validation in both directions"""
    from app.application.dto.producto import (
        ProductoSearchDTO,
        ProductoResponseDTO,
        ProductoCreateDTO,
    )
    from app.domain.entities.producto import ProductoEntity
    from datetime import datetime
    
    # Test input DTO validation
    dto = ProductoSearchDTO(buscar="test", limit=10, marca="", familia="")
    assert dto.buscar == "test"
    assert dto.limit == 10
    
    # Test output DTO conversion
    entity = ProductoEntity(
        codigo="TEST001",
        descripcion="Test Product",
        marca="TestBrand",
        pvp=99.99,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    response_dto = ProductoResponseDTO.from_entity(entity)
    assert response_dto.codigo == "TEST001"
    assert response_dto.descripcion == "Test Product"

def test_error_handling_and_http_status_codes(db_session):
    """Test error handling and HTTP status codes"""
    # Test 404 (not found)
    response = client.get("/api/productos/v2/NONEXISTENT")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    
    # Test 422 (validation error)
    response = client.get("/api/productos/v2/list?limit=0")  # Invalid limit
    assert response.status_code == 422  # Pydantic validation error

def test_database_transaction_commit_rollback(db_session):
    """Test database transactions committed/rolled back correctly"""
    from app.domain.services.producto import ProductoService
    from app.infrastructure.repositories.producto import SQLAlchemyProductoRepository
    from app.application.dto.producto import ProductoCreateDTO
    from app.domain.exceptions.not_found import ProductoYaExisteException
    
    service = ProductoService(SQLAlchemyProductoRepository(db_session))
    
    # Test commit (successful transaction)
    try:
        dto = ProductoCreateDTO(
            codigo=f"UNIQUE_{datetime.now().timestamp()}",
            descripcion="Test Product for transaction",
            marca="TestBrand",
        )
        result = service.crear_producto(dto)
        assert result.codigo == dto.codigo
    except ProductoYaExisteException:
        pass  # Expected if code exists
    
    # Test rollback (failed transaction)
    # This is implicit in service layer - if validation fails, no commit happens
```

**Step 2: GREEN - Implement integration tests** (Already done in Step 1)

**Step 3: REFACTOR - Optimize**

- Extract common test fixtures
- Add parametrized tests
- Improve test documentation

**Test Fixtures Needed:**

- TestClient (FastAPI)
- Database session (real database with productos_clean view)

**Dependencies:** TASK-3.4.2 (HTTP layer created), TASK-3.4.3 (V2 endpoints)

**Estimated Time:** 2 hours

**Verification Command:**

```bash
pytest tests/integration/test_di_flow.py -v
pytest tests/integration/test_di_flow.py --cov=app/interfaces/http --cov-report=term-missing
```

---

### TASK-3.5.4: Performance Testing

**Description:** Verify response time degradation is minimal (< 100ms) for critical endpoints.

**Acceptance Criteria:**

- [ ] Performance benchmarks created for critical endpoints
- [ ] Response time P95 < 100ms for critical endpoints
- [ ] Response time degradation < 20% vs baseline
- [ ] No memory leaks in dependency injection (10k requests)
- [ ] Database connection pooling works correctly
- [ ] Application startup time < 2s (including DI setup)
- [ ] Memory usage increase < 50MB vs baseline

**TDD Approach:**

**Step 1: RED - Write performance tests**

```python
# tests/integration/test_performance.py
import pytest
import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_v2_list_endpoint_performance():
    """Test V2 list endpoint performance: P95 < 100ms"""
    response_times = []
    
    for _ in range(100):  # 100 requests
        start = time.time()
        response = client.get("/api/productos/v2/list?buscar=test&limit=10")
        elapsed = time.time() - start
        response_times.append(elapsed)
        assert response.status_code == 200
    
    # Calculate P95
    response_times.sort()
    p95_index = int(len(response_times) * 0.95)
    p95 = response_times[p95_index]
    
    assert p95 < 0.1  # < 100ms (0.1s)
    print(f"P95 response time: {p95 * 1000:.2f}ms")

def test_v2_detail_endpoint_performance():
    """Test V2 detail endpoint performance: P95 < 50ms"""
    response_times = []
    
    for _ in range(100):  # 100 requests
        start = time.time()
        response = client.get("/api/productos/v2/TEST001")
        elapsed = time.time() - start
        response_times.append(elapsed)
        assert response.status_code == 200
    
    # Calculate P95
    response_times.sort()
    p95_index = int(len(response_times) * 0.95)
    p95 = response_times[p95_index]
    
    assert p95 < 0.05  # < 50ms (0.05s)
    print(f"P95 response time: {p95 * 1000:.2f}ms")

def test_memory_no_leaks():
    """Test no memory leaks in DI after 10k requests"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    for _ in range(10000):  # 10k requests
        client.get("/api/productos/v2/list?buscar=test&limit=1")
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    # Memory increase should be reasonable (< 50MB)
    assert memory_increase < 50 * 1024 * 1024  # < 50MB
    print(f"Memory increase: {memory_increase / 1024 / 1024:.2f}MB")

def test_application_startup_time():
    """Test application startup < 2s"""
    import subprocess
    import time
    
    start = time.time()
    result = subprocess.run(
        ["python", "-c", "from app.main import app; print('Ready')"],
        capture_output=True,
        text=True,
        timeout=10
    )
    elapsed = time.time() - start
    
    assert result.returncode == 0
    assert elapsed < 2.0  # < 2s
    print(f"Startup time: {elapsed:.2f}s")
```

**Step 2: GREEN - Run performance tests and optimize**

```bash
# Run performance tests
pytest tests/integration/test_performance.py::test_v2_list_endpoint_performance -v

# If P95 > 100ms, investigate and optimize:
# 1. Add database indexes
# 2. Optimize ORM queries
# 3. Add caching layer (future phase)
# 4. Optimize DTO conversion
```

**Step 3: REFACTOR - Optimize**

- Add database query optimization
- Optimize DTO conversion (use list comprehension)
- Add caching if needed (future phase)

**Test Fixtures Needed:**

- TestClient (FastAPI)
- psutil (for memory monitoring)

**Dependencies:** TASK-3.4.2 (HTTP layer created), TASK-3.4.3 (V2 endpoints)

**Estimated Time:** 1 hour

**Verification Command:**

```bash
pytest tests/integration/test_performance.py -v
# Verify:
# - P95 < 100ms for critical endpoints
# - Degradation < 20% vs baseline
# - No memory leaks
```

---

### TASK-3.5.5: Type Safety

**Description:** Maintain type safety with mypy and type hints for all new code.

**Acceptance Criteria:**

- [ ] All new code includes type hints
- [ ] mypy runs on codebase: zero mypy errors in migrated code
- [ ] Return types annotated for all functions
- [ ] Parameter types annotated for all functions
- [ ] Optional/Union types used correctly
- [ ] Pydantic models have proper type annotations
- [ ] Type hints覆盖率 >= 90% for new code
- [ ] No `Any` types in business logic

**TDD Approach:**

**Step 1: RED - Run mypy to find type errors**

```bash
mypy app/interfaces/http/productos.py
mypy app/domain/services/producto.py
mypy app/application/dto/producto.py
mypy app/infrastructure/repositories/producto.py
mypy app/infrastructure/models/producto_clean.py
```

**Step 2: GREEN - Fix type errors**

```python
# Fix missing type hints
from typing import Optional
from datetime import datetime

def buscar_productos_v2(
    buscar: str,
    limit: int,
    marca: str,
    familia: str,
    service: ProductoService,  # ← Add type hint
) -> list[ProductoResponseDTO]:  # ← Add return type
    """Search products with filters"""
    dto = ProductoSearchDTO(
        buscar=buscar,
        limit=limit,
        marca=marca,
        familia=familia,
    )
    entities = service.buscar_productos(dto)
    return [ProductoResponseDTO.from_entity(e) for e in entities]

# Fix Any types
def get_producto_service() -> ProductoService:  # ← Specific type, not Any
    return ProductoService(SQLAlchemyProductoRepository(SessionLocal()))
```

**Step 3: REFACTOR - Optimize**

- Use modern type hints (str | None instead of Optional[str])
- Add type aliases for complex types
- Add type comments for obscure cases

**Test Fixtures Needed:**

- mypy (type checker)

**Dependencies:** TASK-3.4.2 (HTTP layer created)

**Estimated Time:** 1 hour

**Verification Command:**

```bash
mypy app/interfaces/http/ app/domain/ app/infrastructure/ app/application/
# Verify: zero mypy errors
mypy --html-report mypy-report app/
# Verify: Type hints覆盖率 >= 90%
```

---

## Task Dependencies

### Phase 3.4: DI Setup

```
TASK-3.4.1 (DI Configuration)
    ↓ (No dependencies)
TASK-3.4.2 (HTTP Layer Created)
    ↓ (Depends on 3.4.1)
TASK-3.4.3 (V2 Endpoints Migrated)
    ↓ (Depends on 3.4.2)
TASK-3.4.4 (V1 Backward Compatibility)
    ↓ (Depends on 3.4.2)
TASK-3.4.5 (BC3 Suite Compatibility)
    ↓ (Depends on 3.4.2, 3.4.3, 3.4.4)
```

### Phase 3.5: Testing Migration

```
TASK-3.5.1 (Service Tests Fixing)
    ↓ (No dependencies)
TASK-3.5.2 (Coverage Maintenance)
    ↓ (Depends on 3.4.x all)
TASK-3.5.3 (Integration Tests)
    ↓ (Depends on 3.4.x all)
TASK-3.5.4 (Performance Testing)
    ↓ (Depends on 3.4.x all)
TASK-3.5.5 (Type Safety)
    ↓ (Depends on 3.4.2)
```

---

## Execution Order

### Sequential Execution (Recommended)

1. **Phase 3.4:** Complete all DI setup tasks first
   - TASK-3.4.1 → TASK-3.4.2 → TASK-3.4.3 → TASK-3.4.4 → TASK-3.4.5
2. **Phase 3.5:** Complete testing migration tasks
   - TASK-3.5.1 → TASK-3.5.2 → TASK-3.5.3 → TASK-3.5.4 → TASK-3.5.5

### Parallel Execution (Advanced)

- Phase 3.4: Sequential (must complete in order)
- Phase 3.5: Can run TASK-3.5.1 + TASK-3.5.2 + TASK-3.5.5 in parallel
- Phase 3.5: Must run TASK-3.5.3 + TASK-3.5.4 after Phase 3.4 complete

---

## Time Estimates

| Phase | Task | Estimated Time | Total Phase Time |
|-------|------|----------------|------------------|
| **3.4** | TASK-3.4.1 | 30 min | 6.5 hours |
| | TASK-3.4.2 | 2 hours | |
| | TASK-3.4.3 | 2 hours | |
| | TASK-3.4.4 | 1 hour | |
| | TASK-3.4.5 | 1 hour | |
| **3.5** | TASK-3.5.1 | 1 hour | 7 hours |
| | TASK-3.5.2 | 2 hours | |
| | TASK-3.5.3 | 2 hours | |
| | TASK-3.5.4 | 1 hour | |
| | TASK-3.5.5 | 1 hour | |
| **TOTAL** | - | **13.5 hours** | **13.5 hours** |

---

## Completion Criteria

### Phase 3.4 Completion

- [ ] All 5 tasks in Phase 3.4 completed
- [ ] All acceptance criteria satisfied
- [ ] All tests passing (unit + integration)
- [ ] Performance benchmarks met
- [ ] BC3 Suite compatibility verified
- [ ] No blocking issues

### Phase 3.5 Completion

- [ ] All 5 tasks in Phase 3.5 completed
- [ ] All acceptance criteria satisfied
- [ ] All tests passing (unit + integration + performance)
- [ ] Coverage >= 39% (baseline maintained)
- [ ] Type safety maintained (mypy zero errors)
- [ ] No blocking issues

### Overall Completion

- [ ] All 10 tasks completed
- [ ] All 10 acceptance criteria satisfied
- [ ] SDD workflow ready for next phase (Verify)

---

## Next Steps

After completing all tasks:

1. **Run full test suite:**

   ```bash
   pytest tests/ -v --cov=app --cov-report=html
   ```

2. **Verify acceptance criteria:**
   - Manual BC3 Suite App testing
   - Performance benchmarks
   - Coverage report review

3. **Proceed to SDD Verify phase**
   - Review artifacts
   - Run verification tests
   - Generate verification report

4. **Proceed to SDD Archive phase**
   - Complete change documentation
   - Archive completed change
   - Lessons learned

---

**End of Tasks**
