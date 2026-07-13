# Fase 4.2 - Advanced Features: Technical Specification

## Overview

Detailed technical specifications for implementing pagination, sorting, and advanced filtering for API-DISANO following hexagonal architecture principles and leveraging Fase 4.1 caching infrastructure.

**Change ID:** fase4-advanced-features  
**Phase:** Fase 4.2 - Specification  
**Version:** 1.0  
**Status:** Draft

---

## 1. Functional Requirements

### 1.1 Pagination System

#### FR-1.1.1: Pagination Request DTO

**Description**: Data Transfer Object for pagination requests with comprehensive validation.

**Requirements**:

- Supports `page` parameter (1-based, minimum 1)
- Supports `per_page` parameter (default 20, range 1-100)
- Validates that page ≥ 1
- Validates that 1 ≤ per_page ≤ 100
- Provides calculated `offset` property

**Technical Specifications**:

```python
class PaginationRequestDTO(BaseModel):
    page: int = Field(1, ge=1, description="Page number (1-based)")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page
```

**Acceptance Criteria**:

- [ ] Default page is 1
- [ ] Default per_page is 20
- [ ] Page values < 1 raise ValidationError
- [ ] Per_page values < 1 raise ValidationError
- [ ] Per_page values > 100 raise ValidationError
- [ ] Offset calculation is correct: (page-1) * per_page

#### FR-1.1.2: Pagination Metadata DTO

**Description**: Metadata DTO for pagination responses with navigation information.

**Requirements**:

- Includes total_items count
- Calculates total_pages from total_items and per_page
- Includes current_page number
- Includes per_page value
- Calculates has_next flag
- Calculates has_previous flag

**Technical Specifications**:

```python
class PaginationMetadata(BaseModel):
    total_items: int
    total_pages: int
    current_page: int
    per_page: int
    has_next: bool
    has_previous: bool
    
    @classmethod
    def from_query(cls, total_items: int, current_page: int, per_page: int) -> "PaginationMetadata":
        total_pages = (total_items + per_page - 1) // per_page
        return cls(
            total_items=total_items,
            total_pages=total_pages,
            current_page=current_page,
            per_page=per_page,
            has_next=current_page < total_pages,
            has_previous=current_page > 1,
        )
```

**Acceptance Criteria**:

- [ ] total_pages calculation correct for all edge cases
- [ ] has_next is False on last page
- [ ] has_next is True on all other pages
- [ ] has_previous is False on first page
- [ ] has_previous is True on all other pages
- [ ] Total pages = 0 when total_items = 0

#### FR-1.1.3: Paginated Response DTO

**Description**: Complete response DTO for paginated results with metadata and applied filters/sorting.

**Requirements**:

- Includes items array
- Includes pagination metadata
- Optionally includes filters_applied
- Optionally includes sorting_applied
- Supports multiple entity types (Producto, Familia)

**Technical Specifications**:

```python
class PaginatedResponseDTO(BaseModel):
    items: List[Any]
    pagination: PaginationMetadata
    filters_applied: Optional[dict] = None
    sorting_applied: Optional[dict] = None
```

**Acceptance Criteria**:

- [ ] items array is correctly typed
- [ ] pagination metadata is complete
- [ ] filters_applied matches input filters
- [ ] sorting_applied matches input sorting criteria
- [ ] Serialization to JSON works correctly

### 1.2 Sorting System

#### FR-1.2.1: Sort Criteria DTO

**Description**: DTO for sorting criteria with field validation and order normalization.

**Requirements**:

- Supports field specification
- Supports order specification (asc/desc)
- Validates field against whitelist
- Normalizes order to lowercase
- Provides default values

**Technical Specifications**:

```python
class SortCriteria(BaseModel):
    field: str
    order: str = "asc"
    
    @field_validator("order")
    @classmethod
    def normalize_order(cls, v: str) -> str:
        return v.lower()
    
    @field_validator("field")
    @classmethod
    def validate_field(cls, v: str) -> str:
        allowed_fields = [
            "codigo", "descripcion", "marca", "familia", 
            "pvp", "bc3_descripcion_corta", "bc3_product_type"
        ]
        if v not in allowed_fields:
            raise ValueError(f"Sort field must be one of: {allowed_fields}")
        return v
```

