# Fase 4.2 - Advanced Features: Implementation Tasks

## Tasks Overview

Detailed implementation tasks for adding pagination, sorting, and advanced filtering to API-DISANO following hexagonal architecture principles.

**Change ID:** fase4-advanced-features  
**Phase:** Fase 4.2 - Tasks  
**Version:** 1.0  
**Status**: Draft

---

## Phase 1: Core DTOs + Repository Methods (TASK-1.1 to TASK-1.10)

### TASK-1.1: Create Pagination DTO Package Structure

**Description**: Create the package structure for pagination DTOs.

**Priority**: HIGH  
**Estimated Time**: 15 minutes  
**Dependencies**: None  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Create directory: `app/application/dto/pagination/`
2. Create `__init__.py` file with exports
3. Verify package structure
4. Write basic test for package import

**Deliverables**:

- `app/application/dto/pagination/__init__.py`
- Directory structure created
- Test for package import

**Acceptance Criteria**:

- [ ] Directory structure created
- [ ] `__init__.py` exports all DTO classes
- [ ] Package can be imported successfully
- [ ] Test for package import passes

---

### TASK-1.2: Implement PaginationRequestDTO

**Description**: Implement DTO for pagination requests with comprehensive validation.

**Priority**: HIGH  
**Estimated Time**: 30 minutes  
**Dependencies**: TASK-1.1  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Create file: `app/application/dto/pagination/pagination_request.py`
2. Implement `PaginationRequestDTO` class
3. Add field: `page` with validation (≥ 1)
4. Add field: `per_page` with validation (1-100)
5. Add field: `sort` (optional)
6. Add `offset` property for calculation
7. Add `parse_sort_criteria()` method
8. Write unit tests for validation
9. Write unit tests for offset calculation
10. Verify Pydantic validation works

**Deliverables**:

- `app/application/dto/pagination/pagination_request.py`
- Unit tests in `tests/unit/application/dto/test_pagination_request.py`

**Acceptance Criteria**:

- [ ] `page` defaults to 1
- [ ] `page` validates ≥ 1
- [ ] `per_page` defaults to 20
- [ ] `per_page` validates 1-100
- [ ] `offset` property calculates correctly
- [ ] `sort` field optional
- [ ] All unit tests passing
- [ ] Zero mypy errors

---

### TASK-1.3: Implement PaginatedResponseDTO

**Description**: Implement DTO for paginated responses with metadata.

**Priority**: HIGH  
**Estimated Time**: 30 minutes  
**Dependencies**: TASK-1.1  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Create file: `app/application/dto/pagination/pagination_response.py`
2. Implement `PaginationMetadata` class
3. Add fields: total_items, total_pages, current_page, per_page, has_next, has_previous
4. Add `from_query()` classmethod for calculation
5. Implement `PaginatedResponseDTO` class
6. Add fields: items, pagination, filters_applied, sorting_applied
7. Write unit tests for metadata calculation
8. Write unit tests for response serialization
9. Verify JSON serialization works
10. Test edge cases (empty results, single page)

**Deliverables**:

- `app/application/dto/pagination/pagination_response.py`
- Unit tests in `tests/unit/application/dto/test_pagination_response.py`

**Acceptance Criteria**:

- [ ] `PaginationMetadata` has all required fields
- [ ] `from_query()` calculates total_pages correctly
- [ ] `has_next` is False on last page
- [ ] `has_previous` is False on first page
- [ ] `PaginatedResponseDTO` includes metadata
- [ ] JSON serialization works
- [ ] All unit tests passing
- [ ] Edge cases handled (empty, single page)

---

### TASK-1.4: Implement SortCriteria DTO

**Description**: Implement DTO for sorting criteria with field validation.

**Priority**: HIGH  
**Estimated Time**: 20 minutes  
**Dependencies**: TASK-1.1  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Create file: `app/application/dto/pagination/sort_criteria.py`
2. Implement `SortCriteria` class
3. Add field: `sort` (optional)
4. Add field: `field` with whitelist validation
5. Add field: `order` with "asc"/"desc" validation
6. Add field validator to normalize order to lowercase
7. Define allowed fields whitelist
8. Write unit tests for field validation
9. Write unit tests for order validation
10. Write unit tests for default values

**Deliverables**:

- `app/application/dto/pagination/sort_criteria.py`
- Unit tests in `tests/unit/application/dto/test_sort_criteria.py`

**Acceptance Criteria**:

- [ ] Field whitelist includes all database columns
- [ ] Invalid fields raise ValidationError
- [ ] Order values other than "asc"/"desc" rejected
- [ ] Order normalized to lowercase
- [ ] Default sort is codigo asc
- [ ] All unit tests passing
- [ ] Zero mypy errors

