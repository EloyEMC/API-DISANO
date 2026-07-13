# Fase 3 - Architecture Hexagonal Migration: Specification

## Overview

Detailed functional and non-functional requirements for migrating API-DISANO to Hexagonal Architecture with Dependency Injection.

**Change ID:** fase3-architecture-hexagonal  
**Phase:** Fase 3.4 + 3.5 (DI Setup + Testing Migration)  
**Version:** 1.0

---

## 1. Functional Requirements

### 1.1 Fase 3.4: Dependency Injection Setup

#### FR-1.4.1: DI Configuration in main.py

**Description:** Configure FastAPI application with dependency injection for database sessions, repositories, and services.

**Acceptance Criteria:**

- GIVEN FastAPI application exists in main.py
- WHEN application starts with DI configuration
- THEN dependency functions are registered and callable via Depends()
- AND database sessions are properly scoped to requests
- AND services receive correct repository implementations

**Evidence Required:**

- pytest tests for DI setup
- Application startup success (< 2s)
- No dependency injection errors in logs

---

#### FR-1.4.2: HTTP Interface Layer (productos router)

**Description:** Create `app/interfaces/http/productos.py` with hexagonal architecture pattern using DI.

**Acceptance Criteria:**

- GIVEN productos router exists with hexagonal pattern
- WHEN HTTP requests arrive
- THEN dependencies are injected via FastAPI Depends()
- AND business logic calls ProductoService methods
- AND DTOs validate request/response data
- AND no direct database access in HTTP layer

**Evidence Required:**

- File exists at app/interfaces/http/productos.py
- All endpoints use service dependencies
- No sqlite3 imports in http layer
- Repository interface imports only

---

#### FR-1.4.3: V2 Endpoints Migration

**Description:** Migrate V2 endpoints to use Product Services with DTOs.

**Endpoints to migrate:**

1. `GET /api/productos/v2/list` - Search products with filters
2. `GET /api/productos/v2/{codigo}` - Get product by code
3. `GET /api/productos/v2/marca/{marca}` - Filter by brand
4. `GET /api/productos/v2/familia/{familia}` - Filter by family

**Acceptance Criteria:**

- GIVEN V2 endpoints use ProductoService
- WHEN client makes V2 requests
- THEN ProductoSearchDTO validates query parameters
- AND ProductoResponseDTO formats responses
- AND business logic is in service layer
- AND response time degradation < 100ms

**Evidence Required:**

- HTTP 200 OK responses for all V2 endpoints
- Pydantic validation errors for invalid input
- Service layer business logic executed
- No direct database queries in router

---

#### FR-1.4.4: V1 Endpoints Backward Compatibility

**Description:** Maintain V1 endpoints for backward compatibility while using hexagonal architecture internally.

**Endpoints to maintain:**

1. `GET /api/productos/` - Legacy list endpoint
2. `GET /api/productos/{codigo}` - Legacy detail endpoint

**Acceptance Criteria:**

- GIVEN V1 endpoints exist
- WHEN existing clients use V1 endpoints
- THEN responses match legacy format
- AND internal architecture uses services
- AND BC3 Suite App continues working
- AND no breaking changes for clients

**Evidence Required:**

- BC3 Suite integration tests passing
- V1 responses match legacy schema
- HTTP 200 OK for valid requests
- HTTP 404 for non-existent products

---

#### FR-1.4.5: BC3 Suite Compatibility

**Description:** Ensure BC3 Suite integration works with hexagonal architecture.

**BC3 Fields Required:**

- `bc3_descripcion_corta` - Short description for BC3
- `bc3_product_type` - Product classification
- `bc3_descripcion_completa` - Full description
- `codigo` (aliased as `codigo_web`) - Product code
- `descripcion` - Primary description field

**Acceptance Criteria:**

- GIVEN BC3 Suite App makes V2 requests
- WHEN hexagonal architecture processes requests
- THEN BC3 fields are present in responses
- AND responses match BC3 Suite schema
- AND 8,288 products accessible
- AND BC3 Suite tests pass

**Evidence Required:**

- BC3 Suite integration test suite (all passing)
- Response validation with BC3 schema
- Product count verification (8,288)
- Performance benchmarks (response time < 500ms)

---

### 1.2 Fase 3.5: Testing Migration

#### FR-1.5.1: Service Tests Fixing

