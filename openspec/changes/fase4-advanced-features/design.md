# Fase 4.2 - Advanced Features: Design Document

## Design Overview

Detailed technical design for implementing pagination, sorting, and advanced filtering for API-DISANO following hexagonal architecture principles.

**Change ID:** fase4-advanced-features  
**Phase:** Fase 4.2 - Design  
**Version:** 1.0  
**Status:** Draft

---

## 1. Architecture Design

### 1.1 Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    HTTP Layer (Interfaces)                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  FastAPI Routers (productos.py, familias.py, bc3.py) │  │
│  │  - V2 endpoints: /api/*/v2/* (pagination + filtering)│  │
│  │  - V1 endpoints: /api/*/list (backward compatible)   │  │
│  │  - V1ToV2Adapter: Adapt V1 params to V2 DTOs        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Application Layer (DTOs)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  app/application/dto/pagination/                     │  │
│  │  - PaginationRequestDTO: Input validation             │  │
│  │  - PaginatedResponseDTO: Output formatting           │  │
│  │  - SortCriteria: Sort field + order validation      │  │
│  │  - FilterCriteria: Advanced filters validation      │  │
│  │  - PaginationMetadata: Response metadata calculation │  │
│  │  - V1ToV2Adapter: V1/V2 compatibility layer         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Domain Layer (Services)                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  app/domain/services/                               │  │
│  │  - ProductoService.buscar_productos_paginado()      │  │
│  │  - FamiliaService.buscar_familias_paginado()        │  │
│  │  - Business logic + domain rules                    │  │
│  │  - Entity to DTO conversion                         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│               Infrastructure Layer (Repositories)             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  app/infrastructure/repositories/                    │  │
│  │  - SQLAlchemyProductoRepository: DB queries          │  │
│  │  - SQLAlchemyFamiliaRepository: DB queries           │  │
│  │  - _apply_filters(): Filter chain                   │  │
│  │  - _apply_sorting(): Order by logic                 │  │
│  │  - _apply_text_search(): ILIKE patterns             │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  app/infrastructure/cache/                          │  │
│  │  - PaginationCache: Cache layer for paginated       │  │
│  │  - CacheManager: Fase 4.1 cache infrastructure      │  │
│  │  - Cache invalidation pattern-based                 │  │
│  │  - Cache warming for popular queries                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Database Layer (SQLAlchemy)                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  productos_clean, familias_clean tables              │  │
│  │  - Additional indexes for performance               │  │
│  │  - Query optimization                                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Data Flow

```
1. HTTP Request → FastAPI Router
   ↓
2. Query Params → PaginationRequestDTO (validation)
   ↓
3. DTO → Service.buscar_*_paginado() (business logic)
   ↓
4. Service → Repository.buscar_*_paginado() (data access)
   ↓
5. Repository → Cache.get(cache_key) (check cache)
   ↓
6a. Cache Hit → Return cached data
   ↓
6b. Cache Miss → Execute DB query → Cache.set(cache_key)
   ↓
7. DB Results → Entities (domain models)
   ↓
8. Entities → DTOs (application models)
   ↓
9. DTOs → PaginatedResponseDTO (metadata + items)
   ↓
10. Response → JSON serialization
   ↓
11. HTTP Response → Client
```

### 1.3 Dependency Injection Chain

```python
# app/main.py (DI configuration)

# 1. Database session
def get_db_session():
    """Get database session with proper scoping"""
    with SessionLocal() as session:
        yield session

# 2. Cache manager
def get_cache_manager():
    """Get cache manager from Fase 4.1"""
    return CacheManager()

# 3. Cache wrapper for pagination
def get_pagination_cache(cache_manager: CacheManager = Depends(get_cache_manager)):
    """Get pagination cache wrapper"""
    return PaginationCache(cache_manager)

# 4. Repository implementation
def get_producto_repository(
    session: Session = Depends(get_db_session),
    pagination_cache: PaginationCache = Depends(get_pagination_cache)
):
    """Get product repository with caching"""
    return SQLAlchemyProductoRepository(session, pagination_cache)

# 5. Domain service
def get_producto_service(
    repository: ProductoRepository = Depends(get_producto_repository)
):
    """Get product domain service"""
    return ProductoService(repository)

# 6. HTTP endpoints receive service via Depends()
@router.get("/v2/list")
async def buscar_productos_v2_paginado(
    service: ProductoService = Depends(get_producto_service),
    # ... query params
):
    return service.buscar_productos_paginado(dto)
```

---

## 2. Component Design

### 2.1 DTO Package Design

#### Package Structure

```
app/application/dto/pagination/
├── __init__.py                    # Exports all DTOs
├── pagination_request.py          # PaginationRequestDTO
├── pagination_response.py         # PaginatedResponseDTO, PaginationMetadata
├── sort_criteria.py               # SortCriteria
├── filter_criteria.py            # FilterCriteria
└── v1_adapter.py                 # V1ToV2Adapter
```

#### Key Design Decisions

**Single Responsibility**: Each DTO has one clear purpose

- `PaginationRequestDTO`: Input validation + pagination logic
- `PaginatedResponseDTO`: Output formatting
- `PaginationMetadata`: Metadata calculation only
- `SortCriteria`: Sort validation only
- `FilterCriteria`: Filter validation only
- `V1ToV2Adapter`: Compatibility layer only

