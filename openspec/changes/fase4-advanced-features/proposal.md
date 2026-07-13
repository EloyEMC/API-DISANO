# Fase 4.2 - Advanced Features: Proposal

## Executive Summary

### Business Problem

API-DISANO currently serves products data without pagination, sorting, or advanced filtering capabilities. As the product database grows, clients face challenges:

- **Performance degradation**: Large result sets cause slow responses and memory issues
- **Inefficient data access**: Clients must fetch entire datasets and filter client-side
- **Poor user experience**: No way to navigate large product catalogs efficiently
- **Development complexity**: Each client must implement similar filtering/pagination logic

### Proposed Solution

Implement comprehensive pagination, sorting, and advanced filtering for API-DISANO endpoints following hexagonal architecture principles and leveraging the caching infrastructure from Fase 4.1.

### Expected Business Value

- **Improved performance**: 50-70% reduction in response times for large datasets
- **Better user experience**: Efficient navigation of product catalogs
- **Reduced development effort**: Clients no longer need to implement client-side pagination/filtering
- **Scalability**: API can handle growing product databases without performance degradation
- **Backward compatibility**: Existing V1 endpoints remain functional

### Success Metrics

| Metric | Current | Target | Success Criteria |
|--------|---------|--------|------------------|
| P95 Response Time (large queries) | ~500ms | <200ms | 60% improvement |
| Client-side filtering required | 100% | 0% | Complete elimination |
| API complexity for pagination | High | Low | Standard REST patterns |
| V1 endpoint compatibility | 100% | 100% | Zero breaking changes |
| Cache hit rate (paginated queries) | 0% | >50% | From Fase 4.1 cache |

---

## Business Requirements

### User Stories

#### US-1: Pagination for Product Lists

**As a** frontend developer  
**I want to** paginate product lists with consistent performance  
**So that** users can navigate large product catalogs efficiently

**Acceptance Criteria:**

- API supports `page` and `per_page` parameters
- Default pagination: page 1, 20 items per page
- Maximum items per page: 100
- Response includes metadata: total items, total pages, has_next/previous

#### US-2: Multi-field Sorting

**As a** business user  
**I want to** sort products by price, name, brand, or other fields  
**So that** I can view products in the most relevant order

**Acceptance Criteria:**

- API supports `sort=campo:order` parameter (e.g., `sort=precio:desc`)
- Supports ascending and descending order
- Supports default sorting by product code
- Response includes sorting criteria applied

#### US-3: Advanced Filtering

**As a** catalog manager  
**I want to** filter products by brand, family, price range, and BC3-specific fields  
**So that** I can quickly find relevant products

**Acceptance Criteria:**

- API supports filters for: marca, familia, pvp_min, pvp_max
- API supports BC3-specific filters: bc3_product_type, bc3_has_descripcion_corta
- API supports text search across multiple fields
- Response includes filters applied

#### US-4: Backward Compatibility

**As a** existing V1 API consumer  
**I want to** continue using existing V1 endpoints without changes  
**So that** my application continues to work during migration

**Acceptance Criteria:**

- V1 endpoints maintain current signature
- V1 endpoints return same response format
- V1 endpoints use new pagination logic internally
- Zero breaking changes for V1 consumers

### Business Rules

#### BR-1: Pagination Limits

- Default per_page: 20 items
- Maximum per_page: 100 items (configurable)
- Minimum per_page: 1 item
- Page numbering starts at 1

#### BR-2: Sorting Rules

- Default sort:.codigo asc
- Sort fields limited to whitelisted fields only
- Sort order limited to: asc, desc
- Multi-sort not supported in MVP (future enhancement)

#### BR-3: Filtering Rules

- Exact match for: marca, familia, bc3_product_type
- Range validation for: pvp_min, pvp_max (pvp_min ≤ pvp_max)
- Text search applies to: codigo, descripcion, descripcion_corta, bc3_descripcion_corta, bc3_descripcion_completa
- Empty filter sets return all items

#### BR-4: BC3-Specific Rules