**Description:** Fix 14/14 failing service tests to pass with proper imports and mocks.

**Current Issues:**

- `ProductoRepositoryInterface` import missing
- Test entities missing required fields
- Mock repository setup incorrect

**Acceptance Criteria:**

- GIVEN service tests exist in tests/unit/domain/test_producto_service.py
- WHEN pytest runs service tests
- THEN all 14 tests pass
- AND proper imports resolved
- AND mock repositories configured correctly
- AND TDD cycle (RED → GREEN → REFACTOR) followed

**Evidence Required:**

- pytest results: 14/14 passing
- Coverage report shows service methods covered
- No import errors
- Mock assertions verify correct service behavior

---

#### FR-1.5.2: Coverage Maintenance

**Description:** Maintain or improve code coverage baseline during migration.

**Baseline:** 39% coverage (from Fase 2)

**Acceptance Criteria:**

- GIVEN coverage baseline is 39%
- WHEN hexagonal architecture is implemented
- THEN coverage >= 39% (maintain baseline)
- AND new code has >= 80% coverage (TDD target)
- AND critical paths (service, repository) >= 90%
- AND pytest-cov report shows no uncovered critical paths

**Evidence Required:**

- pytest-cov report: >= 39% overall
- Coverage by module: domain >= 90%, infrastructure >= 80%, http >= 70%
- No uncovered critical business logic
- Coverage diff shows improvement, not regression

---

#### FR-1.5.3: Integration Tests for DI Flow

**Description:** Add integration tests that verify dependency injection flow from HTTP to database.

**Test Scenarios:**

1. HTTP request → Depends() → Service → Repository → Database → Response
2. Service layer business logic validation
3. Repository ORM operations with real database
4. DTO validation in both directions
5. Error handling and HTTP status codes

**Acceptance Criteria:**

- GIVEN integration tests exist for DI flow
- WHEN HTTP requests are made via test client
- THEN dependencies are correctly injected
- AND service layer validates business rules
- AND repository performs ORM operations
- AND database transactions committed/rolled back
- AND HTTP responses include correct status codes

**Evidence Required:**

- Integration tests using FastAPI TestClient
- Database fixtures (test DB with productos_clean view)
- All integration tests passing
- Transaction rollback verified
- HTTP status codes validated

---

#### FR-1.5.4: Performance Testing

**Description:** Verify response time degradation is minimal (< 100ms) for critical endpoints.

**Benchmark Endpoints:**

- `GET /api/productos/v2/list?buscar=test&limit=10`
- `GET /api/productos/v2/{codigo}`
- `GET /api/productos/` (V1 legacy)

**Acceptance Criteria:**

- GIVEN performance benchmarks exist for endpoints
- WHEN load testing with 100 concurrent requests
- THEN 95th percentile response time < 100ms
- AND response time degradation < 20% vs baseline
- AND no memory leaks in dependency injection
- AND database connection pooling works correctly

**Evidence Required:**

- Performance benchmark report (before/after migration)
- Response time P95 < 100ms for critical endpoints
- Memory usage stable under load
- Database connection pool metrics

---

#### FR-1.5.5: Type Safety

**Description:** Maintain type safety with mypy and type hints for all new code.

**Acceptance Criteria:**

- GIVEN all new code includes type hints
- WHEN mypy runs on the codebase
- THEN zero mypy errors in migrated code
- AND return types annotated for all functions
- AND parameter types annotated for all functions
- AND Optional/Union types used correctly
- AND Pydantic models have proper type annotations

**Evidence Required:**

- mypy report: zero errors
- Type hints覆盖率 >= 90% for new code
- No `Any` types in business logic
- Pydantic models properly typed

---

## 2. API Contracts

### 2.1 V2 Endpoints Specification

#### GET /api/productos/v2/list

**Purpose:** Search products with filters

**Query Parameters:**

| Parameter | Type | Required | Description | Constraints |
|-----------|------|----------|-------------|-------------|
| `buscar` | string | Yes | Search term (codigo, descripcion) | min_length: 1 |
| `limit` | integer | No | Max results to return | min: 1, max: 100, default: 10 |
| `marca` | string | No | Filter by brand | max_length: 50, default: "" |
| `familia` | string | No | Filter by family | max_length: 50, default: "" |

**Response (200 OK):**