---

### TASK-1.5: Implement FilterCriteria DTO

**Description**: Implement comprehensive DTO for advanced filtering.

**Priority**: HIGH  
**Estimated Time**: 30 minutes  
**Dependencies**: TASK-1.1  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Create file: `app/application/dto/pagination/filter_criteria.py`
2. Implement `FilterCriteria` class
3. Add field: `marca` (optional, max_length=50)
4. Add field: `familia` (optional, max_length=50)
5. Add field: `pvp_min` (optional, ≥ 0)
6. Add field: `pvp_max` (optional, ≥ 0)
7. Add field: `bc3_product_type` (optional)
8. Add field: `bc3_has_descripcion_corta` (optional bool)
9. Add field: `buscar` (optional, min_length=1)
10. Add model validator for pvp_min ≤ pvp_max
11. Write unit tests for field validation
12. Write unit tests for price range validation
13. Write unit tests for optional fields
14. Verify Pydantic validation works

**Deliverables**:

- `app/application/dto/pagination/filter_criteria.py`
- Unit tests in `tests/unit/application/dto/test_filter_criteria.py`

**Acceptance Criteria**:

- [ ] All filter fields are optional
- [ ] pvp_min ≥ 0 enforced
- [ ] pvp_max ≥ 0 enforced
- [ ] pvp_min ≤ pvp_max enforced
- [ ] marca/familia max_length = 50
- [ ] buscar min_length = 1
- [ ] All unit tests passing
- [ ] Zero mypy errors

---

### TASK-1.6: Extend ProductoRepositoryInterface

**Description**: Extend repository interface with pagination method.

**Priority**: HIGH  
**Estimated Time**: 20 minutes  
**Dependencies**: TASK-1.2, TASK-1.3  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Open file: `app/domain/repositories/producto.py`
2. Import required DTOs
3. Add abstract method: `buscar_productos_paginado()`
4. Define method signature with proper type hints
5. Add comprehensive docstring
6. Verify interface compiles
7. Write unit test for interface compliance
8. Verify no existing tests broken

**Deliverables**:

- Updated `app/domain/repositories/producto.py`
- Unit test for interface compliance

**Acceptance Criteria**:

- [ ] Method signature defined correctly
- [ ] Type hints complete
- [ ] Docstring comprehensive
- [ ] Returns tuple[list[ProductoEntity], int]
- [ ] Interface compiles without errors
- [ ] Unit test for interface compliance passes
- [ ] No existing tests broken

---

### TASK-1.7: Implement Repository Pagination Method

**Description**: Implement pagination method in SQLAlchemy repository.

**Priority**: HIGH  
**Estimated Time**: 60 minutes  
**Dependencies**: TASK-1.6  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Open file: `app/infrastructure/repositories/producto.py`
2. Import required DTOs and SQLAlchemy functions
3. Implement `buscar_productos_paginado()` method
4. Implement `_apply_filters()` helper method
5. Implement `_apply_sorting()` helper method
6. Implement `_apply_text_search()` helper method
7. Add field mapping for sorting
8. Test filter chain building
9. Test sort order application
10. Test text search patterns
11. Test pagination offset/limit
12. Test COUNT query execution
13. Test entity conversion
14. Write integration tests
15. Verify performance acceptable

**Deliverables**:

- Updated `app/infrastructure/repositories/producto.py`
- Integration tests in `tests/integration/repositories/test_producto_pagination.py`

**Acceptance Criteria**:

- [ ] Filter chain builds correctly
- [ ] Sort order applies correctly
- [ ] Text search works across all fields
- [ ] Pagination offset/limit applied
- [ ] COUNT query executes before pagination
- [ ] Entity conversion works
- [ ] Returns correct tuple format
- [ ] All integration tests passing
- [ ] Performance acceptable (< 200ms P95)

---

### TASK-1.8: Implement Similar Methods for Familia

**Description**: Implement pagination for Familia entity following same pattern.

**Priority**: MEDIUM  
**Estimated Time**: 45 minutes  
**Dependencies**: TASK-1.7  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Open file: `app/domain/repositories/familia.py`
2. Extend `FamiliaRepositoryInterface` with pagination method
3. Open file: `app/infrastructure/repositories/familia.py`
4. Implement pagination methods for Familia
5. Adapt filter logic for Familia fields
6. Write unit tests for Familia DTOs
7. Write integration tests for Familia repository
8. Verify consistency with Producto pattern

**Deliverables**:

- Updated `app/domain/repositories/familia.py`
- Updated `app/infrastructure/repositories/familia.py`
- Tests for Familia pagination

**Acceptance Criteria**:

- [ ] Familia interface extended
- [ ] Familia repository implements pagination
- [ ] Filter logic adapted for Familia fields
- [ ] Consistent pattern with Producto
- [ ] All tests passing
- [ ] Zero mypy errors

---

### TASK-1.9: Write Comprehensive Unit Tests for DTOs

**Description**: Write complete unit test suite for all pagination DTOs.

**Priority**: HIGH  
**Estimated Time**: 30 minutes  
**Dependencies**: TASK-1.2, TASK-1.3, TASK-1.4, TASK-1.5  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Create test files for each DTO
2. Write tests for default values
3. Write tests for validation constraints
4. Write tests for edge cases
5. Write tests for property calculations
6. Write tests for method implementations
7. Verify test coverage > 80%
8. Run tests and verify all passing
9. Check for mypy errors

**Deliverables**:

- Complete unit test suite
- Test coverage report

**Acceptance Criteria**:

- [ ] All DTOs have comprehensive tests
- [ ] Default values tested
- [ ] Validation constraints tested
- [ ] Edge cases covered
- [ ] Property calculations tested
- [ ] Test coverage > 80%
- [ ] All tests passing
- [ ] Zero mypy errors

---

### TASK-1.10: Write Integration Tests for Repository

**Description**: Write integration tests for repository pagination methods.

**Priority**: HIGH  
**Estimated Time**: 45 minutes  
**Dependencies**: TASK-1.7, TASK-1.8  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Create integration test file
2. Write test for basic pagination
3. Write test for pagination with filters
4. Write test for pagination with sorting
5. Write test for combined filters + sorting + pagination
6. Write test for COUNT query performance
7. Write test for memory usage
8. Write test for edge cases
9. Write test for large datasets
10. Verify all tests passing
11. Check performance against targets

**Deliverables**:

- Integration tests in `tests/integration/repositories/test_producto_pagination.py`
- Integration tests in `tests/integration/repositories/test_familia_pagination.py`

**Acceptance Criteria**:

- [ ] Basic pagination test passes
- [ ] Filter tests pass
- [ ] Sorting tests pass
- [ ] Combined tests pass
- [ ] COUNT query performance < 50ms
- [ ] Memory usage < 100MB
- [ ] Edge cases handled
- [ ] All tests passing
- [ ] Performance targets met

---

## Phase 2: Service Layer + Cache Integration (TASK-2.1 to TASK-2.8)

### TASK-2.1: Implement ProductoService Pagination Method

**Description**: Implement service layer method for pagination with business logic.

**Priority**: HIGH  
**Estimated Time**: 30 minutes  
**Dependencies**: TASK-1.7  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Open file: `app/domain/services/producto.py`
2. Import required DTOs
3. Implement `buscar_productos_paginado()` method
4. Add domain rule validation (pvp_min ≤ pvp_max)
5. Convert entities to DTOs
6. Build pagination metadata
7. Build complete response DTO
8. Write unit tests for service method
9. Test business logic
10. Test entity conversion

**Deliverables**:

- Updated `app/domain/services/producto.py`
- Unit tests for service method

**Acceptance Criteria**:

- [ ] Domain rules validated correctly
- [ ] Entities converted to DTOs correctly
- [ ] Pagination metadata calculated correctly
- [ ] Complete response DTO built
- [ ] All unit tests passing
- [ ] Zero mypy errors

---

### TASK-2.2: Implement FamiliaService Pagination Method

**Description**: Implement service layer method for Familia pagination.

**Priority**: MEDIUM  
**Estimated Time**: 20 minutes  
**Dependencies**: TASK-1.8, TASK-2.1  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Open file: `app/domain/services/familia.py`
2. Import required DTOs
3. Implement `buscar_familias_paginado()` method
4. Adapt business logic for Familia
5. Write unit tests for service method
6. Test consistency with Producto service

**Deliverables**:

- Updated `app/domain/services/familia.py`
- Unit tests for Familia service

**Acceptance Criteria**:

- [ ] Familia service implements pagination
- [ ] Business logic adapted correctly
- [ ] Consistent pattern with Producto
- [ ] All unit tests passing
- [ ] Zero mypy errors

---

### TASK-2.3: Create PaginationCache Wrapper

**Description**: Create cache wrapper specifically for pagination results.

**Priority**: HIGH  
**Estimated Time**: 30 minutes  
**Dependencies**: TASK-1.1, Fase 4.1 cache  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Create file: `app/infrastructure/cache/pagination_cache.py`
2. Implement `PaginationCache` class
3. Add `generate_cache_key()` method
4. Add `get()` method
5. Add `set()` method
6. Add `invalidate_pattern()` method
7. Add cache statistics tracking
8. Write unit tests for cache wrapper
9. Test cache key generation
10. Test cache hit/miss

