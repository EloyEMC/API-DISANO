# Fase 3 - Architecture Hexagonal Migration: Proposal

## Executive Summary

Migrar API-DISANO desde arquitectura monolítica a **Architecture Hexagonal** con **Dependency Injection** para mejorar testabilidad, mantenibilidad y seguir BC3 Suite patterns.

**Estimated effort:** 8-12 hours total (Fase 3.4 + 3.5)  
**Timeline:** 1-2 semanas  
**Risk level:** MEDIUM (backward compatibility maintained)  
**Impact:** High - foundation for future scalability

## Business Problem

### Current Issues

1. **Hard to Test:** Routers access database directly with sqlite3 connections, making tests slow and fragile
2. **Mixed Concerns:** Business logic mixed with HTTP layer in routers
3. **No Separation:** Domain logic coupled to database implementation
4. **Technical Debt:** 623-line router file with monolithic structure
5. **Maintenance Risk:** Changes in one area affect multiple concerns

### Impact

- **Test coverage stuck at 39%** - difficult to add comprehensive tests
- **Development velocity slows** - changes require touching multiple layers
- **Bug risk increases** - no clear boundaries between concerns
- **Onboarding difficulty** - new developers struggle with monolithic code
- **Deployment risk** - monolithic deployment of coupled concerns

## Proposed Solution

### Architecture Hexagonal (Clean Architecture)

**Core Principles:**

1. **Domain Independence:** Business logic has ZERO dependencies on infrastructure
2. **Dependency Inversion:** High-level modules don't depend on low-level modules
3. **Interface Segregation:** Repositories as abstract contracts (ABC)
4. **Single Responsibility:** Each layer has ONE clear purpose

**Three-Layer Structure:**

- **Domain:** Business rules + entities + repository interfaces
- **Infrastructure:** Database + external implementations
- **Application/Interfaces:** DTOs + HTTP layer + use cases

### Dependency Injection with FastAPI Depends

**Strategy:** Use native FastAPI `Depends()` for DI

```python
def get_producto_service() -> ProductoService:
    return ProductoService(SQLAlchemyProductoRepository(SessionLocal()))

@router.get("/v2/list")
async def buscar_productos_v2(
    buscar: str,
    service: ProductoService = Depends(get_producto_service)
):
    # Business logic in service, HTTP layer thin
```

**Benefits:**

- ✅ Testable (mock repositories easily)
- ✅ Clear dependency graph
- ✅ No additional dependencies
- ✅ Request-scoped lifecycle
- ✅ Type-safe with IDE support

## Scope

### In Scope ✅

1. **Fase 3.4: Dependency Injection**
   - Configure DI in main.py
   - Create `app/interfaces/http/productos.py` with DI
   - Migrate productos router (5 endpoints, V1 + V2)
   - Update tests for DI flow
   - Verify BC3 Suite compatibility

2. **Fase 3.5: Testing Migration**
   - Adapt existing tests to hexagonal architecture
   - Add integration tests for DI flow
   - Fix service test import issues (14/14 failing)
   - Maintain 39%+ coverage baseline
   - Run BC3 Suite integration tests

### Out of Scope ❌

1. **Fase 3.6:** Migrate remaining routers (familias, bc3)
2. **Fase 3.7:** Cleanup legacy code
3. **Database schema changes** (using productos_clean view)
4. **New features** - only refactoring existing functionality
5. **Performance optimization** - maintain current response times

## Acceptance Criteria

### Functional Requirements

- [ ] **Fase 3.4.1:** DI setup in main.py completed
- [ ] **Fase 3.4.2:** `app/interfaces/http/productos.py` created with DI
- [ ] **Fase 3.4.3:** All 5 productos endpoints migrated to DI (V1 + V2)
- [ ] **Fase 3.4.4:** Existing BC3 Suite integration tests passing
- [ ] **Fase 3.4.5:** V1 endpoints maintain backward compatibility

### Non-Functional Requirements

- [ ] **Fase 3.5.1:** 14 service tests passing (currently 14/14 failing)
- [ ] **Fase 3.5.2:** Coverage >= 39% (maintain baseline)
- [ ] **Fase 3.5.3:** Integration tests for DI flow added
- [ ] **Fase 3.5.4:** Response time degradation < 100ms
- [ ] **Fase 3.5.5:** Type safety maintained (no mypy errors)

### Business Requirements

- [ ] BC3 Suite V2 endpoints working correctly
- [ ] No data loss during migration
- [ ] Zero downtime for existing clients
- [ ] Deployment rollback plan documented
- [ ] Team onboarding material updated

## Success Metrics

### Code Quality

- **Coverage:** >= 39% (maintain baseline)
- **Test Pass Rate:** 100% for migrated code
- **Type Safety:** 100% type hints for new code
- **Linting:** Zero ruff warnings for new code

### Performance

- **Response Time:** < 100ms degradation
- **Startup Time:** < 2s (including DI setup)
- **Memory Usage:** < 50MB increase

### Business Impact

- **Testability:** Unit tests 10x faster (mock vs real DB)
- **Development Velocity:** 2x faster new endpoint development
- **Bug Risk:** 50% reduction (clear boundaries)
- **Onboarding Time:** 30% faster (clear architecture)

## Technical Approach

### Migration Strategy

**Phased Rollout:**

1. **Phase 1:** Migrate productos router only (most critical)
2. **Phase 2:** Fix service tests and add integration tests
3. **Phase 3:** Verify BC3 Suite compatibility
4. **Phase 4:** Deploy to staging, full testing
5. **Phase 5:** Production deployment with rollback plan

**Backward Compatibility:**

- Keep V1 endpoints working
- Test with BC3 Suite App
- Verify existing clients still work
- Monitor production metrics