```json
{
  "codigo": "TEST001",
  "descripcion": "Test Product",
  "marca": "TestBrand",
  "familia": "Electrónica",
  "pvp": 99.99,
  "bc3_descripcion_corta": "Short desc",
  "bc3_product_type": "TYPE_01",
  "bc3_descripcion_completa": "Full description"
}
```

**Error Responses:**

- `400 Bad Request` - Invalid query parameters
- `500 Internal Server Error` - Database or service error

---

#### GET /api/productos/v2/{codigo}

**Purpose:** Get product by code

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `codigo` | string | Yes | Product code |

**Response (200 OK):**
Same as GET /api/productos/v2/list response

**Error Responses:**

- `404 Not Found` - Product does not exist
- `500 Internal Server Error` - Database or service error

---

#### GET /api/productos/v2/marca/{marca}

**Purpose:** Search products by brand

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `marca` | string | Yes | Brand name |

**Query Parameters:**

| Parameter | Type | Required | Description | Constraints |
|-----------|------|----------|-------------|-------------|
| `limit` | integer | No | Max results | min: 1, max: 100, default: 10 |

**Response (200 OK):**
Array of ProductoResponseDTO objects

**Error Responses:**

- `500 Internal Server Error` - Database or service error

---

#### GET /api/productos/v2/familia/{familia}

**Purpose:** Search products by family

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `familia` | string | Yes | Family name |

**Query Parameters:**

| Parameter | Type | Required | Description | Constraints |
|-----------|------|----------|-------------|-------------|
| `limit` | integer | No | Max results | min: 1, max: 100, default: 10 |

**Response (200 OK):**
Array of ProductoResponseDTO objects

**Error Responses:**

- `500 Internal Server Error` - Database or service error

---

### 2.2 V1 Endpoints (Backward Compatible)

#### GET /api/productos/

**Purpose:** Legacy product search (maintained for BC3 compatibility)

**Query Parameters:**

| Parameter | Type | Required | Description | Constraints |
|-----------|------|----------|-------------|-------------|
| `buscar` | string | No | Search term | - |
| `limit` | integer | No | Max results | min: 1, max: 500, default: 100 |
| `marca` | string | No | Filter by brand | - |

**Response (200 OK):**
Legacy V1 format (maintains backward compatibility)

**Error Responses:**

- `404 Not Found` - No products found
- `500 Internal Server Error` - Database error

---

#### GET /api/productos/{codigo}

**Purpose:** Legacy product detail (maintained for BC3 compatibility)

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `codigo` | string | Yes | Product code |

**Response (200 OK):**
Legacy V1 format (maintains backward compatibility)

**Error Responses:**

- `404 Not Found` - Product does not exist
- `500 Internal Server Error` - Database error

---

## 3. Data Contracts

### 3.1 Input DTOs

#### ProductoSearchDTO

```python
class ProductoSearchDTO(BaseModel):
    buscar: Optional[str] = Field(None, min_length=1)
    limit: int = Field(10, ge=1, le=100)
    marca: Optional[str] = Field(None, max_length=50)
    familia: Optional[str] = Field(None, max_length=50)
```

**Validation Rules:**

- `buscar`: Optional, min 1 character if provided
- `limit`: Required, 1-100 range, default 10
- `marca`: Optional, max 50 characters
- `familia`: Optional, max 50 characters

---

#### ProductoCreateDTO

```python
class ProductoCreateDTO(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=50)
    descripcion: str = Field(..., min_length=2)
    marca: str = Field(..., min_length=1)
    familia: Optional[str] = Field(None)
    pvp: Optional[float] = Field(None, ge=0)
    bc3_descripcion_corta: Optional[str] = Field(None)
    bc3_product_type: Optional[str] = Field(None)
    bc3_descripcion_completa: Optional[str] = Field(None)
```

**Validation Rules:**

- `codigo`: Required, 1-50 characters
- `descripcion`: Required, min 2 characters
- `marca`: Required, min 1 character
- `pvp`: Optional, >= 0
- All fields validated by Pydantic v2

---

#### ProductoUpdateDTO

```python
class ProductoUpdateDTO(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=2)
    marca: Optional[str] = Field(None, min_length=1)
    familia: Optional[str] = Field(None)
    pvp: Optional[float] = Field(None, ge=0)
    bc3_descripcion_corta: Optional[str] = Field(None)
    bc3_product_type: Optional[str] = Field(None)
    bc3_descripcion_completa: Optional[str] = Field(None)
```