**Pydantic Advantages**:

- Automatic validation
- Type hints enforcement
- JSON serialization/deserialization
- Schema generation for OpenAPI
- Built-in error messages

**DTO Validation Flow**:

```python
# HTTP Query Params → FastAPI → Pydantic → DTO → Validation Error OR Valid DTO
GET /api/productos/v2/list?page=0&per_page=200
                                ↓
                        ValidationError (page must be ≥ 1)
                        ValidationError (per_page must be ≤ 100)
```

### 2.2 Repository Implementation Design

#### Repository Method Signature

```python
def buscar_productos_paginado(
    self,
    dto: PaginationRequestDTO
) -> tuple[list[ProductoEntity], int]:
    """
    Returns: (entities_for_current_page, total_count)
    
    Why return tuple instead of dict?
    - Type-safe: tuple[list[Entity], int] vs dict with dynamic keys
    - Clearer: first element is items, second is total
    - Efficient: No intermediate dict creation
    - Compatible: Works with entity conversion
    """
```

#### Query Building Strategy

**Strategy**: SQLAlchemy filter chain with lazy evaluation

```python
# Good: Lazy evaluation, single query
query = self.session.query(ProductoModel)

# Apply filters (chained, not executed yet)
if dto.filters:
    query = self._apply_filters(query, dto.filters)

# Apply sorting (chained, not executed yet)
query = self._apply_sorting(query, dto.parse_sort_criteria())

# Get total count BEFORE pagination (one query)
total_count = query.count()  # Executes COUNT(*)

# Apply pagination (chained, not executed yet)
query = query.offset(dto.offset).limit(dto.per_page)

# Execute final query (second query)
models = query.all()  # Executes SELECT ... LIMIT ... OFFSET ...
```

**Performance**: 2 queries per request

1. `SELECT COUNT(*) FROM ... WHERE ...` (for total_count)
2. `SELECT * FROM ... WHERE ... ORDER BY ... LIMIT ... OFFSET ...` (for items)

**Why not execute COUNT separately?**

- COUNT is expensive on large datasets
- We can cache COUNT results separately
- We can estimate COUNT for huge datasets (future optimization)

### 2.3 Cache Integration Design

#### Cache Key Strategy

**Challenge**: How to generate consistent cache keys for identical queries?

**Solution**: Hash-based cache key from complete DTO

```python
def generate_cache_key(dto: PaginationRequestDTO, entity_type: str) -> str:
    """
    Generate cache key from DTO hash
    
    Why hash instead of concatenation?
    - Consistent ordering: JSON dict keys sorted
    - Length-limited: MD5 hash is always 32 chars
    - Collision-resistant: MD5 is sufficient for cache keys
    - Fast: MD5 is fast to compute
    - Debuggable: Can reconstruct from hash if needed
    """
    key_data = {
        "entity": entity_type,
        "page": dto.page,
        "per_page": dto.per_page,
        "sort": dto.sort,
        "filters": dto.filters.model_dump() if dto.filters else None,
    }
    
    # JSON with sorted keys for consistency
    key_str = json.dumps(key_data, sort_keys=True)
    
    # MD5 hash (32 characters, hex string)
    hash_hex = hashlib.md5(key_str.encode()).hexdigest()
    
    # Final cache key: pag:producto:1a2b3c4d5e6f7g8h9i0j...
    return f"pag:{entity_type}:{hash_hex}"
```

**Cache Key Examples**:

- `pag:producto:8f434346648f6b96df89dda901c5176b10d6d8f61` (page=1, per_page=20)
- `pag:producto:a8f5f167f44f4964e6c998dee827110c4371d95d5` (page=2, per_page=20, sort=precio:desc)
- `pag:familia:b14a7b8059d9c055954c92674ce60032c9bf41ff9` (entity=familia)

#### Cache Data Structure

```python
# Cached data format
{
    "items": [  # List of entities (as dicts or entities)
        {
            "codigo": "P001",
            "descripcion": "LED Panel",
            # ... other fields
        },
        # ... more items
    ],
    "total": 150  # Total count for metadata
}
```

**Why cache items + total together?**

- Atomic: Either both cached or both not cached
- Consistent: total matches items when cache was built
- Simple: Single cache.get() returns complete data
- Efficient: No second cache lookup for total

#### Cache Invalidation Strategy

**Challenge**: When to invalidate cached pagination results?

**Solution**: Pattern-based invalidation on writes

```python
class ProductoService:
    def actualizar_producto(self, codigo: str, dto: ProductoUpdateDTO):
        """Update product with cache invalidation"""
        
        # 1. Update database
        producto = self.repository.update(codigo, dto)
        
        # 2. Invalidate ALL product pagination cache
        # Why invalidate all? Because any product change could affect ANY query
        # Alternative: Track which queries include this product (complex)
        self.cache.invalidate_pattern("pag:producto:*")
        
        return producto
    
    def crear_producto(self, dto: ProductoCreateDTO):
        """Create product with cache invalidation"""
        
        # 1. Create in database
        producto = self.repository.create(dto)
        
        # 2. Invalidate ALL product pagination cache
        self.cache.invalidate_pattern("pag:producto:*")
        
        return producto
    
    def eliminar_producto(self, codigo: str):
        """Delete product with cache invalidation"""
        
        # 1. Delete from database
        self.repository.delete(codigo)
        
        # 2. Invalidate ALL product pagination cache
        self.cache.invalidate_pattern("pag:producto:*")
        
        return True
```