- bc3_product_type accepts: columna, generador, etc.
- bc3_has_descripcion_corta: boolean filter for presence/absence of short description
- BC3 filters are additive (AND logic)

### Non-Functional Requirements

#### NFR-1: Performance

- P95 response time < 200ms for paginated queries
- P99 response time < 500ms for paginated queries
- Memory usage < 100MB per paginated query
- COUNT query performance < 50ms

#### NFR-2: Caching Strategy

- Cache TTL: 5 minutes for paginated results
- Cache key based on complete DTO hash
- Cache invalidation on writes
- Cache warming for popular queries

#### NFR-3: Architecture Compliance

- Must follow hexagonal architecture principles
- No direct database access in HTTP layer
- Dependency injection for all components
- DTO pattern for input/output validation

#### NFR-4: Quality Assurance

- Test coverage > 80% for new code
- Zero mypy errors
- All existing tests must pass
- TDD methodology (RED → GREEN → REFACTOR)

---

## Product Requirements

### Feature Specifications

#### F1: Pagination Implementation

**Description**: Implement offset-based pagination for all product and family list endpoints.

**Technical Specifications**:

- Pagination DTO: `PaginationRequestDTO` (page, per_page, sort, filters)
- Metadata DTO: `PaginationMetadata` (total_items, total_pages, current_page, per_page, has_next, has_previous)
- Repository method: `buscar_productos_paginado(dto) → tuple[list[Entity], int]`
- Service method: `buscar_productos_paginado(dto) → PaginatedResponseDTO`

**Endpoints**:

```
GET /api/productos/v2/list?page=1&per_page=20
GET /api/productos/v2/search?page=1&per_page=20
GET /api/familias/v2/list?page=1&per_page=20
GET /api/bc3/v2/list?page=1&per_page=20
```

**Response Format**:

```json
{
  "items": [...],
  "pagination": {
    "total_items": 150,
    "total_pages": 8,
    "current_page": 1,
    "per_page": 20,
    "has_next": true,
    "has_previous": false
  },
  "filters_applied": {...},
  "sorting_applied": {...}
}
```

#### F2: Sorting Implementation

**Description**: Implement multi-field sorting with ascending/descending order for all list endpoints.

**Technical Specifications**:

- Sort DTO: `SortCriteria` (field, order)
- Field whitelist: codigo, descripcion, marca, familia, pvp, bc3_descripcion_corta, bc3_product_type
- Repository query: SQLAlchemy `asc()`/`desc()` functions
- Default sort: codigo asc

**Endpoints**:

```
GET /api/productos/v2/list?sort=precio:desc
GET /api/productos/v2/list?sort=marca:asc,familia:desc (multi-sort)
```

**Sorting Rules**:

- Invalid sort fields return HTTP 400
- Invalid sort orders default to asc
- Sorting applies after filtering
- Multi-sort applied in order specified

#### F3: Advanced Filtering Implementation

**Description**: Implement comprehensive filtering with exact matches, ranges, and text search.

**Technical Specifications**:

- Filter DTO: `FilterCriteria` (marca, familia, pvp_min, pvp_max, bc3_product_type, bc3_has_descripcion_corta, buscar)
- Repository query: SQLAlchemy filter chain
- Text search: ILIKE pattern matching
- Filter validation in service layer

**Endpoints**:

```
GET /api/productos/v2/list?marca=Disano&familia=Iluminación&pvp_min=50&pvp_max=200
GET /api/productos/v2/list?bc3_product_type=columna&bc3_has_descripcion_corta=true
GET /api/productos/v2/list?buscar=led
```

**Filtering Rules**:

- Multiple filters use AND logic
- Text search is case-insensitive
- pvp_min ≤ pvp_max validation
- Empty filter values ignored

#### F4: Backward Compatibility

**Description**: Maintain V1 endpoint signatures while using new pagination logic internally.

**Technical Specifications**:

- Adapter DTO: `V1ToV2Adapter`
- V1 endpoints internally convert to V2 DTOs
- V1 response format maintained
- Zero breaking changes

