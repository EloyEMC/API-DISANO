# Fase 4.1: Performance Optimization - Tasks

## Phase 4.1.1: Database Indexing

### TASK-4.1.1.1: Analyze Query Patterns

**Description**: Analyze current query patterns to identify indexing opportunities.

**Acceptance Criteria**:

- [ ] Query analysis completed for all major endpoints
- [ ] Most frequent queries identified
- [ ] Fields requiring indexing documented
- [ ] Query execution times baseline established

**TDD Approach**:

```python
# tests/performance/test_query_analysis.py
def test_identify_frequent_queries():
    """Test that frequent queries are properly identified"""
    # Analyze query patterns
    frequent_queries = analyze_query_patterns()
    
    # Verify most frequent queries identified
    assert len(frequent_queries) >= 5
    assert all('query' in q for q in frequent_queries)
    assert all('frequency' in q for q in frequent_queries)
```

**Dependencies**: None

---

### TASK-4.1.1.2: Add Strategic Indexes

**Description**: Add indexes to frequently queried fields in productos_clean view.

**Acceptance Criteria**:

- [ ] Indexes created for codigo, descripcion, marca, familia fields
- [ ] Composite indexes for common query combinations
- [ ] Index sizes measured and documented
- [ ] Query performance improved by > 20%

**TDD Approach**:

```python
# tests/integration/test_database_indexes.py
def test_indexes_exist_on_frequently_queried_fields():
    """Test that indexes exist on frequently queried fields"""
    from app.infrastructure.database.connection import SessionLocal
    from sqlalchemy import text
    
    session = SessionLocal()
    result = session.execute(text("SELECT name FROM sqlite_master WHERE type='index'"))
    indexes = [row[0] for row in result.fetchall()]
    session.close()
    
    # Verify indexes exist
    assert any('idx_codigo' in idx for idx in indexes)
    assert any('idx_marca' in idx for idx in indexes)
    assert any('idx_familia' in idx for idx in indexes)
```

**Dependencies**: TASK-4.1.1.1

---

### TASK-4.1.1.3: Run ANALYZE for Query Optimization

**Description**: Execute SQLite ANALYZE command to update query planner statistics.

**Acceptance Criteria**:

- [ ] ANALYZE command executed successfully
- [ ] Query statistics updated
- [ ] Performance improvement verified
- [ ] Benchmark results documented

**TDD Approach**:

```python
# tests/integration/test_query_optimization.py
def test_analyze_updates_query_statistics():
    """Test that ANALYZE updates query statistics"""
    from app.infrastructure.database.connection import SessionLocal
    from sqlalchemy import text
    
    session = SessionLocal()
    # Run ANALYZE
    session.execute(text("ANALYZE productos_clean"))
    session.commit()
    session.close()
    
    # Verify statistics updated
    result = session.execute(text("SELECT stat FROM sqlite_stat1 WHERE tbl='productos_clean'"))
    stats = result.fetchall()
    assert len(stats) > 0  # Statistics exist
```

**Dependencies**: TASK-4.1.1.2

---

## Phase 4.1.2: Query Optimization

### TASK-4.1.2.1: Identify N+1 Query Problems

**Description**: Identify and document N+1 query patterns in the codebase.

**Acceptance Criteria**:

- [ ] N+1 query patterns identified
- [ ] Impact on performance measured
- [ ] Optimization strategy documented
- [ ] Fix priority established

**TDD Approach**:

```python
# tests/performance/test_n_plus_one_detection.py
def test_no_n_plus_one_queries_in_product_search():
    """Test that product search doesn't trigger N+1 queries"""
    from app.domain.services.producto import ProductoService
    from app.infrastructure.repositories.producto import SQLAlchemyProductoRepository
    from app.infrastructure.database.connection import SessionLocal
    
    session = SessionLocal()
    repository = SQLAlchemyProductoRepository(session)
    service = ProductoService(repository)
    
    # Monitor queries
    query_count = count_queries(lambda: service.buscar_productos(dto))
    
    # Should use single query (or minimal number)
    assert query_count <= 2  # Allow 1-2 queries, not N+1
```

**Dependencies**: TASK-4.1.1.3

---

### TASK-4.1.2.2: Optimize SQLAlchemy Queries

**Description**: Optimize SQLAlchemy queries using joinedload, selectinload, and other techniques.

**Acceptance Criteria**:

- [ ] Eager loading applied where appropriate
- [ ] Query count reduced by 33%
- [ ] Response time improved by 25%
- [ ] All tests still passing