**Deliverables**:

- `app/infrastructure/cache/pagination_cache.py`
- Unit tests for cache wrapper

**Acceptance Criteria**:

- [ ] Cache key generated consistently
- [ ] `get()` method works correctly
- [ ] `set()` method works correctly
- [ ] `invalidate_pattern()` works correctly
- [ ] Cache statistics tracked
- [ ] All unit tests passing
- [ ] Zero mypy errors

---

### TASK-2.4: Integrate Cache with Repository

**Description**: Modify repository to use cache for pagination results.

**Priority**: HIGH  
**Estimated Time**: 45 minutes  
**Dependencies**: TASK-2.3, TASK-1.7  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Modify repository constructor to accept cache
2. Add cache check before database query
3. Add cache set after database query
4. Handle cache hit scenarios
5. Handle cache miss scenarios
6. Update dependency injection chain
7. Write integration tests for cache integration
8. Test cache hit performance
9. Test cache miss performance
10. Verify cache hit rate > 50%

**Deliverables**:

- Updated repository with cache integration
- Integration tests for cache

**Acceptance Criteria**:

- [ ] Cache checked before DB query
- [ ] Cache set after DB query
- [ ] Cache hit handled correctly
- [ ] Cache miss handled correctly
- [ ] DI chain updated
- [ ] Cache hit > 50% for popular queries
- [ ] Performance improved with cache
- [ ] All tests passing

---

### TASK-2.5: Implement Cache Invalidation Strategy

**Description**: Add cache invalidation to service layer methods.

**Priority**: HIGH  
**Estimated Time**: 30 minutes  
**Dependencies**: TASK-2.1, TASK-2.4  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Modify service constructor to accept cache
2. Add cache invalidation to `crear_producto()`
3. Add cache invalidation to `actualizar_producto()`
4. Add cache invalidation to `eliminar_producto()`
5. Use pattern-based invalidation
6. Write tests for invalidation
7. Test invalidation on create
8. Test invalidation on update
9. Test invalidation on delete

**Deliverables**:

- Updated service methods with invalidation
- Tests for cache invalidation

**Acceptance Criteria**:

- [ ] Cache invalidated on create
- [ ] Cache invalidated on update
- [ ] Cache invalidated on delete
- [ ] Pattern-based invalidation works
- [ ] No stale cache after writes
- [ ] All tests passing

---

### TASK-2.6: Implement Cache Warming Strategy

**Description**: Implement cache warming for popular queries on startup.

**Priority**: MEDIUM  
**Estimated Time**: 30 minutes  
**Dependencies**: TASK-2.3, TASK-2.4  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Define popular queries list
2. Create `warm_cache()` function
3. Execute popular queries and cache results
4. Add startup hook in FastAPI app
5. Test cache warming on startup
6. Test cache warming completes in reasonable time
7. Verify cache populated after startup

**Deliverables**:

- Cache warming implementation
- Startup integration
- Tests for cache warming

**Acceptance Criteria**:

- [ ] Popular queries defined
- [ ] Cache warming executes on startup
- [ ] Cache warming completes < 5 seconds
- [ ] Cache populated after startup
- [ ] No errors during warming
- [ ] All tests passing

---

### TASK-2.7: Write Integration Tests for Cache

**Description**: Write comprehensive integration tests for cache functionality.

**Priority**: HIGH  
**Estimated Time**: 30 minutes  
**Dependencies**: TASK-2.4, TASK-2.5, TASK-2.6  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Create integration test file for cache
2. Write test for cache hit on identical query
3. Write test for cache miss on new query
4. Write test for cache invalidation on writes
5. Write test for cache warming
6. Write test for cache statistics
7. Write test for cache performance
8. Verify cache hit rate > 50%
9. Verify all tests passing

**Deliverables**:

- Integration tests in `tests/integration/test_pagination_cache.py`

**Acceptance Criteria**:

- [ ] Cache hit test passes
- [ ] Cache miss test passes
- [ ] Cache invalidation test passes
- [ ] Cache warming test passes
- [ ] Cache statistics test passes
- [ ] Cache hit rate > 50%
- [ ] All tests passing

---

### TASK-2.8: Optimize Cache Configuration

**Description**: Tune cache TTL and configuration based on testing results.

**Priority**: MEDIUM  
**Estimated Time**: 20 minutes  
**Dependencies**: TASK-2.7  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Analyze cache performance from tests
2. Adjust cache TTL based on results
3. Optimize cache key generation if needed
4. Tune cache warming queries
5. Update cache configuration
6. Re-run performance tests
7. Verify performance targets met

**Deliverables**:

- Optimized cache configuration
- Performance test results

**Acceptance Criteria**:

- [ ] Cache TTL optimized
- [ ] Cache warming queries tuned
- [ ] Performance targets met
- [ ] Cache hit rate > 50%
- [ ] P95 response time < 200ms

---

## Phase 3: HTTP Layer + V1 Compatibility (TASK-3.1 to TASK-3.10)

### TASK-3.1: Implement V2 Product List Endpoint

**Description**: Implement V2 endpoint with full pagination support.

**Priority**: HIGH  
**Estimated Time**: 45 minutes  
**Dependencies**: TASK-2.1  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Open file: `app/interfaces/http/productos.py`
2. Import required DTOs and service
3. Add V2 endpoint: `/api/productos/v2/list`
4. Define all query parameters (page, per_page, sort, filters)
5. Build PaginationRequestDTO from query params
6. Call service method
7. Return PaginatedResponseDTO
8. Add comprehensive docstring
9. Add OpenAPI documentation
10. Write acceptance tests

**Deliverables**:

- Updated `app/interfaces/http/productos.py`
- Acceptance tests for V2 endpoint

**Acceptance Criteria**:

- [ ] V2 endpoint accessible
- [ ] All query parameters work
- [ ] Pagination works correctly
- [ ] Sorting works correctly
- [ ] Filtering works correctly
- [ ] Response format correct
- [ ] OpenAPI documentation complete
- [ ] All acceptance tests passing

---

### TASK-3.2: Implement V2 Familia List Endpoint

**Description**: Implement V2 endpoint for families with pagination.

**Priority**: MEDIUM  
**Estimated Time**: 30 minutes  
**Dependencies**: TASK-2.2, TASK-3.1  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Open file: `app/interfaces/http/familias.py`
2. Import required DTOs and service
3. Add V2 endpoint: `/api/familias/v2/list`
4. Define query parameters (adapted for families)
5. Build PaginationRequestDTO from query params
6. Call service method
7. Return PaginatedResponseDTO
8. Add docstring and OpenAPI docs
9. Write acceptance tests

**Deliverables**:

- Updated `app/interfaces/http/familias.py`
- Acceptance tests for V2 endpoint

**Acceptance Criteria**:

- [ ] V2 endpoint accessible
- [ ] Query parameters work for families
- [ ] Pagination works correctly
- [ ] Sorting works correctly
- [ ] Filtering works correctly
- [ ] Consistent pattern with productos
- [ ] All acceptance tests passing

---

### TASK-3.3: Implement V2 BC3 List Endpoint

**Description**: Implement V2 endpoint for BC3 with pagination.

**Priority**: MEDIUM  
**Estimated Time**: 30 minutes  
**Dependencies**: TASK-3.1  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Open file: `app/interfaces/http/bc3.py`
2. Import required DTOs and service
3. Add V2 endpoint: `/api/bc3/v2/list`
4. Define query parameters with BC3-specific filters
5. Build PaginationRequestDTO from query params
6. Call service method
7. Return PaginatedResponseDTO
8. Add docstring and OpenAPI docs
9. Write acceptance tests

**Deliverables**:

- Updated `app/interfaces/http/bc3.py`
- Acceptance tests for V2 endpoint

**Acceptance Criteria**:

- [ ] V2 endpoint accessible
- [ ] BC3-specific filters work
- [ ] Pagination works correctly
- [ ] Sorting works correctly
- [ ] Response format correct
- [ ] All acceptance tests passing

---

### TASK-3.4: Implement V1ToV2Adapter

**Description**: Create adapter for V1 to V2 parameter/response conversion.

**Priority**: HIGH  
**Estimated Time**: 30 minutes  
**Dependencies**: TASK-1.1  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Create file: `app/application/dto/pagination/v1_adapter.py`
2. Implement `V1ToV2Adapter` class
3. Add `adapt_request()` static method
4. Add `adapt_response()` static method
5. Handle V1 limit → V2 per_page conversion
6. Handle V1 buscar → V2 filter conversion
7. Write unit tests for adapter
8. Test request adaptation
9. Test response adaptation

**Deliverables**:

- `app/application/dto/pagination/v1_adapter.py`
- Unit tests for adapter

**Acceptance Criteria**:

- [ ] V1 limit → V2 per_page works
- [ ] V1 buscar → V2 filter works
- [ ] V1 marca/familia → V2 filters work
- [ ] Response adaptation works
- [ ] Defaults applied correctly
- [ ] All unit tests passing
- [ ] Zero mypy errors

---

### TASK-3.5: Adapt V1 Endpoints to Use V2 Logic

**Description**: Modify V1 endpoints to use V2 pagination logic internally.