**Acceptance Criteria**:

- [ ] Order normalized to lowercase
- [ ] Invalid fields raise ValidationError
- [ ] Order values other than "asc"/"desc" rejected
- [ ] Default order is "asc"
- [ ] Field whitelist includes all database columns

#### FR-1.2.2: Multi-Sort Support

**Description**: Support for sorting by multiple fields in specified order.

**Requirements**:

- Parse multi-sort string (e.g., "marca:asc,familia:desc")
- Apply sorting in specified order
- Validate each field against whitelist
- Validate each order value

**Technical Specifications**:

```python
def parse_multi_sort(sort_string: str) -> List[SortCriteria]:
    """Parse multi-sort string into list of SortCriteria"""
    if not sort_string:
        return []
    
    criteria_list = []
    for part in sort_string.split(","):
        parts = part.strip().split(":")
        field = parts[0].strip()
        order = parts[1].strip().lower() if len(parts) > 1 else "asc"
        criteria_list.append(SortCriteria(field=field, order=order))
    
    return criteria_list
```

**Acceptance Criteria**:

- [ ] Single sort works correctly
- [ ] Multiple sort fields parsed correctly
- [ ] Invalid fields raise ValidationError
- [ ] Invalid order values raise ValidationError
- [ ] Empty string returns empty list
- [ ] Whitespace handled correctly

### 1.3 Advanced Filtering System

#### FR-1.3.1: Filter Criteria DTO

**Description**: Comprehensive DTO for advanced filtering with multiple filter types.

**Requirements**:

- Supports exact match filters (marca, familia)
- Supports range filters (pvp_min, pvp_max)
- Supports BC3-specific filters (bc3_product_type, bc3_has_descripcion_corta)
- Supports text search (buscar)
- Validates pvp_min ≤ pvp_max

**Technical Specifications**:

```python
class FilterCriteria(BaseModel):
    marca: Optional[str] = Field(None, max_length=50)
    familia: Optional[str] = Field(None, max_length=50)
    pvp_min: Optional[float] = Field(None, ge=0)
    pvp_max: Optional[float] = Field(None, ge=0)
    bc3_product_type: Optional[str] = Field(None)
    bc3_has_descripcion_corta: Optional[bool] = Field(None)
    buscar: Optional[str] = Field(None, min_length=1)
    
    @model_validator(mode="after")
    def validate_price_range(self) -> "FilterCriteria":
        if self.pvp_min is not None and self.pvp_max is not None:
            if self.pvp_min > self.pvp_max:
                raise ValueError("pvp_min cannot be greater than pvp_max")
        return self
```

**Acceptance Criteria**:

- [ ] All filter fields are optional
- [ ] pvp_min ≥ 0 enforced
- [ ] pvp_max ≥ 0 enforced
- [ ] pvp_min ≤ pvp_max enforced
- [ ] marca/familia max_length = 50
- [ ] buscar min_length = 1
- [ ] Empty filter values ignored in queries

#### FR-1.3.2: Text Search Implementation

**Description**: Case-insensitive text search across multiple fields using ILIKE patterns.

**Requirements**:

- Search across codigo, descripcion, descripcion_corta, bc3_descripcion_corta, bc3_descripcion_completa
- Case-insensitive matching
- Pattern matching using ILIKE
- OR logic between searched fields

**Technical Specifications**:

```python
def apply_text_search(query, search_pattern: str):
    """Apply text search to query"""
    pattern = f"%{search_pattern}%"
    return query.filter(
        or_(
            ProductoModel.codigo.ilike(pattern),
            ProductoModel.descripcion.ilike(pattern),
            ProductoModel.descripcion_corta.ilike(pattern),
            ProductoModel.bc3_descripcion_corta.ilike(pattern),
            ProductoModel.bc3_descripcion_completa.ilike(pattern),
        )
    )
```

**Acceptance Criteria**:

- [ ] Case-insensitive matching works
- [ ] Pattern matching works (e.g., "led" matches "LED Panel")
- [ ] OR logic between searched fields
- [ ] Empty search term returns all results
- [ ] Performance acceptable for large datasets

### 1.4 Backward Compatibility

#### FR-1.4.1: V1 to V2 Adapter

**Description**: Adapter for converting V1 request parameters to V2 DTOs.

**Requirements**:

- Convert V1 limit to V2 per_page
- Convert V1 buscar to V2 filter
- Convert V1 marca/familia to V2 filters
- Default page = 1
- Default per_page = limit or 10

**Technical Specifications**:

```python
class V1ToV2Adapter:
    @staticmethod
    def adapt_request(
        limit: int = 10,
        buscar: Optional[str] = None,
        marca: Optional[str] = None,
        familia: Optional[str] = None
    ) -> PaginationRequestDTO:
        filters = FilterCriteria(
            marca=marca,
            familia=familia,
            buscar=buscar
        )
        
        return PaginationRequestDTO(
            page=1,
            per_page=min(limit, 100),
            filters=filters
        )
    
    @staticmethod
    def adapt_response(response: PaginatedResponseDTO) -> List:
        """Convert V2 paginated response to V1 array format"""
        return response.items
```

**Acceptance Criteria**:

- [ ] V1 limit → V2 per_page correctly
- [ ] V1 limit > 100 clamped to 100
- [ ] V1 buscar → V2 filter correctly
- [ ] V1 marca/familia → V2 filters correctly
- [ ] Default values applied correctly

---

## 2. Non-Functional Requirements

### 2.1 Performance Requirements

#### NFR-2.1.1: Response Time Targets

- **P95 Response Time**: < 200ms for paginated queries
- **P99 Response Time**: < 500ms for paginated queries
- **COUNT Query Performance**: < 50ms
- **Memory Usage**: < 100MB per paginated query

#### NFR-2.1.2: Cache Performance Targets

- **Cache Hit Rate**: > 50% for popular queries
- **Cache TTL**: 5 minutes for paginated results
- **Cache Invalidation Time**: < 100ms on writes
- **Cache Warming Time**: < 5 seconds on startup

### 2.2 Caching Requirements

#### NFR-2.2.1: Cache Strategy

- **Cache Key Generation**: Based on complete DTO hash
- **Cache Storage**: Use Fase 4.1 CacheManager
- **Cache Pattern**: Pattern-based invalidation
- **Cache Warming**: Warm popular queries on startup

#### NFR-2.2.2: Cache Invalidation

- **Invalidation Trigger**: Product create/update/delete
- **Invalidation Pattern**: `pag:producto:*` for all product pagination
- **Invalidation TTL**: Immediate on writes
- **Cache Warm**: Re-warm popular queries after invalidation

### 2.3 Architecture Requirements

#### NFR-2.3.1: Hexagonal Architecture Compliance

- **Layer Separation**: No cross-layer dependencies
- **Dependency Inversion**: Infrastructure depends on domain interfaces
- **Dependency Injection**: All components injectable via FastAPI Depends()
- **DTO Pattern**: All input/output use DTOs

#### NFR-2.3.2: Testing Requirements

- **Test Coverage**: > 80% for new code
- **Test Types**: Unit, integration, acceptance tests
- **TDD Methodology**: RED → GREEN → REFACTOR
- **Zero Breaking Changes**: All existing tests must pass

### 2.4 Quality Requirements

#### NFR-2.4.1: Code Quality

- **Mypy Errors**: Zero mypy errors
- **Type Hints**: Complete type hints for new code
- **Code Style**: Follow existing project style
- **Documentation**: Docstrings for all public methods

#### NFR-2.4.2: API Quality

- **OpenAPI Documentation**: Complete for all new endpoints
- **Error Messages**: Clear and actionable
- **Response Format**: Consistent across all endpoints
- **HTTP Status Codes**: Correct for all scenarios

---

## 3. Technical Specifications

### 3.1 Domain Layer Specifications

#### 3.1.1: Repository Interface Extension

**File**: `app/domain/repositories/producto.py`

**Extension**: Add new method to `ProductoRepositoryInterface`

```python
@abstractmethod
def buscar_productos_paginado(
    self,
    dto: PaginationRequestDTO
) -> tuple[list[ProductoEntity], int]:
    """Search products with pagination, sorting, and filtering
    
    Args:
        dto: Complete pagination request DTO with filters and sorting
        
    Returns:
        tuple[list[ProductoEntity], int]: 
            - List of entities for current page
            - Total count of matching items
    """
    pass
```

**Requirements**:

- Abstract method signature defined
- Type hints complete
- Docstring comprehensive
- Returns tuple for efficient metadata retrieval

#### 3.1.2: Familia Repository Extension

**File**: `app/domain/repositories/familia.py`

**Extension**: Similar pagination method for families

```python
@abstractmethod
def buscar_familias_paginado(
    self,
    dto: PaginationRequestDTO
) -> tuple[list[FamiliaEntity], int]:
    """Search families with pagination, sorting, and filtering
    
    Args:
        dto: Complete pagination request DTO with filters and sorting
        
    Returns:
        tuple[list[FamiliaEntity], int]: 
            - List of entities for current page
            - Total count of matching items
    """
    pass
```

### 3.2 Application Layer Specifications

#### 3.2.1: DTO Package Structure

**Directory**: `app/application/dto/pagination/`

**Files**:

```
app/application/dto/pagination/
├── __init__.py
├── pagination_request.py
├── pagination_response.py
├── sort_criteria.py
├── filter_criteria.py
└── v1_adapter.py
```

#### 3.2.2: Pagination Request DTO

**File**: `app/application/dto/pagination/pagination_request.py`

```python
from pydantic import BaseModel, Field, field_validator

class PaginationRequestDTO(BaseModel):
    """DTO for pagination requests"""
    
    page: int = Field(1, ge=1, description="Page number (1-based)")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    sort: Optional[str] = Field(None, description="Sort criteria (e.g., 'precio:desc')")
    
    @property
    def offset(self) -> int:
        """Calculate offset from page and per_page"""
        return (self.page - 1) * self.per_page
    
    def parse_sort_criteria(self) -> SortCriteria:
        """Parse sort string into SortCriteria"""
        if not self.sort:
            return SortCriteria(field="codigo", order="asc")  # Default
        
        parts = self.sort.split(":")
        field = parts[0]
        order = parts[1] if len(parts) > 1 else "asc"
        
        return SortCriteria(field=field, order=order)
```

#### 3.2.3: Pagination Response DTO

**File**: `app/application/dto/pagination/pagination_response.py`

```python
from pydantic import BaseModel
from typing import List, Optional, Any

class PaginatedResponseDTO(BaseModel):
    """Complete response DTO for paginated results"""
    
    items: List[Any]
    pagination: PaginationMetadata
    filters_applied: Optional[dict] = None
    sorting_applied: Optional[dict] = None


class PaginationMetadata(BaseModel):
    """Metadata for pagination"""
    
    total_items: int = Field(..., description="Total items matching query")
    total_pages: int = Field(..., description="Total pages")
    current_page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Has next page")
    has_previous: bool = Field(..., description="Has previous page")
    
    @classmethod
    def from_query(
        cls,
        total_items: int,
        current_page: int,
        per_page: int
    ) -> "PaginationMetadata":
        """Create metadata from query results"""
        total_pages = (total_items + per_page - 1) // per_page
        return cls(
            total_items=total_items,
            total_pages=total_pages,
            current_page=current_page,
            per_page=per_page,
            has_next=current_page < total_pages,
            has_previous=current_page > 1,
        )
```

### 3.3 Infrastructure Layer Specifications

#### 3.3.1: Repository Implementation

**File**: `app/infrastructure/repositories/producto.py`

**Extension**: Implement pagination method