**Validation Rules:**

- All fields optional (partial updates)
- Same validation rules as create DTO
- Pydantic v2 validation

---

#### ProductoPrecioUpdateDTO

```python
class ProductoPrecioUpdateDTO(BaseModel):
    pvp: float = Field(..., ge=0)
```

**Validation Rules:**

- `pvp`: Required, >= 0
- Simple single-field DTO for price updates

---

### 3.2 Output DTOs

#### ProductoResponseDTO

```python
class ProductoResponseDTO(BaseModel):
    codigo: str
    descripcion: str
    marca: str
    familia: Optional[str] = None
    pvp: Optional[float] = None
    bc3_descripcion_corta: Optional[str] = None
    bc3_product_type: Optional[str] = None
    bc3_descripcion_completa: Optional[str] = None

    @classmethod
    def from_entity(cls, entity: ProductoEntity) -> "ProductoResponseDTO":
        # Conversion from ProductoEntity to DTO
```

**BC3 Suite Compatibility:**

- Includes all 5 BC3 fields
- Maintains BC3 Suite schema
- Serializable to JSON

---

#### ProductoListResponseDTO

```python
class ProductoListResponseDTO(BaseModel):
    productos: list[ProductoResponseDTO]
    total: int
    limit: int
    filtered: bool

    @classmethod
    def from_entities(cls, entities: list[ProductoEntity], limit: int, has_filters: bool):
        # Conversion from entity list to list DTO
```

**Usage:**

- Wrap array responses with metadata
- Include total count, limit, filter flag
- Useful for pagination and UI

---

### 3.3 Domain Entities

#### ProductoEntity

```python
class ProductoEntity(BaseModel):
    codigo: str
    descripcion: str
    marca: str
    familia: Optional[str] = None
    pvp: Optional[float] = None
    bc3_descripcion_corta: Optional[str] = None
    bc3_product_type: Optional[str] = None
    bc3_descripcion_completa: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(frozen=True)
```

**Business Rules:**

- Immutable (frozen=True)
- No database dependencies
- Contains BC3 fields
- Domain entity only (no HTTP concerns)

---

### 3.4 Repository Interfaces

#### ProductoRepositoryInterface

```python
class ProductoRepositoryInterface(ABC):
    @abstractmethod
    def save(self, entity: ProductoEntity) -> ProductoEntity:
        pass

    @abstractmethod
    def get_by_codigo(self, codigo: str) -> ProductoEntity:
        pass

    @abstractmethod
    def buscar_productos(
        self, termino: str, limit: int, marca: str, familia: str
    ) -> list[ProductoEntity]:
        pass

    @abstractmethod
    def delete(self, codigo: str) -> bool:
        pass

    @abstractmethod
    def get_all(self, skip: int, limit: int) -> list[ProductoEntity]:
        pass

    @abstractmethod
    def count_total(self) -> int:
        pass
```

**Contract:**

- Abstract Base Class (ABC)
- All methods abstract (no implementation)
- Defines repository contract for domain layer
- Implementation in infrastructure layer

---

## 4. Use Cases (CQRS)

### 4.1 Queries (Read Operations)

#### UC-Q1: Buscar Productos

**Actor:** User/Client (public endpoint)

**Preconditions:**

- Database contains 8,288 products
- productos_clean view exists
- Indexes on codigo, descripcion, marca

**Main Flow:**

1. Client sends GET request to /api/productos/v2/list with query params
2. FastAPI Depends() injects ProductoService
3. ProductoService receives ProductoSearchDTO (validated)
4. ProductoService calls repository.buscar_productos()
5. Repository queries productos_clean view with filters
6. Repository returns list[ProductoEntity]
7. Service returns list to HTTP layer
8. HTTP layer converts to ProductoResponseDTO[]
9. FastAPI serializes to JSON (200 OK)

**Alternative Flows:**

- **3a:** Invalid query params → Pydantic validation error (400 Bad Request)
- **6a:** No products found → Empty list (200 OK)
- **6b:** Database error → HTTPException (500 Internal Server Error)

**Postconditions:**

- Client receives product list
- Response includes BC3 fields
- Response time < 100ms (P95)

---

#### UC-Q2: Obtener Producto por Código