**TDD Approach**:

```python
# tests/integration/test_query_optimization.py
def test_optimized_queries_reduced_count():
    """Test that optimized queries reduce database calls"""
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    # Monitor query count
    initial_queries = count_database_queries()
    response = client.get("/api/productos/v2/list?buscar=test&limit=10")
    final_queries = count_database_queries()
    
    queries_used = final_queries - initial_queries
    assert queries_used <= 2  # Should use 1-2 queries maximum
```

**Dependencies**: TASK-4.1.2.1

---

### TASK-4.1.2.3: Optimize BC3 Query Performance

**Description**: Optimize BC3-specific queries for better performance.

**Acceptance Criteria**:

- [ ] BC3 statistics query optimized
- [ ] BC3 search queries improved
- [ ] P95 response time < 50ms for BC3 endpoints
- [ ] Cache keys defined for BC3 data

**TDD Approach**:

```python
# tests/integration/test_bc3_performance.py
def test_bc3_stats_performance_optimized():
    """Test that BC3 stats endpoint is optimized"""
    import time
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    # Measure response time
    start = time.time()
    response = client.get("/api/bc3/stats")
    elapsed = time.time() - start
    
    assert response.status_code == 200
    assert elapsed < 0.05  # < 50ms
```

**Dependencies**: TASK-4.1.2.2

---

## Phase 4.1.3: Caching Layer

### TASK-4.1.3.1: Design Cache Strategy

**Description**: Design caching strategy including cache keys, TTL, and invalidation rules.

**Acceptance Criteria**:

- [ ] Cache key pattern defined
- [ ] TTL values established per data type
- [ ] Cache invalidation strategy documented
- [ ] Cache warming strategy defined

**TDD Approach**:

```python
# tests/unit/cache/test_cache_strategy.py
def test_cache_key_generation_consistent():
    """Test that cache keys are generated consistently"""
    from app.infrastructure.cache.cache_manager import CacheManager
    
    manager = CacheManager()
    key1 = manager.generate_key("product", "TEST001")
    key2 = manager.generate_key("product", "TEST001")
    
    assert key1 == key2  # Consistent key generation
```

**Dependencies**: None

---

### TASK-4.1.3.2: Implement Redis Cache

**Description**: Implement Redis cache layer for expensive operations.

**Acceptance Criteria**:

- [ ] Redis connection configured
- [ ] Cache manager implemented
- [ ] Cache decorators added to services
- [ ] Fallback when Redis unavailable

**TDD Approach**:

```python
# tests/integration/test_redis_cache.py
def test_redis_cache_hit_improves_performance():
    """Test that cache hit improves performance"""
    import time
    from app.infrastructure.cache.cache_manager import CacheManager
    
    cache = CacheManager()
    
    # First call (cache miss)
    start = time.time()
    result = cache.get_or_compute("key", lambda: expensive_operation())
    miss_time = time.time() - start
    
    # Second call (cache hit)
    start = time.time()
    result = cache.get_or_compute("key", lambda: expensive_operation())
    hit_time = time.time() - start
    
    # Cache hit should be faster
    assert hit_time < miss_time
```

**Dependencies**: TASK-4.1.3.1

---

### TASK-4.1.3.3: Add Cache to Expensive Operations

**Description**: Add caching to expensive operations like statistics and search results.

**Acceptance Criteria**:

- [ ] Product search results cached
- [ ] BC3 statistics cached
- [ ] Family statistics cached
- [ ] Cache hit rate > 60%

**TDD Approach**:

```python
# tests/integration/test_cache_integration.py
def test_product_search_cache_improves_performance():
    """Test that product search caching improves performance"""
    import time
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    # First request (cache miss)
    start = time.time()
    response1 = client.get("/api/productos/v2/list?buscar=test&limit=10")
    miss_time = time.time() - start
    
    # Second request (cache hit)
    start = time.time()
    response2 = client.get("/api/productos/v2/list?buscar=test&limit=10")
    hit_time = time.time() - start
    
    assert response1.json() == response2.json()  # Same results
    assert hit_time < miss_time  # Cache hit faster
```

**Dependencies**: TASK-4.1.3.2

---

## Phase 4.1.4: Connection Pooling

### TASK-4.1.4.1: Configure Connection Pool

**Description**: Configure SQLAlchemy connection pool for optimal performance.

**Acceptance Criteria**:

- [ ] Pool size configured
- [ ] Pool overflow handling configured
- [ ] Connection timeout configured
- [ ] Pool monitoring implemented