**Why invalidate all instead of selective?**

- Simplicity: No complex tracking logic
- Correctness: Guaranteed no stale cache
- Performance: Pattern invalidation is fast
- TTL: Cache expires anyway (5 min)

**Cache Warming Strategy**:

```python
def warm_popular_queries(cache: PaginationCache, repository: ProductoRepository):
    """Warm cache for frequently accessed queries on startup"""
    
    popular_queries = [
        PaginationRequestDTO(page=1, per_page=20),  # First page, no filters
        PaginationRequestDTO(
            page=1,
            per_page=20,
            filters=FilterCriteria(marca="Disano")
        ),  # Disano products
        PaginationRequestDTO(
            page=1,
            per_page=20,
            filters=FilterCriteria(marca="Fosnova")
        ),  # Fosnova products
        PaginationRequestDTO(
            page=1,
            per_page=20,
            sort="precio:desc"
        ),  # Sorted by price
    ]
    
    for query in popular_queries:
        cache_key = cache.generate_cache_key(query)
        if not cache.get(cache_key):
            # Cache miss - execute query and cache result
            items, total = repository.buscar_productos_paginado(query)
            cache.set(cache_key, {"items": items, "total": total}, ttl=600)  # 10 min
```

### 2.4 HTTP Layer Design

#### V2 Endpoint Design

**Endpoint Pattern**: `/api/{entity}/v2/{action}`

```python
@router.get("/v2/list", response_model=PaginatedResponseDTO)
async def buscar_productos_v2_paginado(
    # Pagination parameters
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    
    # Sorting parameter
    sort: Optional[str] = Query(
        None,
        description="Sort criteria (e.g., 'precio:desc'). "
                    "Fields: codigo, descripcion, marca, familia, pvp, "
                    "bc3_descripcion_corta, bc3_product_type"
    ),
    
    # Filter parameters
    marca: Optional[str] = Query(None, description="Filter by brand"),
    familia: Optional[str] = Query(None, description="Filter by family"),
    pvp_min: Optional[float] = Query(None, ge=0, description="Min price"),
    pvp_max: Optional[float] = Query(None, ge=0, description="Max price"),
    bc3_product_type: Optional[str] = Query(None, description="BC3 type"),
    bc3_has_descripcion_corta: Optional[bool] = Query(
        None,
        description="Filter by presence/absence of short description"
    ),
    buscar: Optional[str] = Query(
        None,
        min_length=1,
        description="Search term (case-insensitive)"
    ),
    
    # Dependency injection
    service: ProductoService = Depends(get_producto_service),
):
    """
    Search products with advanced pagination, sorting, and filtering.
    
    ## Features
    - **Pagination**: Navigate large result sets with page/per_page
    - **Sorting**: Order results by any field (asc/desc)
    - **Advanced Filtering**: Filter by brand, family, price range, BC3 fields
    - **Text Search**: Full-text search across multiple fields
    
    ## Examples
    
    Get first page of Disano products:
    ```
    GET /api/productos/v2/list?page=1&per_page=20&marca=Disano
    ```
    
    Sort by price descending:
    ```
    GET /api/productos/v2/list?sort=precio:desc
    ```
    
    Filter by price range:
    ```
    GET /api/productos/v2/list?pvp_min=50&pvp_max=200
    ```
    
    BC3 columnas only:
    ```
    GET /api/productos/v2/list?bc3_product_type=columna
    ```
    """
    
    # Build DTO from query params
    filters = FilterCriteria(
        marca=marca,
        familia=familia,
        pvp_min=pvp_min,
        pvp_max=pvp_max,
        bc3_product_type=bc3_product_type,
        bc3_has_descripcion_corta=bc3_has_descripcion_corta,
        buscar=buscar
    )
    
    dto = PaginationRequestDTO(
        page=page,
        per_page=per_page,
        sort=sort,
        filters=filters
    )
    
    # Execute query
    result = service.buscar_productos_paginado(dto)
    
    return result
```

#### V1 Endpoint Design (Backward Compatible)

**Strategy**: Maintain V1 signature, use V2 logic internally

```python
@router.get("/list", response_model=List[ProductoResponseDTO])
async def listar_productos_v1(
    # V1 parameters (unchanged signature)
    buscar: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=500),  # V1 allowed 500
    marca: Optional[str] = Query(None),
    familia: Optional[str] = Query(None),
    
    # Dependency injection
    service: ProductoService = Depends(get_producto_service),
):
    """
    V1 endpoint - backward compatible.
    
    Uses V2 pagination logic internally but returns V1 format.
    """
    
    # Adapt V1 params to V2 DTO
    v2_dto = V1ToV2Adapter.adapt_request(
        limit=limit,
        buscar=buscar,
        marca=marca,
        familia=familia
    )
    
    # Use V2 service method
    paginated_result = service.buscar_productos_paginado(v2_dto)
    
    # Return V1 format (just the items, no metadata)
    return V1ToV2Adapter.adapt_response(paginated_result)
```

#### Error Handling Design

**Strategy**: Detailed error responses for debugging