**Actor:** User/Client (public endpoint)

**Preconditions:**

- Product exists in database
- productos_clean view accessible

**Main Flow:**

1. Client sends GET request to /api/productos/v2/{codigo}
2. FastAPI Depends() injects ProductoService
3. ProductoService calls repository.get_by_codigo(codigo)
4. Repository queries productos_clean view
5. Repository returns ProductoEntity
6. Service returns entity to HTTP layer
7. HTTP layer converts to ProductoResponseDTO
8. FastAPI serializes to JSON (200 OK)

**Alternative Flows:**

- **5a:** Product not found → ProductoNotFoundException → HTTPException (404 Not Found)
- **5b:** Database error → HTTPException (500 Internal Server Error)

**Postconditions:**

- Client receives product details
- Response includes BC3 fields
- Response time < 50ms (P95)

---

### 4.2 Commands (Write Operations)

#### UC-C1: Crear Producto (Future)

**Actor:** Admin user (authenticated endpoint)

**Preconditions:**

- Admin API key verified
- Product code does not exist

**Main Flow:**

1. Admin sends POST request to /api/productos/admin/create
2. API key middleware validates admin access
3. FastAPI Depends() injects ProductoService
4. Service receives ProductoCreateDTO (validated)
5. Service validates business rules (descripcion >= 2 chars, pvp >= 0)
6. Service checks product does not exist (repository.get_by_codigo())
7. Service creates ProductoEntity from DTO
8. Service calls repository.save(entity)
9. Repository inserts into productos_clean view
10. Repository returns ProductoEntity
11. Service returns entity to HTTP layer
12. HTTP layer converts to ProductoResponseDTO
13. FastAPI serializes to JSON (201 Created)

**Alternative Flows:**

- **2a:** Invalid API key → 401 Unauthorized
- **6a:** Business validation fails → ValidationException → 400 Bad Request
- **7a:** Product already exists → ProductoYaExisteException → 409 Conflict
- **9a:** Database error → HTTPException (500 Internal Server Error)

**Postconditions:**

- Product created in database
- Response includes all fields
- BC3 fields populated

---

#### UC-C2: Actualizar Producto (Future)

**Actor:** Admin user (authenticated endpoint)

**Preconditions:**

- Admin API key verified
- Product exists in database

**Main Flow:**

1. Admin sends PUT/PATCH request to /api/productos/admin/{codigo}
2. API key middleware validates admin access
3. FastAPI Depends() injects ProductoService
4. Service receives ProductoUpdateDTO (validated, partial)
5. Service retrieves existing product (repository.get_by_codigo())
6. Service applies updates to entity
7. Service validates updated fields
8. Service creates updated ProductoEntity
9. Service calls repository.save(entity)
10. Repository updates productos_clean view
11. Repository returns ProductoEntity
12. Service returns entity to HTTP layer
13. HTTP layer converts to ProductoResponseDTO
14. FastAPI serializes to JSON (200 OK)

**Alternative Flows:**

- **2a:** Invalid API key → 401 Unauthorized
- **5a:** Product not found → ProductoNotFoundException → 404 Not Found
- **7a:** Invalid update data → ValidationException → 400 Bad Request
- **10a:** Database error → HTTPException (500 Internal Server Error)

**Postconditions:**

- Product updated in database
- Response includes updated fields
- BC3 fields preserved

---

## 5. Non-Functional Requirements

### 5.1 Performance

#### NFR-P1: Response Time

**Requirement:** 95th percentile response time < 100ms for critical endpoints

**Endpoints:**

- GET /api/productos/v2/list
- GET /api/productos/v2/{codigo}

**Measurement:**

- Use performance testing framework (locust/pytest-benchmark)
- 100 concurrent requests for 1 minute
- Measure P95 response time
- Compare vs baseline

**Acceptance:**

- P95 < 100ms ✅
- Degradation < 20% vs baseline ✅

---

#### NFR-P2: Startup Time

**Requirement:** Application startup < 2 seconds including DI setup

**Measurement:**

- Measure time from `python app/main.py` to `INFO: Application startup complete`
- Include database connection pool initialization
- Include DI container setup

**Acceptance:**

- Startup < 2s ✅

---

#### NFR-P3: Memory Usage

**Requirement:** Memory usage increase < 50MB vs baseline

**Measurement:**