```python
class SQLAlchemyProductoRepository(ProductoRepositoryInterface):
    
    def buscar_productos_paginado(
        self,
        dto: PaginationRequestDTO
    ) -> tuple[list[ProductoEntity], int]:
        """Execute paginated query with sorting and filtering"""
        
        # Base query
        query = self.session.query(ProductoModel)
        
        # Apply filters
        query = self._apply_filters(query, dto.filters)
        
        # Get total count BEFORE pagination
        total_count = query.count()
        
        # Apply sorting
        query = self._apply_sorting(query, dto.parse_sort_criteria())
        
        # Apply pagination
        query = query.offset(dto.offset).limit(dto.per_page)
        
        # Execute query
        models = query.all()
        
        # Convert to entities
        entities = [model.to_entity() for model in models]
        
        return entities, total_count
    
    def _apply_filters(
        self,
        query,
        filters: Optional[FilterCriteria]
    ):
        """Apply advanced filters to query"""
        if not filters:
            return query
        
        # Brand filter
        if filters.marca:
            query = query.filter(ProductoModel.marca == filters.marca)
        
        # Family filter
        if filters.familia:
            query = query.filter(ProductoModel.familia == filters.familia)
        
        # Price range
        if filters.pvp_min is not None:
            query = query.filter(ProductoModel.pvp >= filters.pvp_min)
        if filters.pvp_max is not None:
            query = query.filter(ProductoModel.pvp <= filters.pvp_max)
        
        # BC3 specific filters
        if filters.bc3_product_type:
            query = query.filter(
                ProductoModel.bc3_product_type == filters.bc3_product_type
            )
        
        if filters.bc3_has_descripcion_corta is not None:
            if filters.bc3_has_descripcion_corta:
                query = query.filter(
                    ProductoModel.bc3_descripcion_corta.isnot(None)
                )
            else:
                query = query.filter(
                    ProductoModel.bc3_descripcion_corta.is_(None)
                )
        
        # Text search
        if filters.buscar:
            query = self._apply_text_search(query, filters.buscar)
        
        return query
    
    def _apply_sorting(
        self,
        query,
        sort_criteria: Optional[SortCriteria]
    ):
        """Apply sorting to query"""
        if not sort_criteria:
            return query.order_by(asc(ProductoModel.codigo))  # Default
        
        field_mapping = {
            "codigo": ProductoModel.codigo,
            "descripcion": ProductoModel.descripcion,
            "marca": ProductoModel.marca,
            "familia": ProductoModel.familia,
            "pvp": ProductoModel.pvp,
            "bc3_descripcion_corta": ProductoModel.bc3_descripcion_corta,
            "bc3_product_type": ProductoModel.bc3_product_type,
        }
        
        field = field_mapping.get(sort_criteria.field)
        if field:
            order_func = desc if sort_criteria.order == "desc" else asc
            return query.order_by(order_func(field))
        
        return query  # Fallback to no sorting
    
    def _apply_text_search(
        self,
        query,
        search_pattern: str
    ):
        """Apply text search to query"""
        pattern = f"%{search_pattern}%"
        return query.filter(
            or_(
                ProductoModel.codigo.ilike(pattern),
                ProductoModel.descripcion.ilike(pattern),
                ProductoModel.descripcion_corta.ilike(pattern),
                ProductoModel.bc3_descripcion_corta.ilike(pattern),
                ProductoModel.bc3_descripcion_completa.ilike(pattern),
            )
        )
```

#### 3.3.2: Cache Integration

**File**: `app/infrastructure/cache/pagination_cache.py`

```python
from app.infrastructure.cache.cache_manager import CacheManager
from typing import Optional, List, Any
import hashlib
import json

class PaginationCache:
    """Cache for pagination results"""
    
    def __init__(self, cache_backend: CacheManager):
        self.cache = cache_backend
    
    def generate_cache_key(
        self,
        dto: PaginationRequestDTO,
        entity_type: str = "producto"
    ) -> str:
        """Generate consistent cache key from DTO"""
        key_data = {
            "entity": entity_type,
            "page": dto.page,
            "per_page": dto.per_page,
            "sort": dto.sort,
            "filters": dto.filters.model_dump() if dto.filters else None,
        }
        
        # Hash para key consistente
        key_str = json.dumps(key_data, sort_keys=True)
        return f"pag:{entity_type}:{hashlib.md5(key_str.encode()).hexdigest()}"
    
    def get(self, cache_key: str) -> Optional[dict]:
        """Get cached results"""
        return self.cache.get(cache_key)
    
    def set(self, cache_key: str, data: dict, ttl: int = 300):
        """Cache results with TTL"""
        self.cache.set(cache_key, data, ttl)
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate cache matching pattern"""
        self.cache.invalidate_pattern(pattern)
```

### 3.4 HTTP Layer Specifications

#### 3.4.1: V2 Product List Endpoint

**File**: `app/interfaces/http/productos.py`

**Extension**: Add V2 endpoint with pagination