```python
from fastapi import HTTPException, status

@router.get("/v2/list", response_model=PaginatedResponseDTO)
async def buscar_productos_v2_paginado(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    sort: Optional[str] = Query(None, description="Sort criteria"),
    # ... other params
    service: ProductoService = Depends(get_producto_service),
):
    try:
        # Build DTO from query params
        filters = FilterCriteria(
            marca=marca,
            familia=familia,
            pvp_min=pvp_min,
            pvp_max=pvp_max,
            bc3_product_type=bc3_product_type,
            bc3_has_descripcion_corta=bc3_has_descripcion_corta,
            buscar=buscar
        )
        
        dto = PaginationRequestDTO(
            page=page,
            per_page=per_page,
            sort=sort,
            filters=filters
        )
        
        # Execute query
        result = service.buscar_productos_paginado(dto)
        
        return result
        
    except ValidationError as e:
        # Pydantic validation error (e.g., invalid sort field)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(e),
                    "details": e.errors()
                }
            }
        )
        
    except Exception as e:
        # Unexpected error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": str(e) if DEBUG else None
                }
            }
        )
```

---

## 3. Database Design

### 3.1 Index Design

#### Index Strategy

**Principle**: Index fields that are frequently filtered, sorted, or joined

```sql
-- 1. Single-column indexes for frequently filtered fields
CREATE INDEX IF NOT EXISTS idx_productos_marca 
ON productos_clean(marca);

CREATE INDEX IF NOT EXISTS idx_productos_familia 
ON productos_clean(familia);

CREATE INDEX IF NOT EXISTS idx_productos_pvp 
ON productos_clean(pvp);

CREATE INDEX IF NOT EXISTS idx_productos_bc3_type 
ON productos_clean(bc3_product_type);

-- 2. Composite indexes for common filter combinations
CREATE INDEX IF NOT EXISTS idx_productos_marca_familia 
ON productos_clean(marca, familia);

CREATE INDEX IF NOT EXISTS idx_productos_marca_pvp 
ON productos_clean(marca, pvp);

-- 3. Index for text search (if supported)
-- SQLite FTS5 for full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS productos_fts 
USING fts5(
    codigo,
    descripcion,
    descripcion_corta,
    bc3_descripcion_corta,
    bc3_descripcion_completa,
    content=productos_clean,
    content_rowid=rowid
);

-- Triggers to keep FTS table in sync
CREATE TRIGGER IF NOT EXISTS productos_fts_insert 
AFTER INSERT ON productos_clean 
BEGIN
    INSERT INTO productos_fts(
        rowid,
        codigo,
        descripcion,
        descripcion_corta,
        bc3_descripcion_corta,
        bc3_descripcion_completa
    ) VALUES (
        NEW.rowid,
        NEW.codigo,
        NEW.descripcion,
        NEW.descripcion_corta,
        NEW.bc3_descripcion_corta,
        NEW.bc3_descripcion_completa
    );
END;

CREATE TRIGGER IF NOT EXISTS productos_fts_update 
AFTER UPDATE ON productos_clean 
BEGIN
    UPDATE productos_fts SET
        codigo = NEW.codigo,
        descripcion = NEW.descripcion,
        descripcion_corta = NEW.descripcion_corta,
        bc3_descripcion_corta = NEW.bc3_descripcion_corta,
        bc3_descripcion_completa = NEW.bc3_descripcion_completa
    WHERE rowid = NEW.rowid;
END;

CREATE TRIGGER IF NOT EXISTS productos_fts_delete 
AFTER DELETE ON productos_clean 
BEGIN
    DELETE FROM productos_fts WHERE rowid = OLD.rowid;
END;
```

#### Index Performance Analysis

```sql
-- Analyze indexes after creation
ANALYZE;

-- Check index usage (requires SQLite pragmas)
PRAGMA index_list('productos_clean');

-- Check index size
SELECT 
    name,
    tbl_name,
    sql
FROM sqlite_master
WHERE type = 'index' 
AND tbl_name = 'productos_clean';
```

### 3.2 Query Optimization

#### Query Execution Plan

```python
# Enable query analysis
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()
    print("\n=== QUERY ===")
    print(statement)
    print("Parameters:", parameters)

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    print("=== END QUERY ({}s) ===".format(total))
```

#### Query Optimization Techniques

**1. Eager Loading for Joins**:

```python
# Good: Eager load related entities
query = self.session.query(ProductoModel).options(
    joinedload(ProductoModel.familia)
)

# Bad: Lazy loading (N+1 problem)
query = self.session.query(ProductoModel)
# Each familia loaded separately later
```

**2. Select Only Needed Columns**:

```python
# Good: Select only needed columns
query = self.session.query(
    ProductoModel.codigo,
    ProductoModel.descripcion,
    ProductoModel.marca
)

# Bad: Select all columns
query = self.session.query(ProductoModel)
```

**3. Use EXISTS Instead of IN for Subqueries**:

```python
# Good: EXISTS (stops at first match)
query = query.filter(
    exists().where(
        and_(
            FamiliaModel.codigo == ProductoModel.familia,
            FamiliaModel.descripcion == "Iluminación"
        )
    )
)

# Bad: IN (evaluates entire subquery)
query = query.filter(
    ProductoModel.familia.in_(
        [f.codigo for f in familia_query.all()]
    )
)
```

---

## 4. Testing Design

### 4.1 Test Pyramid