- Use memory_profiler or docker stats
- Measure steady-state memory under load
- Compare vs baseline

**Acceptance:**

- Memory increase < 50MB ✅
- No memory leaks after 10k requests ✅

---

### 5.2 Reliability

#### NFR-R1: Error Handling

**Requirement:** All errors handled with appropriate HTTP status codes and error messages

**Status Codes:**

- 200 OK - Success
- 400 Bad Request - Invalid input
- 401 Unauthorized - Invalid API key
- 404 Not Found - Resource not found
- 409 Conflict - Duplicate resource
- 500 Internal Server Error - Unexpected error

**Error Response Format:**

```json
{
  "detail": "Product not found"
}
```

**Acceptance:**

- All exceptions mapped to HTTP status codes ✅
- Error messages are clear and actionable ✅
- No stack traces in production responses ✅

---

#### NFR-R2: Database Transaction Management

**Requirement:** Database transactions properly committed/rolled back

**Measurement:**

- Test transaction rollback on service exceptions
- Test transaction commit on success
- Test connection cleanup

**Acceptance:**

- Transactions rolled back on error ✅
- Connections released after request ✅
- No orphan transactions ✅

---

### 5.3 Security

#### NFR-S1: API Key Authentication

**Requirement:** Admin endpoints require valid API key

**Implementation:**

- API key middleware validates `X-API-Key` header
- Uses verify_admin_api_key() function
- Returns 401 Unauthorized for invalid keys

**Acceptance:**

- Valid key → 200 OK ✅
- Invalid key → 401 Unauthorized ✅
- Missing key → 401 Unauthorized ✅

---

#### NFR-S2: Input Validation

**Requirement:** All inputs validated before processing

**Implementation:**

- Pydantic v2 DTOs validate request bodies
- FastAPI Query() validates query params
- Product service validates business rules

**Acceptance:**

- Invalid input → 400 Bad Request ✅
- Valid input → Processing continues ✅
- No SQL injection possible ✅

---

#### NFR-S3: SQL Injection Prevention

**Requirement:** No SQL injection vulnerabilities

**Implementation:**

- Use SQLAlchemy ORM (parameterized queries)
- Never concatenate raw SQL
- Validate inputs before queries

**Acceptance:**

- All queries use ORM ✅
- No raw SQL concatenation ✅
- SQL injection tests pass ✅

---

### 5.4 Maintainability

#### NFR-M1: Code Organization

**Requirement:** Clear separation of concerns following hexagonal architecture

**Structure:**

```
app/
├── domain/              # Business logic (no external deps)
├── infrastructure/      # Database + external implementations
├── application/         # DTOs + use cases
└── interfaces/http/     # HTTP layer with DI
```

**Acceptance:**

- Each layer has single responsibility ✅
- Domain has no infrastructure dependencies ✅
- HTTP layer is thin (< 50 lines per endpoint) ✅

---

#### NFR-M2: Type Safety

**Requirement:** All code includes type hints

**Measurement:**

- Run mypy on codebase
- Check type hint覆盖率

**Acceptance:**

- Zero mypy errors in migrated code ✅
- Type hints覆盖率 >= 90% for new code ✅
- No `Any` types in business logic ✅

---

#### NFR-M3: Documentation

**Requirement:** All public interfaces documented

**Documentation:**

- API docs (FastAPI auto-generated)
- Docstrings for all service methods
- Docstrings for all repository methods
- Comments for complex logic

**Acceptance:**

- API docs complete ✅
- Docstrings覆盖率 >= 80% for new code ✅
- Complex logic has comments ✅

---

### 5.5 Scalability

#### NFR-SC1: Database Connection Pooling

**Requirement:** Efficient database connection management

**Implementation:**

- SQLAlchemy session pool
- Scoped sessions for request lifecycle
- Connection limits configured

**Acceptance:**

- Connection pool configured ✅
- Connections released after request ✅
- Pool exhaustion handled gracefully ✅

---

#### NFR-SC2: Caching Readiness

**Requirement:** Architecture supports future caching

**Implementation:**

- Service layer abstract from data source
- Repository interface cache-agnostic
- DTOs serializable for cache storage

**Acceptance:**

- Cache can be added without changing services ✅
- Cache can be added without changing HTTP layer ✅
- Cache-agnostic repository interface ✅

---

## 6. Acceptance Criteria