**Priority**: HIGH  
**Estimated Time**: 30 minutes  
**Dependencies**: TASK-3.4  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Open V1 endpoints in `app/interfaces/http/productos.py`
2. Import `V1ToV2Adapter`
3. Adapt V1 params to V2 DTO
4. Call V2 service method
5. Adapt V2 response to V1 format
6. Keep V1 signature unchanged
7. Keep V1 response format unchanged
8. Write acceptance tests for V1 compatibility
9. Verify zero breaking changes

**Deliverables**:

- Updated V1 endpoints
- Acceptance tests for V1 compatibility

**Acceptance Criteria**:

- [ ] V1 signature unchanged
- [ ] V1 response format unchanged
- [ ] V1 uses V2 logic internally
- [ ] V1 performance acceptable
- [ ] Zero breaking changes
- [ ] All existing tests still pass
- [ ] Acceptance tests passing

---

### TASK-3.6: Write Acceptance Tests for V2 Endpoints

**Description**: Write comprehensive acceptance tests for all V2 endpoints.

**Priority**: HIGH  
**Estimated Time**: 45 minutes  
**Dependencies**: TASK-3.1, TASK-3.2, TASK-3.3  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Create acceptance test file
2. Write test for pagination
3. Write test for sorting
4. Write test for filtering
5. Write test for text search
6. Write test for combined features
7. Write test for error handling
8. Write test for performance
9. Test all V2 endpoints
10. Verify all tests passing

**Deliverables**:

- Acceptance tests in `tests/acceptance/test_v2_endpoints.py`

**Acceptance Criteria**:

- [ ] Pagination test passes
- [ ] Sorting test passes
- [ ] Filtering test passes
- [ ] Text search test passes
- [ ] Combined features test passes
- [ ] Error handling test passes
- [ ] Performance test passes
- [ ] All V2 endpoints tested
- [ ] All tests passing

---

### TASK-3.7: Write Acceptance Tests for V1 Compatibility

**Description**: Write acceptance tests to ensure V1 backward compatibility.

**Priority**: HIGH  
**Estimated Time**: 30 minutes  
**Dependencies**: TASK-3.5  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Create acceptance test file for V1
2. Write test for V1 list endpoint
3. Write test for V1 search endpoint
4. Write test for V1 response format
5. Write test for V1 performance
6. Test V1 vs V2 parity
7. Verify zero breaking changes
8. Verify V1 signature unchanged

**Deliverables**:

- Acceptance tests in `tests/acceptance/test_v1_compatibility.py`

**Acceptance Criteria**:

- [ ] V1 list test passes
- [ ] V1 search test passes
- [ ] V1 response format test passes
- [ ] V1 performance test passes
- [ ] V1 vs V2 parity test passes
- [ ] Zero breaking changes confirmed
- [ ] All tests passing

---

### TASK-3.8: Update OpenAPI Documentation

**Description**: Update OpenAPI documentation for all new endpoints.

**Priority**: MEDIUM  
**Estimated Time**: 30 minutes  
**Dependencies**: TASK-3.1, TASK-3.2, TASK-3.3, TASK-3.5  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Update OpenAPI descriptions
2. Add example queries for common use cases
3. Add parameter descriptions
4. Add response schemas
5. Add error response schemas
6. Add deprecation notices for V1
7. Test OpenAPI generation
8. Verify documentation is complete

**Deliverables**:

- Updated OpenAPI documentation
- Example queries documented

**Acceptance Criteria**:

- [ ] OpenAPI descriptions complete
- [ ] Example queries included
- [ ] Parameter descriptions complete
- [ ] Response schemas documented
- [ ] Error schemas documented
- [ ] V1 deprecation notices added
- [ ] OpenAPI generation works
- [ ] Documentation is accurate

---

### TASK-3.9: Test Backward Compatibility with Existing Tests

**Description**: Run all existing tests to ensure zero breaking changes.

**Priority**: HIGH  
**Estimated Time**: 20 minutes  
**Dependencies**: TASK-3.5  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Run all existing tests
2. Identify any failing tests
3. Investigate test failures
4. Fix any breaking changes found
5. Re-run all tests
6. Verify zero breaking changes
7. Document any compatibility issues resolved

**Deliverables**:

- All existing tests passing
- Compatibility documentation

**Acceptance Criteria**:

- [ ] All existing tests pass
- [ ] Zero breaking changes
- [ ] No regressions introduced
- [ ] V1 endpoints work as before
- [ ] V2 endpoints work correctly

---

### TASK-3.10: Test Performance Against Targets

**Description**: Run performance tests to verify targets are met.

**Priority**: HIGH  
**Estimated Time**: 30 minutes  
**Dependencies**: TASK-3.6  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Run performance tests
2. Measure P95 response time
3. Measure P99 response time
4. Measure COUNT query time
5. Measure memory usage
6. Measure cache hit rate
7. Compare against targets
8. Optimize if needed
9. Document performance results