```
        E2E Tests (5%)
        ┌─────────────┐
       /             \ E2E testing of
      /  Acceptance   \ complete workflows
     /________________\ (using TestClient)
    /                  \______________________
   /    Integration Tests (30%)              \ 
  /  ┌─────────────────────────────────┐     \
 /   │ Repository + Service + Cache       │    \
/    │ - Real database (test DB)          │     \
│    │ - Real cache (in-memory)            │     │
│    │ - End-to-end query execution       │     │
│    └─────────────────────────────────────┘     │
│                                                    │
│    Unit Tests (65%)                                │
│    ┌─────────────────────────────────┐             │
│    │ DTO validation tests             │             │
│    │ - Pydantic validation            │             │
│    │ - Offset calculation             │             │
│    │ - Metadata calculation            │             │
│    │                                 │             │
│    │ Repository method tests          │             │
│    │ - Filter chain building          │             │
│    │ - Sort order application         │             │
│    │ - Text search pattern matching    │             │
│    │                                 │             │
│    │ Service layer tests              │             │
│    │ - Domain rules                   │             │
│    │ - Entity conversion              │             │
│    │ - Cache integration              │             │
│    └─────────────────────────────────────┘         │
│                                                    │
└────────────────────────────────────────────────────┘
```

### 4.2 Test Data Design

#### Fixture Strategy

```python
# tests/conftest.py

@pytest.fixture
def test_database():
    """Create in-memory test database"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    # Create test data
    yield session
    
    session.close()
    engine.dispose()

@pytest.fixture
def sample_productos(test_database):
    """Create sample products for testing"""
    productos = [
        ProductoModelClean(
            codigo="P001",
            descripcion="LED Panel 600x600",
            marca="Disano",
            familia="Iluminación",
            pvp=89.99,
            bc3_descripcion_corta="Panel LED",
            bc3_product_type="columna"
        ),
        ProductoModelClean(
            codigo="P002",
            descripcion="LED Downlight",
            marca="Disano",
            familia="Iluminación",
            pvp=45.50,
            bc3_descripcion_corta="Downlight",
            bc3_product_type="columna"
        ),
        ProductoModelClean(
            codigo="P003",
            descripcion="LED Strip",
            marca="Fosnova",
            familia="Iluminación",
            pvp=29.99,
            bc3_descripcion_corta="Tira LED",
            bc3_product_type="columna"
        ),
    ]
    
    test_database.add_all(productos)
    test_database.commit()
    
    return productos

@pytest.fixture
def pagination_cache():
    """Create in-memory cache for testing"""
    from app.infrastructure.cache.cache_manager import CacheManager
    
    cache_manager = CacheManager()
    return PaginationCache(cache_manager)
```

### 4.3 Test Case Design

#### Unit Test Example

```python
# tests/unit/application/dto/test_pagination_request.py

def test_pagination_request_default_values():
    """Test default values for pagination request"""
    dto = PaginationRequestDTO()
    
    assert dto.page == 1
    assert dto.per_page == 20
    assert dto.sort is None
    assert dto.offset == 0

def test_pagination_request_offset_calculation():
    """Test offset calculation from page and per_page"""
    dto = PaginationRequestDTO(page=3, per_page=10)
    
    assert dto.offset == 20  # (3-1) * 10

def test_pagination_request_page_validation():
    """Test that page < 1 raises ValidationError"""
    with pytest.raises(ValidationError) as exc_info:
        PaginationRequestDTO(page=0, per_page=20)
    
    errors = exc_info.value.errors()
    assert any(e["field"] == "page" and "greater than or equal to 1" in str(e["msg"]) for e in errors)

def test_pagination_request_per_page_validation():
    """Test that per_page > 100 raises ValidationError"""
    with pytest.raises(ValidationError) as exc_info:
        PaginationRequestDTO(page=1, per_page=101)
    
    errors = exc_info.value.errors()
    assert any(e["field"] == "per_page" and "less than or equal to 100" in str(e["msg"]) for e in errors)
```

#### Integration Test Example

```python
# tests/integration/repositories/test_producto_pagination.py

def test_repository_pagination_with_filters(sample_productos, test_database):
    """Test repository pagination with filters applied"""
    repo = SQLAlchemyProductoRepository(test_database)
    
    dto = PaginationRequestDTO(
        page=1,
        per_page=10,
        filters=FilterCriteria(marca="Disano", pvp_min=50)
    )
    
    items, total = repo.buscar_productos_paginado(dto)
    
    assert len(items) <= 10
    assert total >= len(items)
    for item in items:
        assert item.marca == "Disano"
        assert item.pvp >= 50

def test_repository_sorting(sample_productos, test_database):
    """Test repository sorting by price descending"""
    repo = SQLAlchemyProductoRepository(test_database)
    
    dto = PaginationRequestDTO(
        page=1,
        per_page=10,
        sort="precio:desc"
    )
    
    items, _ = repo.buscar_productos_paginado(dto)
    
    # Verify sorting
    prices = [item.pvp for item in items]
    assert prices == sorted(prices, reverse=True)

def test_repository_text_search(sample_productos, test_database):
    """Test repository text search"""
    repo = SQLAlchemyProductoRepository(test_database)
    
    dto = PaginationRequestDTO(
        page=1,
        per_page=10,
        filters=FilterCriteria(buscar="LED")
    )
    
    items, _ = repo.buscar_productos_paginado(dto)
    
    # Verify text search
    assert len(items) >= 2  # At least 2 products have "LED"
    for item in items:
        # Search is case-insensitive
        assert any("led" in field.lower() for field in [
            item.descripcion,
            item.descripcion_corta or "",
            item.bc3_descripcion_corta or ""
        ])
```