### 6.1 Phase 3.4 Acceptance

**AC-3.4.1:** DI Configuration Complete
**Given:** FastAPI application exists  
**When:** DI configuration added to main.py  
**Then:** Dependency functions registered and callable  
**And:** Application starts successfully (< 2s)  
**And:** No DI errors in logs

---

**AC-3.4.2:** HTTP Interface Layer Created
**Given:** productos router exists  
**When:** app/interfaces/http/productos.py created  
**Then:** All endpoints use service dependencies  
**And:** No sqlite3 imports in HTTP layer  
**And:** Repository interfaces only imported

---

**AC-3.4.3:** V2 Endpoints Migrated
**Given:** V2 endpoints using ProductService  
**When:** Client makes V2 requests  
**Then:** Pydantic validation for requests/responses  
**And:** Business logic in service layer  
**And:** Response time degradation < 100ms

---

**AC-3.4.4:** V1 Backward Compatibility
**Given:** V1 endpoints exist  
**When:** Existing clients use V1 endpoints  
**Then:** Responses match legacy format  
**And:** BC3 Suite App continues working  
**And:** No breaking changes

---

**AC-3.4.5:** BC3 Suite Compatibility
**Given:** BC3 Suite App makes V2 requests  
**When:** Hexagonal architecture processes requests  
**Then:** BC3 fields present in responses  
**And:** 8,288 products accessible  
**And:** BC3 Suite tests pass

---

### 6.2 Phase 3.5 Acceptance

**AC-3.5.1:** Service Tests Passing
**Given:** Service tests exist  
**When:** pytest runs service tests  
**Then:** All 14 tests pass  
**And:** Imports resolved  
**And:** Mock repositories configured correctly

---

**AC-3.5.2:** Coverage Maintained
**Given:** Coverage baseline is 39%  
**When:** Hexagonal architecture implemented  
**Then:** Coverage >= 39% overall  
**And:** New code >= 80% coverage  
**And:** Critical paths >= 90% coverage

---

**AC-3.5.3:** Integration Tests Added
**Given:** Integration tests for DI flow  
**When:** HTTP requests made via test client  
**Then:** Dependencies correctly injected  
**And:** Service layer validates business rules  
**And:** Transactions committed/rolled back

---

**AC-3.5.4:** Performance Validated
**Given:** Performance benchmarks exist  
**When:** Load testing with 100 concurrent requests  
**Then:** P95 response time < 100ms  
**And:** Degradation < 20% vs baseline  
**And:** No memory leaks

---

**AC-3.5.5:** Type Safety Maintained
**Given:** All new code includes type hints  
**When:** mypy runs on codebase  
**Then:** Zero mypy errors  
**And:** Type hints覆盖率 >= 90%  
**And:** No `Any` types in business logic

---

## 7. Error Handling

### 7.1 Exception to HTTP Status Mapping

| Exception | HTTP Status | Description |
|-----------|-------------|-------------|
| `ValidationException` | 400 Bad Request | Business validation failed |
| `ProductoNotFoundException` | 404 Not Found | Product does not exist |
| `ProductoYaExisteException` | 409 Conflict | Product code already exists |
| `HTTPException` | As configured | FastAPI HTTP exception |
| `Exception` (unhandled) | 500 Internal Server Error | Unexpected error |

### 7.2 Error Response Format

```json
{
  "detail": "Product not found"
}
```

**For Validation Errors:**

```json
{
  "detail": [
    {
      "loc": ["body", "descripcion"],
      "msg": "ensure this value has at least 2 characters",
      "type": "value_error.any_str.min_length",
      "ctx": {"min_length": 2}
    }
  ]
}
```

### 7.3 Error Handling Pattern

```python
try:
    entity = service.obtener_producto(codigo)
    return ProductoResponseDTO.from_entity(entity)
except ProductoNotFoundException:
    raise HTTPException(status_code=404, detail="Product not found")
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
```

---

## 8. Testing Requirements

### 8.1 Unit Tests

**Domain Layer:**

- ProductoEntity validation tests
- Domain exception tests
- Repository interface contract tests
- Service business logic tests (with mocks)

**Infrastructure Layer:**

- ORM model tests (4/4 passing)
- Repository implementation tests
- Database connection tests

**Application Layer:**

- DTO validation tests
- DTO conversion tests (entity ↔ DTO)
- Use case tests (with mocks)