**TDD Approach**:

```python
# tests/integration/test_connection_pool.py
def test_connection_pool_configured():
    """Test that connection pool is properly configured"""
    from app.infrastructure.database.connection import engine
    
    # Verify pool settings
    assert engine.pool.size() > 0  # Pool has configured size
    assert engine.pool.max_overflow > 0  # Overflow handling configured
```

**Dependencies**: TASK-4.1.3.3

---

### TASK-4.1.4.2: Monitor Connection Pool Usage

**Description**: Implement connection pool usage monitoring.

**Acceptance Criteria**:

- [ ] Pool usage metrics collected
- [ ] Connection exhaustion alerts
- [ ] Pool performance logging
- [ ] Optimization recommendations

**TDD Approach**:

```python
# tests/integration/test_pool_monitoring.py
def test_connection_pool_usage_monitored():
    """Test that connection pool usage is monitored"""
    from app.infrastructure.database.connection import get_pool_stats
    
    stats = get_pool_stats()
    
    assert "size" in stats
    assert "checked_in" in stats
    assert "overflow" in stats
    assert "checked_out" in stats
```

**Dependencies**: TASK-4.1.4.1

---

## Phase 4.1.5: Monitoring & Metrics

### TASK-4.1.5.1: Collect Performance Metrics

**Description**: Implement performance metrics collection.

**Acceptance Criteria**:

- [ ] Response time metrics collected
- [ ] Query execution time logged
- [ ] Cache performance monitored
- [ ] Metrics export format defined

**TDD Approach**:

```python
# tests/integration/test_performance_metrics.py
def test_performance_metrics_collected():
    """Test that performance metrics are collected"""
    from app.monitoring.metrics import MetricsCollector
    
    collector = MetricsCollector()
    
    # Record metric
    collector.record("response_time", 0.050, tags={"endpoint": "/api/productos/v2/list"})
    
    # Verify metric collected
    metrics = collector.get_metrics("response_time")
    assert len(metrics) > 0
    assert metrics[0]["value"] == 0.050
```

**Dependencies**: TASK-4.1.4.2

---

### TASK-4.1.5.2: Create Performance Dashboard

**Description:** Create performance dashboard/report.

**Acceptance Criteria**:

- [ ] Performance report generated
- [ ] Key metrics displayed
- [ ] Trends identified
- [ ] Recommendations provided

**TDD Approach**:

```python
# tests/integration/test_performance_dashboard.py
def test_performance_dashboard_generated():
    """Test that performance dashboard is generated"""
    from app.monitoring.dashboard import generate_dashboard
    
    dashboard = generate_dashboard()
    
    assert "response_times" in dashboard
    assert "cache_performance" in dashboard
    assert "database_queries" in dashboard
    assert "recommendations" in dashboard
```

**Dependencies**: TASK-4.1.5.1

---

## Dependencies

```
TASK-4.1.1.1 → TASK-4.1.1.2 → TASK-4.1.1.3
                        ↓
                TASK-4.1.2.1 → TASK-4.1.2.2 → TASK-4.1.2.3
                        ↓
                TASK-4.1.3.1 → TASK-4.1.3.2 → TASK-4.1.3.3
                        ↓
                TASK-4.1.4.1 → TASK-4.1.4.2
                        ↓
                TASK-4.1.5.1 → TASK-4.1.5.2
```

---

## Execution Order

**Sequential execution** (each phase depends on previous):

1. Phase 4.1.1 (Database Indexing)
2. Phase 4.1.2 (Query Optimization)
3. Phase 4.1.3 (Caching Layer)
4. Phase 4.1.4 (Connection Pooling)
5. Phase 4.1.5 (Monitoring & Metrics)

---

## Estimated Time

| Phase | Estimated Time |
|-------|----------------|
| 4.1.1: Database Indexing | 2 hours |
| 4.1.2: Query Optimization | 2 hours |
| 4.1.3: Caching Layer | 3 hours |
| 4.1.4: Connection Pooling | 1 hour |
| 4.1.5: Monitoring & Metrics | 2 hours |
| **Total** | **10 hours** |

---

## Completion Criteria

- ✅ P95 response time < 50ms (50% improvement)
- ✅ Average response time < 10ms
- ✅ Database queries reduced by 33%
- ✅ Cache hit rate > 60%
- ✅ All existing tests passing
- ✅ Performance benchmarks documented
- ✅ Monitoring dashboard functional