#### Acceptance Test Example

```python
# tests/acceptance/test_pagination_endpoints.py

async def test_v2_pagination_endpoint(client, sample_productos):
    """Test V2 pagination endpoint"""
    response = await client.get(
        "/api/productos/v2/list?page=1&per_page=2&sort=precio:desc"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "items" in data
    assert "pagination" in data
    assert "filters_applied" in data
    assert "sorting_applied" in data
    
    # Verify pagination metadata
    pagination = data["pagination"]
    assert pagination["total_items"] >= 3
    assert pagination["current_page"] == 1
    assert pagination["per_page"] == 2
    assert pagination["total_pages"] >= 2
    assert len(data["items"]) == 2
    
    # Verify sorting applied
    sorting = data["sorting_applied"]
    assert sorting["field"] == "precio"
    assert sorting["order"] == "desc"

async def test_v1_backward_compatibility(client, sample_productos):
    """Test V1 backward compatibility"""
    response_v1 = await client.get(
        "/api/productos/list?limit=2&marca=Disano"
    )
    
    response_v2 = await client.get(
        "/api/productos/v2/list?per_page=2&marca=Disano"
    )
    
    # Both should return same items
    assert response_v1.status_code == 200
    assert response_v2.status_code == 200
    
    items_v1 = response_v1.json()
    items_v2 = response_v2.json()["items"]
    
    assert len(items_v1) == len(items_v2)
    assert [item["codigo"] for item in items_v1] == [item["codigo"] for item in items_v2]

async def test_advanced_filtering_endpoint(client, sample_productos):
    """Test advanced filtering endpoint"""
    response = await client.get(
        "/api/productos/v2/list?"
        "marca=Disano&"
        "pvp_min=40&"
        "pvp_max=100&"
        "bc3_product_type=columna"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify all filters applied
    filters_applied = data["filters_applied"]
    assert filters_applied["marca"] == "Disano"
    assert filters_applied["pvp_min"] == 40.0
    assert filters_applied["pvp_max"] == 100.0
    assert filters_applied["bc3_product_type"] == "columna"
    
    # Verify results match filters
    for item in data["items"]:
        assert item["marca"] == "Disano"
        assert 40.0 <= item["pvp"] <= 100.0
        assert item["bc3_product_type"] == "columna"
```

---

## 5. Performance Design

### 5.1 Performance Targets

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| P95 Response Time | < 200ms | pytest-performance plugin |
| P99 Response Time | < 500ms | pytest-performance plugin |
| COUNT Query Time | < 50ms | SQLAlchemy query logging |
| Cache Hit Rate | > 50% | Cache statistics tracking |
| Memory Usage | < 100MB | memory_profiler |
| Database Query Time | < 100ms | SQLAlchemy query logging |

### 5.2 Performance Monitoring

#### Query Performance Tracking

```python
from time import time
from functools import wraps

def track_query_performance(func):
    """Decorator to track query performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time()
        result = func(*args, **kwargs)
        end_time = time()
        
        execution_time = (end_time - start_time) * 1000  # Convert to ms
        
        # Log performance (in real app, send to metrics service)
        print(f"{func.__name__}: {execution_time:.2f}ms")
        
        # Alert on slow queries
        if execution_time > 200:  # P95 target
            print(f"WARNING: Slow query {func.__name__}: {execution_time:.2f}ms")
        
        return result
    
    return wrapper

class SQLAlchemyProductoRepository(ProductoRepositoryInterface):
    
    @track_query_performance
    def buscar_productos_paginado(
        self,
        dto: PaginationRequestDTO
    ) -> tuple[list[ProductoEntity], int]:
        # ... implementation
        pass
```

#### Cache Performance Tracking

```python
from collections import defaultdict

class CacheStatistics:
    """Track cache performance"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.total_queries = 0
    
    def record_hit(self):
        self.hits += 1
        self.total_queries += 1
    
    def record_miss(self):
        self.misses += 1
        self.total_queries += 1
    
    @property
    def hit_rate(self) -> float:
        if self.total_queries == 0:
            return 0.0
        return self.hits / self.total_queries
    
    def reset(self):
        self.hits = 0
        self.misses = 0
        self.total_queries = 0

class PaginationCache:
    def __init__(self, cache_backend: CacheManager):
        self.cache = cache_backend
        self.stats = CacheStatistics()
    
    def get(self, cache_key: str) -> Optional[dict]:
        result = self.cache.get(cache_key)
        if result:
            self.stats.record_hit()
        else:
            self.stats.record_miss()
        return result
    
    def get_statistics(self) -> dict:
        return {
            "hits": self.stats.hits,
            "misses": self.stats.misses,
            "total_queries": self.stats.total_queries,
            "hit_rate": self.stats.hit_rate
        }
```

---

## 6. Security Design

### 6.1 Input Validation

#### Multi-Layer Validation Strategy