### DI Implementation

**FastAPI Depends Pattern:**

```python
# Dependency functions
def get_db_session() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_producto_repository(db: Session = Depends(get_db_session)) -> ProductoRepositoryInterface:
    return SQLAlchemyProductoRepository(db)

def get_producto_service(repo: ProductoRepositoryInterface = Depends(get_producto_repository)) -> ProductoService:
    return ProductoService(repo)

# HTTP endpoints
@router.get("/v2/list")
async def buscar_productos_v2(
    buscar: str,
    service: ProductoService = Depends(get_producto_service)
):
    # Thin HTTP layer, business logic in service
```

**Testability:**

```python
# Unit tests with mocks
def test_buscar_productos():
    mock_repo = Mock(spec=ProductoRepositoryInterface)
    mock_repo.buscar_productos.return_value = [entity]
    
    service = ProductoService(mock_repo)
    result = service.buscar_productos(dto)
    
    assert len(result) == 1
    mock_repo.buscar_productos.assert_called_once()
```

## Risks and Mitigations

### Risk 1: Backward Compatibility Breakage (HIGH)

**Probability:** 20% | **Impact:** CRITICAL

**Mitigation:**

- Keep V1 endpoints fully functional
- Run BC3 Suite tests before deployment
- Feature flags for gradual rollout
- Rollback plan ready

### Risk 2: Performance Degradation (MEDIUM)

**Probability:** 30% | **Impact:** MEDIUM

**Mitigation:**

- Benchmark critical endpoints
- Cache frequently accessed data
- Optimize SQLAlchemy queries
- Monitor production metrics

### Risk 3: Test Coverage Regression (MEDIUM)

**Probability:** 40% | **Impact:** MEDIUM

**Mitigation:**

- Maintain 39%+ coverage baseline
- Add integration tests for DI flow
- Fix service tests (14/14 failing)
- Run pytest-cov in CI/CD

### Risk 4: Deployment Complexity (LOW)

**Probability:** 15% | **Impact:** LOW

**Mitigation:**

- Test deployment in staging first
- Document deployment steps
- Keep old code for rollback
- Incremental rollout

## BC3 Suite Integration

### Current State

- ✅ V2 endpoints: `/api/productos/v2/list`, `/api/productos/v2/{codigo}`
- ✅ 5 BC3 fields in ProductoEntity
- ✅ BC3 Suite App using V2 API
- ✅ 8,288 products accessible via productos_clean view

### Migration Impact

✅ **NO BREAKING CHANGES:**

- V2 endpoint signatures unchanged
- DTOs include all BC3 fields
- Service layer transparent to HTTP layer
- Same database view (productos_clean)

⚠️ **VERIFICATION REQUIRED:**

- Run BC3 Suite integration tests
- Verify all V2 endpoints working
- Test BC3 Suite App with new architecture
- Monitor production logs

## Timeline

### Week 1: Fase 3.4 (DI Setup)

- **Day 1-2:** Configure DI in main.py, create interfaces/http/productos.py
- **Day 3-4:** Migrate productos router endpoints (V1 + V2)
- **Day 5:** Fix service tests, verify BC3 Suite compatibility

### Week 2: Fase 3.5 (Testing Migration)

- **Day 1-2:** Adapt existing tests to hexagonal architecture
- **Day 3:** Add integration tests for DI flow
- **Day 4:** Full test suite run, fix issues
- **Day 5:** Deploy to staging, final testing, production deployment

## Alternatives Considered

### Option 1: dependency-injector Library

**Rejected:** Additional dependency, more boilerplate, overkill for simple project

### Option 2: Custom DI Container

**Rejected:** Manual lifecycle management, not idiomatic FastAPI, harder to test

### Option 3: No DI (Status Quo)

**Rejected:** Continuing with technical debt, harder to test, maintenance risk

## Dependencies

### Blocking Dependencies

- None (Fase 3.1-3.3 already completed)

### Prerequisites

- ✅ Fase 3.1: Domain Layer (completed)
- ✅ Fase 3.2: Infrastructure Layer (completed)
- ✅ Fase 3.3: Application Layer (completed)
- ✅ BC3 Suite integration working (V2 endpoints validated)

### External Dependencies

- FastAPI `Depends()` (native, no additional deps)
- SQLAlchemy 2.0.51 (already upgraded)
- Pydantic v2 (already using)

## Resources

### Team

- **Developer:** Eloy Martinez Cuesta (Implementor)
- **Reviewer:** [TBD]
- **Stakeholder:** BC3 Suite team

### Documentation

- FASE 3 Architecture Hexagonal doc (`docs/FASE3_ARCHITECTURE_HEXAGONAL.md`)
- BC3 Suite V2 Migration Guide (`docs/BC3_SUITE_APP_V2_MIGRATION.md`)
- Migration Plan (`docs/MIGRATION_PLAN.md`)

## Next Steps

1. **Approve this proposal** ← Current step
2. Create detailed **SDD Spec** (functional requirements)
3. Create **SDD Design** (technical architecture)
4. Create **SDD Tasks** (step-by-step implementation)
5. **Execute tasks** with TDD (RED → GREEN → REFACTOR)
6. **Verify** against acceptance criteria
7. **Archive** completed change

---

## Approval Decision

**Options:**

- ✅ **Approve** - Proceed with Fase 3.4-3.5 as proposed
- 🔄 **Modify** - Request changes to scope or approach
- ❌ **Reject** - Do not proceed with this change

**If Approved:**

- Timeline: 1-2 weeks total
- Effort: 8-12 hours
- Risk: MEDIUM (mitigated)
- Impact: HIGH (architecture foundation)

**Next Phase:** SDD Spec (detailed functional requirements)