**Coverage Target:**

- Domain: >= 90%
- Infrastructure: >= 80%
- Application: >= 80%
- Overall: >= 39%

---

### 8.2 Integration Tests

**DI Flow Tests:**

- HTTP request → Depends() → Service → Repository → Database → Response
- Database transaction commit/rollback
- Connection cleanup

**Service Layer Tests:**

- Business validation rules
- Error handling
- Repository integration

**Repository Tests:**

- ORM operations with real database
- productos_clean view queries
- Index performance

**Coverage Target:**

- HTTP layer: >= 70%
- Service layer: >= 80%
- Repository layer: >= 80%

---

### 8.3 End-to-End Tests

**BC3 Suite Integration:**

- All BC3 Suite endpoints working
- BC3 fields present in responses
- Performance benchmarks met
- No breaking changes

**HTTP Client Tests:**

- V1 endpoints backward compatibility
- V2 endpoints new functionality
- Error responses correct

**Load Tests:**

- 100 concurrent requests
- P95 response time < 100ms
- No memory leaks

---

### 8.4 TDD Compliance

**TDD Cycle:**

1. **RED:** Write failing test
2. **GREEN:** Implement minimal code to pass
3. **REFACTOR:** Improve code while tests pass
4. **REPEAT:** For each feature

**Evidence:**

- Test files created before implementation
- Git commits show test-first approach
- All tests pass after each feature
- No implementation without tests

**Exceptions:**

- Legacy code can have tests added after
- Non-critical refactoring can be done with tests after

---

## 9. Security Requirements

### 9.1 Authentication

**Admin Endpoints:**

- Require valid API key
- Verify API key middleware active
- Return 401 Unauthorized for invalid keys

**Public Endpoints:**

- No authentication required
- Rate limiting active
- Security headers active

---

### 9.2 Authorization

**Admin Operations:**

- Only users with admin API key can access
- Admin endpoints: create, update, delete products

**Public Operations:**

- Read-only operations allowed
- Search, list, detail endpoints

---

### 9.3 Input Validation

**Request Validation:**

- Pydantic v2 DTOs validate request bodies
- FastAPI Query() validates query params
- Type coercion for all inputs

**Response Validation:**

- Pydantic response models validate responses
- Type-safe serialization
- No data leakage in errors

---

### 9.4 SQL Injection Prevention

**Database Access:**

- SQLAlchemy ORM only (parameterized queries)
- No raw SQL concatenation
- Validate inputs before queries

**Evidence:**

- SQL injection tests pass
- ORM query analysis
- Code review for raw SQL

---

## 10. Dependencies

### 10.1 External Dependencies

**Required:**

- FastAPI `Depends()` (native)
- SQLAlchemy 2.0.51 (already upgraded)
- Pydantic v2 (already using)
- pytest (testing framework)

**Not Required:**

- ❌ dependency-injector (rejected, using FastAPI native)
- ❌ Other DI frameworks (overkill)

---

### 10.2 Internal Dependencies

**Fase 3.4 Depends On:**

- ✅ Fase 3.1: Domain Layer (completed)
- ✅ Fase 3.2: Infrastructure Layer (completed)
- ✅ Fase 3.3: Application Layer (completed)
- ✅ BC3 Suite integration working

**Fase 3.5 Depends On:**

- ✅ Fase 3.4: DI Configuration (prerequisite)
- ✅ Service tests fixed
- ✅ HTTP layer created

---

## 11. Out of Scope

### 11.1 Not in Current Scope

❌ **Fase 3.6:** Migrate remaining routers (familias, bc3)  
❌ **Fase 3.7:** Cleanup legacy code  
❌ Database schema changes (using productos_clean view)  
❌ New features (refactoring existing only)  
❌ Performance optimization (maintain current response times)  
❌ Caching implementation (architecture supports it, not in scope)  

---

## 12. Sign-off

### 12.1 Approval Required

**Reviewers:**

- [ ] Technical Lead
- [ ] Product Owner
- [ ] QA Lead

**Acceptance:**

- [ ] All functional requirements satisfied
- [ ] All non-functional requirements satisfied
- [ ] All acceptance criteria met
- [ ] All tests passing
- [ ] Performance benchmarks met
- [ ] BC3 Suite compatibility verified

---

**End of Specification**