```python
# Layer 1: FastAPI parameter validation
page: int = Query(1, ge=1, description="Page number")

# Layer 2: Pydantic DTO validation
class PaginationRequestDTO(BaseModel):
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)

# Layer 3: Domain rules validation
def buscar_productos_paginado(self, dto: PaginationRequestDTO):
    if dto.filters and dto.filters.pvp_min and dto.filters.pvp_max:
        if dto.filters.pvp_min > dto.filters.pvp_max:
            raise ValidationException(
                "pvp_range",
                "pvp_min cannot be greater than pvp_max"
            )
```

#### SQL Injection Prevention

```python
# Good: Parameterized queries (SQLAlchemy default)
query = query.filter(ProductoModel.marca == marca)

# Bad: String concatenation (NEVER DO THIS)
query = query.filter(f"marca = '{marca}'")  # SQL INJECTION VULNERABILITY

# Good: Parameterized text search
search_pattern = f"%{search_term}%"
query = query.filter(ProductoModel.descripcion.ilike(search_pattern))

# Bad: Unsanitized text search (NEVER DO THIS)
query = query.filter(f"descripcion LIKE '%{search_term}%'")  # SQL INJECTION VULNERABILITY
```

### 6.2 Data Protection

#### Sensitive Data Protection

```python
# Never expose internal errors in production
DEBUG = False  # Production setting

@router.get("/v2/list")
async def buscar_productos_v2_paginado(...):
    try:
        # ... logic
        pass
    except Exception as e:
        if DEBUG:
            # Development: Show full error details
            raise HTTPException(
                status_code=500,
                detail={"error": str(e), "traceback": traceback.format_exc()}
            )
        else:
            # Production: Generic error message
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Internal server error",
                    "code": "INTERNAL_ERROR"
                }
            )
```

#### Rate Limiting Strategy

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.get("/v2/list")
@limiter.limit("100/minute")  # 100 requests per minute per IP
async def buscar_productos_v2_paginado(
    request: Request,
    # ... params
):
    # ... implementation
    pass
```

---

## 7. Deployment Design

### 7.1 Database Migration Strategy

#### Migration Script

```python
# app/infrastructure/database/migrations/add_pagination_indexes.py