```python
from fastapi import Query, Depends
from app.application.dto.pagination.pagination_request import PaginationRequestDTO
from app.application.dto.pagination.pagination_response import PaginatedResponseDTO
from app.domain.services.producto import ProductoService

@router.get("/v2/list", response_model=PaginatedResponseDTO)
async def buscar_productos_v2_paginado(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    sort: Optional[str] = Query(None, description="Sort (e.g., 'precio:desc')"),
    marca: Optional[str] = Query(None, description="Filter by brand"),
    familia: Optional[str] = Query(None, description="Filter by family"),
    pvp_min: Optional[float] = Query(None, ge=0, description="Min price"),
    pvp_max: Optional[float] = Query(None, ge=0, description="Max price"),
    bc3_product_type: Optional[str] = Query(None, description="BC3 type filter"),
    bc3_has_descripcion_corta: Optional[bool] = Query(None, description="Has short description"),
    buscar: Optional[str] = Query(None, min_length=1, description="Search term"),
    service: ProductoService = Depends(get_producto_service),
) -> PaginatedResponseDTO:
    """V2 endpoint with full pagination, sorting, and filtering"""
    
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

#### 3.4.2: V1 Product List Endpoint (Backward Compatible)

**File**: `app/interfaces/http/productos.py`

**Extension**: Maintain V1 signature but use V2 logic internally

```python
from app.application.dto.pagination.v1_adapter import V1ToV2Adapter

@router.get("/list", response_model=List[ProductoResponseDTO])
async def listar_productos_v1(
    buscar: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=500),
    marca: Optional[str] = Query(None),
    familia: Optional[str] = Query(None),
    service: ProductoService = Depends(get_producto_service),
) -> List[ProductoResponseDTO]:
    """V1 endpoint - backward compatible"""
    
    # Adapt V1 params to V2 DTO
    v2_dto = V1ToV2Adapter.adapt_request(
        limit=limit,
        buscar=buscar,
        marca=marca,
        familia=familia
    )
    
    # Use V2 service method
    paginated_result = service.buscar_productos_paginado(v2_dto)
    
    # Return V1 format (just the items)
    return V1ToV2Adapter.adapt_response(paginated_result)
```

---

## 4. Database Specifications

### 4.1 Index Requirements

#### 4.1.1: Additional Indexes for Performance

```sql
-- Indexes for frequently filtered fields
CREATE INDEX idx_productos_marca ON productos_clean(marca);
CREATE INDEX idx_productos_familia ON productos_clean(familia);
CREATE INDEX idx_productos_pvp ON productos_clean(pvp);

-- BC3-specific indexes
CREATE INDEX idx_productos_bc3_type ON productos_clean(bc3_product_type);

-- Composite index for common filter combinations
CREATE INDEX idx_productos_marca_familia ON productos_clean(marca, familia);