**Deliverables**:

- Performance test results
- Performance optimization notes

**Acceptance Criteria**:

- [ ] P95 response time < 200ms
- [ ] P99 response time < 500ms
- [ ] COUNT query time < 50ms
- [ ] Memory usage < 100MB
- [ ] Cache hit rate > 50%
- [ ] All performance targets met

---

## Phase 4: Monitoring + Optimization (TASK-4.1 to TASK-4.8)

### TASK-4.1: Implement Query Performance Tracking

**Description**: Add performance tracking to repository methods.

**Priority**: MEDIUM  
**Estimated Time**: 20 minutes  
**Dependencies**: TASK-1.7, TASK-1.8  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Create performance tracking decorator
2. Apply to repository pagination methods
3. Log execution times
4. Log slow queries
5. Add alerting for slow queries
6. Test performance tracking
7. Verify logs are generated

**Deliverables**:

- Performance tracking decorator
- Performance logging

**Acceptance Criteria**:

- [ ] Execution times logged
- [ ] Slow queries identified
- [ ] Alerts generated for slow queries
- [ ] Performance tracking works
- [ ] Logs are accurate

---

### TASK-4.2: Implement Cache Statistics Tracking

**Description**: Add cache statistics tracking to cache wrapper.

**Priority**: MEDIUM  
**Estimated Time**: 20 minutes  
**Dependencies**: TASK-2.3  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Add statistics tracking to cache
2. Track hits, misses, total queries
3. Calculate hit rate
4. Log cache statistics
5. Add method to get statistics
6. Test statistics tracking
7. Verify hit rate calculation

**Deliverables**:

- Cache statistics tracking
- Statistics logging

**Acceptance Criteria**:

- [ ] Hits tracked correctly
- [ ] Misses tracked correctly
- [ ] Hit rate calculated correctly
- [ ] Statistics logged
- [ ] Statistics API works
- [ ] All tests passing

---

### TASK-4.3: Create Database Migration Script

**Description**: Create script to add indexes for pagination performance.

**Priority**: HIGH  
**Estimated Time**: 30 minutes  
**Dependencies**: TASK-1.7  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Create migration script file
2. Add CREATE INDEX statements
3. Add ANALYZE statement
4. Add rollback functionality
5. Test migration script
6. Test rollback script
7. Document migration process
8. Verify indexes created correctly

**Deliverables**:

- Migration script
- Rollback script
- Migration documentation

**Acceptance Criteria**:

- [ ] Migration script creates indexes
- [ ] ANALYZE runs successfully
- [ ] Rollback script works
- [ ] Indexes improve performance
- [ ] Migration documented
- [ ] All tests passing

---

### TASK-4.4: Run Database Migration

**Description**: Execute database migration to add pagination indexes.

**Priority**: HIGH  
**Estimated Time**: 15 minutes  
**Dependencies**: TASK-4.3  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Backup database
2. Run migration script
3. Verify indexes created
4. Run ANALYZE
5. Test query performance
6. Document results
7. Verify no issues

**Deliverables**:

- Database with indexes
- Migration results

**Acceptance Criteria**:

- [ ] Database backed up
- [ ] Indexes created successfully
- [ ] ANALYZE completed
- [ ] Query performance improved
- [ ] No errors encountered
- [ ] Migration documented

---

### TASK-4.5: Optimize Query Performance

**Description**: Optimize database queries based on profiling results.

**Priority**: MEDIUM  
**Estimated Time**: 30 minutes  
**Dependencies**: TASK-4.4, TASK-4.1  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Analyze query performance data
2. Identify slow queries
3. Optimize query strategies
4. Adjust indexes if needed
5. Optimize filtering logic
6. Optimize sorting logic
7. Re-run performance tests
8. Verify improvements

**Deliverables**:

- Optimized queries
- Performance improvements

**Acceptance Criteria**:

- [ ] Slow queries optimized
- [ ] Query performance improved
- [ ] P95 response time < 200ms
- [ ] P99 response time < 500ms
- [ ] Performance targets met

---

### TASK-4.6: Tune Cache Configuration

**Description**: Optimize cache configuration based on real usage patterns.

**Priority**: MEDIUM  
**Estimated Time**: 20 minutes  
**Dependencies**: TASK-2.7, TASK-4.2  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Analyze cache statistics
2. Identify popular queries
3. Adjust cache TTL
4. Optimize cache warming queries
5. Update cache configuration
6. Re-run cache tests
7. Verify improvements

**Deliverables**:

- Optimized cache configuration
- Cache performance improvements

**Acceptance Criteria**:

- [ ] Cache TTL optimized
- [ ] Cache warming queries optimized
- [ ] Cache hit rate > 50%
- [ ] Cache performance improved
- [ ] All tests passing

---

### TASK-4.7: Write Deployment Documentation

**Description**: Create comprehensive documentation for deployment.

**Priority**: MEDIUM  
**Estimated Time**: 30 minutes  
**Dependencies**: TASK-4.4  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Create deployment guide
2. Document migration process
3. Document configuration options
4. Document monitoring setup
5. Document rollback procedures
6. Document performance tuning
7. Add troubleshooting section
8. Review documentation

**Deliverables**:

- Deployment documentation
- Configuration documentation
- Troubleshooting guide

**Acceptance Criteria**:

- [ ] Deployment guide complete
- [ ] Migration process documented
- [ ] Configuration options documented
- [ ] Monitoring setup documented
- [ ] Rollback procedures documented
- [ ] Troubleshooting section included

---

### TASK-4.8: Verify All Acceptance Criteria

**Description**: Final verification that all acceptance criteria are met.

**Priority**: HIGH  
**Estimated Time**: 30 minutes  
**Dependencies**: All previous tasks  
**Status**: 🔄 Pending

**Implementation Steps**:

1. Run all tests
2. Check test coverage > 80%
3. Verify zero mypy errors
4. Verify all existing tests pass
5. Verify P95 response time < 200ms
6. Verify P99 response time < 500ms
7. Verify cache hit rate > 50%
8. Verify backward compatibility
9. Verify architecture compliance
10. Document final results

**Deliverables**:

- Final verification report
- Acceptance criteria checklist

**Acceptance Criteria**:

- [ ] All new tests passing
- [ ] Test coverage > 80%
- [ ] Zero mypy errors
- [ ] All existing tests pass
- [ ] P95 response time < 200ms
- [ ] P99 response time < 500ms
- [ ] Cache hit rate > 50%
- [ ] V1 compatibility maintained
- [ ] Hexagonal architecture maintained
- [ ] Ready for deployment

---

## Task Dependencies

### Critical Path

```
TASK-1.1 → TASK-1.2 → TASK-1.3 → TASK-1.4 → TASK-1.5 → TASK-1.6 → TASK-1.7 → TASK-2.1 → TASK-2.3 → TASK-2.4 → TASK-2.5 → TASK-3.1 → TASK-3.4 → TASK-3.5 → TASK-3.6 → TASK-3.9 → TASK-3.10 → TASK-4.8
```

### Parallelizable Tasks

- TASK-1.8 (after TASK-1.7)
- TASK-2.2 (after TASK-1.8, TASK-2.1)
- TASK-3.2 (after TASK-2.2, TASK-3.1)
- TASK-3.3 (after TASK-3.1)
- TASK-4.1, TASK-4.2 (after TASK-2.3)

### Blockers

- TASK-1.7 blocks most Phase 2 tasks
- TASK-2.1 blocks most HTTP layer tasks
- TASK-4.4 blocks most Phase 4 tasks

---

## Risk Mitigation

### High-Risk Tasks

- TASK-1.7: Repository implementation (complex query building)
- TASK-2.4: Cache integration (potential cache consistency issues)
- TASK-3.5: V1 compatibility (breaking changes risk)
- TASK-4.3: Database migration (production database changes)

### Mitigation Strategies

- TASK-1.7: Comprehensive integration tests, incremental development
- TASK-2.4: Extensive cache testing, TTL-based expiration
- TASK-3.5: V1 signature unchanged, extensive compatibility testing
- TASK-4.3: Backup database, rollback script, test on staging

---

## Success Metrics

### Quality Metrics

- Test coverage > 80%
- Zero mypy errors
- All existing tests passing
- TDD methodology followed

### Performance Metrics

- P95 response time < 200ms
- P99 response time < 500ms
- COUNT query time < 50ms
- Memory usage < 100MB
- Cache hit rate > 50%

### Functional Metrics

- All V2 endpoints functional
- All V1 endpoints backward compatible
- All acceptance criteria met
- Zero breaking changes

---

## Rollback Plan

### Immediate Rollback

- Git revert to last stable commit
- Database rollback script execution
- Cache flush

### Gradual Rollback

- Feature flags to disable new endpoints
- V1 endpoints remain functional
- Monitor production metrics

---

**Tasks Version**: 1.0  
**Created**: 2026-07-12T13:30:00Z  
**Author**: el Gentleman (Pi Coding Agent)  
**Status**: 📝 Draft - Ready for Implementation  
**Total Tasks**: 38 tasks  
**Total Estimated Time**: 8-10 hours  
**Next Phase**: Apply (Implementation)