def add_pagination_indexes():
    """Add indexes for pagination performance"""
    
    from app.infrastructure.database.connection import get_engine
    from sqlalchemy import text
    
    engine = get_engine()
    
    with engine.connect() as conn:
        # Create indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_productos_marca 
            ON productos_clean(marca)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_productos_familia 
            ON productos_clean(familia)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_productos_pvp 
            ON productos_clean(pvp)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_productos_bc3_type 
            ON productos_clean(bc3_product_type)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_productos_marca_familia 
            ON productos_clean(marca, familia)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_productos_marca_pvp 
            ON productos_clean(marca, pvp)
        """))
        
        # Analyze indexes
        conn.execute(text("ANALYZE productos_clean"))
        
        conn.commit()

if __name__ == "__main__":
    add_pagination_indexes()
    print("Pagination indexes created successfully")
```

#### Rollback Strategy

```python
def rollback_pagination_indexes():
    """Rollback pagination indexes"""
    
    from app.infrastructure.database.connection import get_engine
    from sqlalchemy import text
    
    engine = get_engine()
    
    with engine.connect() as conn:
        indexes = [
            "idx_productos_marca",
            "idx_productos_familia",
            "idx_productos_pvp",
            "idx_productos_bc3_type",
            "idx_productos_marca_familia",
            "idx_productos_marca_pvp"
        ]
        
        for index in indexes:
            conn.execute(text(f"DROP INDEX IF EXISTS {index}"))
        
        conn.commit()

if __name__ == "__main__":
    rollback_pagination_indexes()
    print("Pagination indexes rolled back successfully")
```

### 7.2 Configuration Strategy

#### Environment Configuration

```python
# app/config/pagination.py

from pydantic_settings import BaseSettings

class PaginationConfig(BaseSettings):
    """Pagination configuration"""
    
    # Default pagination
    default_page: int = 1
    default_per_page: int = 20
    max_per_page: int = 100
    
    # Cache configuration
    cache_ttl: int = 300  # 5 minutes
    cache_warming_enabled: bool = True
    cache_warming_queries: list = []
    
    # Performance monitoring
    enable_performance_tracking: bool = True
    slow_query_threshold_ms: float = 200.0
    alert_on_slow_queries: bool = True
    
    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 100
    
    class Config:
        env_file = ".env"
        env_prefix = "PAGINATION_"

# Global config instance
pagination_config = PaginationConfig()
```

---

## 8. Implementation Phases

### Phase 1: Core DTOs + Repository Methods (2-3 hours)

**Deliverables**:

- DTO package structure created
- All DTOs implemented with validation
- Repository interface extended
- Repository implementation with filter/sorting/pagination
- Unit tests for DTOs and repository methods

**Tasks**:

1. Create `app/application/dto/pagination/` package
2. Implement `PaginationRequestDTO` with validation
3. Implement `PaginatedResponseDTO` and `PaginationMetadata`
4. Implement `SortCriteria` with field validation
5. Implement `FilterCriteria` with comprehensive filters
6. Extend `ProductoRepositoryInterface` with `buscar_productos_paginado()`
7. Implement `SQLAlchemyProductoRepository.buscar_productos_paginado()`
8. Implement `_apply_filters()`, `_apply_sorting()`, `_apply_text_search()`
9. Write unit tests for DTO validation
10. Write integration tests for repository methods

### Phase 2: Service Layer + Cache Integration (2 hours)

**Deliverables**:

- Domain service methods implemented
- Cache integration complete
- Cache invalidation strategy implemented
- Service layer tests passing
- Cache hit rate > 50%

**Tasks**:

1. Implement `ProductoService.buscar_productos_paginado()`
2. Create `PaginationCache` wrapper
3. Implement cache key generation logic
4. Implement cache invalidation in service methods
5. Implement cache warming strategy
6. Write integration tests for cache integration
7. Verify cache hit rate > 50%
8. Optimize cache TTL based on testing

### Phase 3: HTTP Layer + V1 Compatibility (2-3 hours)

**Deliverables**:

- V2 endpoints implemented
- V1 adapters implemented
- Backward compatibility tests passing
- Acceptance tests for all endpoints
- OpenAPI documentation complete

**Tasks**:

1. Implement V2 `/api/productos/v2/list` endpoint
2. Implement V2 `/api/familias/v2/list` endpoint
3. Implement V2 `/api/bc3/v2/list` endpoint
4. Implement `V1ToV2Adapter`
5. Adapt V1 endpoints to use V2 logic internally
6. Write acceptance tests for V2 endpoints
7. Write acceptance tests for V1 compatibility
8. Update OpenAPI documentation
9. Test V1 backward compatibility
10. Verify zero breaking changes

### Phase 4: Monitoring + Optimization (1-2 hours)

**Deliverables**:

- Performance monitoring implemented
- Database indexes optimized
- Cache tuned for production
- Documentation complete
- Production deployment ready

**Tasks**:

1. Implement query performance tracking
2. Implement cache statistics tracking
3. Create database migration script for indexes
4. Run database index creation
5. Optimize query performance based on profiling
6. Tune cache TTL based on real usage
7. Write deployment documentation
8. Create rollback procedures
9. Verify all performance targets met
10. Prepare production deployment checklist

---

## 9. Rollback Strategy

### 9.1 Code Rollback

**Git Rollback**:

```bash
# Rollback to last stable commit
git revert <commit_hash>

# Or rollback to specific commit
git reset --hard <commit_hash>
```

**Database Rollback**:

```bash
# Rollback indexes
python -m app.infrastructure.database.migrations.rollback_pagination_indexes

# Verify rollback
python -m app.infrastructure.database.migrations.verify_rollback
```

### 9.2 Feature Flags

**Feature Flag Strategy**:

```python
# app/config/feature_flags.py

class FeatureFlags:
    """Feature flags for gradual rollout"""
    
    PAGINATION_ENABLED = os.getenv("PAGINATION_ENABLED", "true").lower() == "true"
    V1_COMPATIBILITY_MODE = os.getenv("V1_COMPATIBILITY_MODE", "true").lower() == "true"
    CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"

# Usage in code
if FeatureFlags.PAGINATION_ENABLED:
    return service.buscar_productos_paginado(dto)
else:
    return service.buscar_productos_legacy()  # Fallback to old logic
```

---

## 10. Success Criteria

### 10.1 Functional Success

- [ ] All V2 endpoints return correct paginated results
- [ ] All V1 endpoints maintain backward compatibility
- [ ] Cache integration functional with hit rate > 50%
- [ ] Text search works across all specified fields
- [ ] Advanced filtering works correctly

### 10.2 Performance Success

- [ ] P95 response time < 200ms
- [ ] P99 response time < 500ms
- [ ] COUNT query performance < 50ms
- [ ] Memory usage < 100MB per query
- [ ] Cache hit rate > 50% for popular queries

### 10.3 Quality Success

- [ ] Test coverage > 80% for new code
- [ ] Zero mypy errors
- [ ] All existing tests still pass
- [ ] TDD methodology followed throughout

### 10.4 Architecture Success

- [ ] Hexagonal architecture maintained
- [ ] No direct database access in HTTP layer
- [ ] Dependency injection functional
- [ ] DTO pattern followed consistently

---

## 11. Monitoring & Observability

### 11.1 Key Metrics

**Performance Metrics**:

- P95 response time
- P99 response time
- COUNT query time
- Memory usage
- Database connection usage

**Cache Metrics**:

- Cache hit rate
- Cache miss rate
- Cache size
- Cache eviction rate

**Business Metrics**:

- Most common filters
- Most common sorting criteria
- Average page size requested
- Popular search terms

### 11.2 Alerting

**Alert Conditions**:

- P95 response time > 200ms
- Cache hit rate < 40%
- Memory usage > 100MB
- Database connection pool exhaustion

---

## 12. Documentation

### 12.1 API Documentation

**OpenAPI Specification**:

- Complete endpoint documentation
- Example queries for common use cases
- Error response schemas
- Deprecation notices for V1 endpoints

### 12.2 Developer Documentation

**Implementation Guide**:

- How to add pagination to new endpoints
- How to extend filtering capabilities
- How to tune cache configuration
- How to monitor performance

### 12.3 Operations Documentation

**Deployment Guide**:

- Database migration procedures
- Configuration options
- Monitoring setup
- Rollback procedures

---

**Design Version**: 1.0  
**Created**: 2026-07-12T13:00:00Z  
**Author**: el Gentleman (Pi Coding Agent)  
**Status**: 📝 Draft - Pending Approval  
**Next Phase**: Tasks (Implementation Breakdown)