**Endpoints**:

```
GET /api/productos/list?limit=10&marca=Disano (V1)
GET /api/productos/v2/list?per_page=10&marca=Disano (V2)
```

**Compatibility Rules**:

- V1 `limit` → V2 `per_page`
- V1 response format unchanged
- V1 uses same business logic as V2
- V1 deprecated documentation updated

### User Experience Considerations

#### UX-1: Consistent API Contract

- All list endpoints follow same pagination/sorting/filtering patterns
- Error messages are clear and actionable
- Response formats are consistent across V1 and V2

#### UX-2: Developer-Friendly Documentation

- OpenAPI documentation with examples
- Example queries for common use cases
- Error response schemas documented
- Deprecation notices for V1 endpoints

#### UX-3: Progressive Enhancement

- V1 endpoints work with existing clients
- V2 endpoints offer enhanced functionality
- Migration path from V1 to V2 documented

### API Contract Specifications

#### V2 API Contract

**Request Format**:

```
GET /api/productos/v2/list?
    page={int}&
    per_page={int}&
    sort={field}:{order}&
    marca={string}&
    familia={string}&
    pvp_min={float}&
    pvp_max={float}&
    bc3_product_type={string}&
    bc3_has_descripcion_corta={bool}&
    buscar={string}
```

**Response Format**:

```json
{
  "items": [
    {
      "codigo": "P001",
      "descripcion": "LED Panel",
      "marca": "Disano",
      "familia": "Iluminación",
      "pvp": 89.99,
      "bc3_descripcion_corta": "Panel LED 600x600",
      "bc3_product_type": "columna",
      "bc3_descripcion_completa": "Panel LED 600x600 18W"
    }
  ],
  "pagination": {
    "total_items": 150,
    "total_pages": 8,
    "current_page": 1,
    "per_page": 20,
    "has_next": true,
    "has_previous": false
  },
  "filters_applied": {
    "marca": "Disano",
    "pvp_min": 50.0,
    "pvp_max": 200.0
  },
  "sorting_applied": {
    "field": "precio",
    "order": "desc"
  }
}
```

**Error Response**:

```json
{
  "error": {
    "code": "INVALID_SORT_FIELD",
    "message": "Sort field must be one of: codigo, descripcion, marca, familia, pvp, bc3_descripcion_corta, bc3_product_type",
    "details": {
      "invalid_field": "invalid_field_name"
    }
  }
}
```

#### V1 API Contract (Unchanged)

**Request Format**:

```
GET /api/productos/list?
    limit={int}&
    marca={string}&
    familia={string}&
    buscar={string}
```

**Response Format**:

```json
[
  {
    "codigo": "P001",
    "descripcion": "LED Panel",
    "marca": "Disano",
    "familia": "Iluminación",
    "pvp": 89.99
  }
]
```

---

## Technical Constraints

### Hexagonal Architecture Constraints

#### HC-1: Layer Separation

- **Domain Layer**: Contains only business logic, entities, repository interfaces
- **Application Layer**: Contains DTOs and use case orchestration
- **Infrastructure Layer**: Contains repository implementations, caching
- **HTTP Layer**: Contains FastAPI routers, no business logic

#### HC-2: Dependency Inversion

- Infrastructure layer depends on domain interfaces
- HTTP layer depends on application DTOs
- No circular dependencies between layers

#### HC-3: Dependency Injection

- All components injected via FastAPI `Depends()`
- Repository implementations are swappable
- Services are stateless and testable

### TDD Methodology Constraints

#### TC-1: Test-First Development

- Write failing test (RED)
- Implement minimum code to pass test (GREEN)
- Refactor for quality (REFACTOR)

#### TC-2: Test Coverage

- Unit tests for DTOs and business logic
- Integration tests for repository and service layers
- Acceptance tests for HTTP endpoints
- > 80% test coverage for new code

#### TC-3: Test Quality

- Tests are deterministic and isolated
- Tests verify business rules, not implementation details
- Tests are fast (< 1 second per test)