-- Text search indexes (if supported)
-- CREATE VIRTUAL TABLE productos_fts USING fts5(
--     codigo, descripcion, descripcion_corta, 
--     bc3_descripcion_corta, bc3_descripcion_completa
-- );
```

#### 4.1.2: Index Performance Targets

- Index size: < 10MB total
- Index creation time: < 30 seconds
- Query improvement: 50-70% reduction in query time

---

## 5. Testing Specifications

### 5.1 Unit Test Specifications

#### 5.1.1: DTO Validation Tests

- Test default values
- Test validation constraints (page ≥ 1, 1 ≤ per_page ≤ 100)
- Test offset calculation
- Test sort criteria validation
- Test filter criteria validation
- Test pvp_min ≤ pvp_max validation

#### 5.1.2: Metadata Calculation Tests

- Test total_pages calculation
- Test has_next calculation
- Test has_previous calculation
- Test edge cases (empty results, single page)

### 5.2 Integration Test Specifications

#### 5.2.1: Repository Pagination Tests

- Test basic pagination
- Test with filters applied
- Test with sorting applied
- Test combined filters + sorting + pagination
- Test COUNT query performance
- Test memory usage

#### 5.2.2: Cache Integration Tests

- Test cache hit on identical query
- Test cache miss on new query
- Test cache invalidation on writes
- Test cache warming on startup
- Test cache key generation

### 5.3 Acceptance Test Specifications

#### 5.3.1: V2 Endpoint Tests

- Test pagination with page/per_page
- Test sorting with sort parameter
- Test filtering with various filters
- Test text search functionality
- Test combined pagination + sorting + filtering
- Test error responses for invalid input

#### 5.3.2: V1 Endpoint Compatibility Tests

- Test V1 endpoint with existing parameters
- Test V1 endpoint response format unchanged
- Test V1 endpoint uses V2 logic internally
- Test V1 endpoint performance

#### 5.3.3: Performance Tests

- Test P95 response time < 200ms
- Test P99 response time < 500ms
- Test memory usage < 100MB
- Test cache hit rate > 50%

---

## 6. Security Specifications

### 6.1 Input Validation

- All input validated via Pydantic models
- SQL injection prevented via parameterized queries
- XSS prevention via proper output encoding
- Rate limiting on expensive queries

### 6.2 Data Protection

- Sensitive data not exposed in errors
- Query parameters sanitized
- Input length limits enforced
- Field whitelisting enforced

---

## 7. Monitoring Specifications

### 7.1 Performance Monitoring

- Track P95/P99 response times
- Monitor cache hit/miss ratios
- Track query execution times
- Monitor memory usage

### 7.2 Error Monitoring

- Track validation errors
- Monitor cache failures
- Track database connection issues
- Monitor pagination edge cases

---

## 8. Deployment Specifications

### 8.1 Database Migration

- Create additional indexes
- Update ANALYZE statistics
- Performance baseline measurement

### 8.2 Configuration

- Cache TTL configuration
- Pagination limits configuration
- Logging configuration
- Monitoring configuration

### 8.3 Rollback Plan

- Database index rollback
- Code rollback capability
- Configuration rollback
- Cache flush capability

---

## 9. Acceptance Criteria Summary

### 9.1 Functional Acceptance

- [ ] All endpoints support pagination
- [ ] All endpoints support sorting
- [ ] All endpoints support advanced filtering
- [ ] V1 endpoints maintain backward compatibility
- [ ] Cache integration functional
- [ ] Text search works correctly

### 9.2 Performance Acceptance

- [ ] P95 response time < 200ms
- [ ] P99 response time < 500ms
- [ ] COUNT query performance < 50ms
- [ ] Cache hit rate > 50%
- [ ] Memory usage < 100MB

### 9.3 Quality Acceptance

- [ ] Test coverage > 80%
- [ ] Zero mypy errors
- [ ] All existing tests pass
- [ ] TDD methodology followed

### 9.4 Architecture Acceptance

- [ ] Hexagonal architecture maintained
- [ ] No direct database access in HTTP layer
- [ ] Dependency injection functional
- [ ] DTO pattern followed

---

## 10. Implementation Phases

### Phase 1: Core DTOs + Repository Methods

**Duration**: 2-3 hours
**Deliverables**:

- DTOs created and validated
- Repository interface extended
- Repository implementation complete
- Unit tests for DTOs and repository

### Phase 2: Service Layer + Cache Integration

**Duration**: 2 hours
**Deliverables**:

- Domain service methods implemented
- Cache integration complete
- Cache invalidation strategy implemented
- Integration tests for service layer

### Phase 3: HTTP Layer + V1 Compatibility

**Duration**: 2-3 hours
**Deliverables**:

- V2 endpoints implemented
- V1 adapters implemented
- Backward compatibility tests passing
- Acceptance tests for all endpoints

### Phase 4: Monitoring + Optimization

**Duration**: 1-2 hours
**Deliverables**:

- Performance monitoring implemented
- Database indexes optimized
- Cache tuned for production
- Documentation complete

---

## 11. Dependencies

### Internal Dependencies

- Fase 3: Architecture Hexagonal Migration (completed)
- Fase 4.1: Performance Optimization (completed)
- Existing test infrastructure
- Existing database schema

### External Dependencies

- None (self-contained implementation)

---

## 12. Risk Mitigation

### 12.1 Performance Risks

- **COUNT query slowness**: Optimize indexes, consider cache
- **Memory issues**: Use generators, limit per_page
- **Cache complexity**: TTL-based, pattern invalidation

### 12.2 Integration Risks

- **Breaking changes**: Extensive testing, maintain V1
- **Architecture violations**: Code review, compliance checks
- **Test coverage gaps**: TDD enforcement, >80% target

---

**Specification Version**: 1.0  
**Created**: 2026-07-12T12:30:00Z  
**Author**: el Gentleman (Pi Coding Agent)  
**Status**: 📝 Draft - Pending Approval  
**Next Phase**: Design