### Cache Integration Constraints

#### CC-1: Cache Strategy

- Leverage Fase 4.1 cache infrastructure
- Cache keys based on complete DTO hash
- TTL: 5 minutes for paginated results

#### CC-2: Cache Invalidation

- Invalidate on product updates
- Invalidate on product creates/deletes
- Pattern-based invalidation for paginated queries

#### CC-3: Cache Warming

- Warm cache for popular queries on startup
- Page 1 queries for common filters
- Queries with high cache hit rates

### BC3-Suite Constraints

#### BC-1: Data Format Compliance

- Maintain BC3 data format compatibility
- Preserve BC3-specific fields (bc3_descripcion_corta, bc3_product_type)
- Support BC3 business rules and constraints

#### BC-2: Business Logic Compliance

- BC3 product types validation
- BC3-specific filtering rules
- BC3 output format requirements

---

## Acceptance Criteria

### Overall Acceptance Criteria

#### AC-1: Functional Completeness

- [ ] All product list endpoints support pagination
- [ ] All product list endpoints support sorting
- [ ] All product list endpoints support filtering
- [ ] V1 endpoints maintain backward compatibility
- [ ] BC3-specific filtering implemented

#### AC-2: Performance Targets

- [ ] P95 response time < 200ms for paginated queries
- [ ] P99 response time < 500ms for paginated queries
- [ ] COUNT query performance < 50ms
- [ ] Cache hit rate > 50% for paginated queries

#### AC-3: Quality Gates

- [ ] Test coverage > 80% for new code
- [ ] Zero mypy errors
- [ ] All existing tests pass
- [ ] TDD methodology followed (RED → GREEN → REFACTOR)

#### AC-4: Architecture Compliance

- [ ] Hexagonal architecture principles followed
- [ ] No direct database access in HTTP layer
- [ ] Dependency injection for all components
- [ ] DTO pattern for input/output validation

### Feature-Specific Acceptance Criteria

#### F1: Pagination AC

- [ ] Pagination request DTO validates page ≥ 1
- [ ] Pagination request DTO validates 1 ≤ per_page ≤ 100
- [ ] Repository returns correct offset based on page/per_page
- [ ] Repository returns total count matching filters
- [ ] Service calculates correct total_pages from total_count
- [ ] Service sets correct has_next/previous flags
- [ ] Response includes all required metadata fields
- [ ] Default page is 1
- [ ] Default per_page is 20

#### F2: Sorting AC

- [ ] Sort criteria DTO validates field against whitelist
- [ ] Sort criteria DTO validates order as "asc" or "desc"
- [ ] Repository applies correct SQLAlchemy order_by function
- [ ] Repository handles invalid sort fields gracefully
- [ ] Default sort is codigo asc
- [ ] Sorting applies after filtering
- [ ] Response includes sorting_applied field
- [ ] Multi-sort support for multiple fields

#### F3: Advanced Filtering AC

- [ ] Filter criteria DTO validates marca/familia as optional strings
- [ ] Filter criteria DTO validates pvp_min/pvp_max as ≥ 0
- [ ] Filter criteria DTO validates pvp_min ≤ pvp_max
- [ ] Repository applies marca filter with exact match
- [ ] Repository applies familia filter with exact match
- [ ] Repository applies pvp_min/pvp_max range filters
- [ ] Repository applies bc3_product_type filter with exact match
- [ ] Repository applies bc3_has_descripcion_corta boolean filter
- [ ] Repository applies text search with ILIKE pattern
- [ ] Text search applies to all relevant fields
- [ ] Multiple filters use AND logic
- [ ] Empty filter values are ignored
- [ ] Response includes filters_applied field

#### F4: Backward Compatibility AC

- [ ] V1 endpoints maintain existing request signature
- [ ] V1 endpoints return existing response format
- [ ] V1ToV2Adapter converts V1 params to V2 DTO
- [ ] V1ToV2Adapter converts V2 response to V1 format
- [ ] V1 endpoints use same business logic as V2
- [ ] Zero breaking changes for V1 consumers
- [ ] V1 deprecation warnings in documentation

### Rollback Criteria

#### RC-1: Critical Performance Regression

- P95 response time > 300ms for paginated queries (rollback threshold)
- Memory usage > 150MB per paginated query
- COUNT query performance > 100ms

#### RC-2: Breaking Changes

- Any V1 endpoint returns different response format
- Any V1 endpoint changes request signature
- Breaking changes in V2 API contract

#### RC-3: Quality Gate Failures

- Test coverage < 70% (rollback threshold)
- Mypy errors introduced
- Existing tests failing

#### RC-4: Architecture Violations

- Direct database access in HTTP layer
- Circular dependencies between layers
- Breaking hexagonal architecture principles

---

## Risks & Mitigations

### Technical Risks

#### TR-1: COUNT Query Performance

**Risk**: COUNT queries may be slow for large datasets (>100k rows)

**Impact**: High - P95 response time may exceed targets

**Mitigation**:

- Use SQLAlchemy count optimizations
- Add database indexes for filtered fields
- Consider COUNT estimation for large datasets
- Cache COUNT results with shorter TTL (2 min)

#### TR-2: Cache Complexity

**Risk**: Cache invalidation may be complex with dynamic filters

**Impact**: Medium - Inconsistent cache state

**Mitigation**:

- TTL-based expiration (5 min)
- Pattern-based invalidation on writes
- Monitor cache hit/miss ratios
- Implement cache warming for popular queries

#### TR-3: Memory Usage

**Risk**: Loading large datasets may cause memory issues

**Impact**: Medium - Potential out-of-memory errors

**Mitigation**:

- Use generators in repository layer
- Limit per_page to 100 items
- Monitor memory usage in tests
- Add memory usage monitoring

#### TR-4: Integration Complexity

**Risk**: Integration with existing hexagonal architecture may introduce bugs

**Impact**: High - May break existing functionality

**Mitigation**:

- Extensive integration testing
- Maintain existing tests passing
- Incremental implementation
- Code review for architecture compliance

### Business Risks

#### BR-1: V1 Consumer Impact

**Risk**: V1 consumers may encounter issues despite backward compatibility

**Impact**: Medium - Potential business disruption

**Mitigation**:

- Maintain V1 signature exactly
- Extensive V1 endpoint testing
- Monitor V1 endpoint performance
- Deprecation notice with migration timeline

#### BR-2: Performance Regression

**Risk**: Pagination may introduce performance regression

**Impact**: High - Degraded user experience

**Mitigation**:

- Performance benchmarks before/after
- Cache integration (Fase 4.1)
- Database optimization (indexes)
- Continuous performance monitoring

#### BR-3: Feature Complexity

**Risk**: Advanced filtering may be too complex for users

**Impact**: Low - Poor adoption

**Mitigation**:

- Clear API documentation
- Example queries for common use cases
- Progressive disclosure in documentation
- User testing with API consumers

### Implementation Risks

#### IR-1: Timeline Overrun

**Risk**: Estimated effort may be insufficient

**Impact**: Medium - Delayed delivery

**Mitigation**:

- Phased implementation approach
- Regular checkpoint reviews
- Defer non-essential features
- Buffer time in estimates

#### IR-2: Test Coverage

**Risk**: Complex filtering logic may have gaps in test coverage

**Impact**: Medium - Potential bugs in production

**Mitigation**:

- TDD methodology enforced
- > 80% test coverage target
- Extensive integration testing
- Edge case testing

#### IR-3: Team Availability

**Risk**: Key team members may be unavailable

**Impact**: Medium - Delayed knowledge transfer

**Mitigation**:

- Comprehensive documentation
- Code review process
- Pair programming for complex features
- Knowledge sharing sessions

---

## Timeline & Milestones

### Estimated Effort

| Phase | Activities | Estimated Effort |
|-------|-----------|------------------|
| Phase 1: Core DTOs + Repository | DTO design, repository interface extension, repository implementation | 2-3 hours |
| Phase 2: Service Layer + Cache | Domain service methods, cache integration, cache invalidation strategy | 2 hours |
| Phase 3: HTTP Layer + V1 Compatibility | V2 endpoints, V1 adapters, backward compatibility tests | 2-3 hours |
| Phase 4: Monitoring + Optimization | Performance monitoring, query optimization, cache tuning, documentation | 1-2 hours |
| **Total** | | **8-10 hours** |

### Milestones

#### Milestone 1: Core Infrastructure Complete (Phase 1)

**Timeline**: 2-3 hours after start
**Deliverables**:

- DTOs created and validated
- Repository interface extended
- Repository implementation complete
- Unit tests for DTOs and repository
- Integration tests for repository pagination

**Success Criteria**:

- All unit tests passing
- All integration tests passing
- Zero mypy errors
- Repository returns correct paginated results

#### Milestone 2: Service Layer + Cache Complete (Phase 2)

**Timeline**: 4-5 hours after start
**Deliverables**:

- Domain service methods implemented
- Cache integration complete
- Cache invalidation strategy implemented
- Integration tests for service layer
- Cache hit/miss tests

**Success Criteria**:

- Cache hit rate > 50% for popular queries
- P95 response time < 200ms
- Cache invalidation working correctly
- All tests passing

#### Milestone 3: HTTP Layer Complete (Phase 3)

**Timeline**: 6-8 hours after start
**Deliverables**:

- V2 endpoints implemented
- V1 adapters implemented
- Backward compatibility tests passing
- Acceptance tests for all endpoints
- OpenAPI documentation complete

**Success Criteria**:

- All V2 endpoints returning correct responses
- All V1 endpoints unchanged
- Acceptance tests passing
- OpenAPI documentation examples working

#### Milestone 4: Production Ready (Phase 4)

**Timeline**: 8-10 hours after start
**Deliverables**:

- Performance monitoring implemented
- Database indexes optimized
- Cache tuned for production
- Documentation complete
- Migration guide for V1 consumers

**Success Criteria**:

- P95 response time < 200ms
- Test coverage > 80%
- All acceptance criteria met
- Ready for production deployment

### Dependencies

#### Internal Dependencies

- Fase 3: Architecture Hexagonal Migration (completed)
- Fase 4.1: Performance Optimization (completed - cache infrastructure)
- Existing test infrastructure
- Existing database schema

#### External Dependencies

- None (self-contained implementation)

#### Dependency Analysis

- **Critical Path**: Phase 1 → Phase 2 → Phase 3 → Phase 4
- **Parallelization**: Limited - phases must be sequential
- **Risk**: Dependencies are satisfied (Fase 3 and 4.1 complete)

---

## Next Steps

1. **Approve Proposal**: Stakeholder review and approval
2. **Create Spec**: Detailed technical specification
3. **Create Design**: Detailed design document
4. **Create Tasks**: Implementation tasks with estimates
5. **Implementation**: Execute phases following TDD methodology

---

## Appendix

### A. Glossary

- **DTO**: Data Transfer Object - Pattern for transferring data between layers
- **Pagination**: Breaking large result sets into smaller chunks (pages)
- **Sorting**: Ordering results by one or more fields
- **Advanced Filtering**: Applying multiple filter criteria to queries
- **Backward Compatibility**: Maintaining compatibility with existing API consumers
- **Cache Warming**: Pre-populating cache with popular query results
- **Cache Invalidation**: Removing cached data when underlying data changes

### B. References

- Fase 3: Architecture Hexagonal Migration (archived)
- Fase 4.1: Performance Optimization (archived)
- BC3-Suite Documentation
- FastAPI Documentation
- SQLAlchemy Documentation
- REST API Pagination Best Practices

### C. OpenAPI Schema

See implementation for complete OpenAPI schema.

---

**Proposal Version**: 1.0  
**Created**: 2026-07-12T12:15:00Z  
**Author**: el Gentleman (Pi Coding Agent)  
**Status**: 📝 Draft - Pending Approval  
**Next Phase**: Specification
