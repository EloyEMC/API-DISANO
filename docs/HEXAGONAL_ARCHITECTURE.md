# 🏛️ Hexagonal Architecture - API-DISANO

## 📋 Overview

API-DISANO migrated from legacy monolithic architecture to **Hexagonal Architecture** (Ports and Adapters Pattern). This provides:

- **Separation of Concerns**: Business logic separated from infrastructure
- **Testability**: Easy to test domain logic with mocks
- **Maintainability**: Clear boundaries between layers
- **Dependency Inversion**: High-level modules don't depend on low-level modules

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    HTTP Layer (Ports)                    │
│         app/interfaces/http/* (FastAPI routers)         │
├─────────────────────────────────────────────────────────┤
│                   Application Layer                      │
│              app/application/dto/* (DTOs)                │
├─────────────────────────────────────────────────────────┤
│                    Domain Layer                          │
│      app/domain/{entities,services,repositories}/       │
│         (Business logic + interfaces)                    │
├─────────────────────────────────────────────────────────┤
│                Infrastructure Layer                       │
│     app/infrastructure/{repositories,models,database}/   │
│          (SQLAlchemy implementations)                    │
├─────────────────────────────────────────────────────────┤
│              External Systems (Adapters)                 │
│                    SQLite Database                        │
└─────────────────────────────────────────────────────────┘
```

## 📁 Directory Structure

```python
app/
├── interfaces/               # HTTP Layer (Ports)
│   └── http/
│       ├── __init__.py
│       ├── productos.py     # Product endpoints with DI
│       ├── familias.py      # Families endpoints with DI
│       └── bc3.py           # BC3 endpoints with DI
├── application/             # Application Layer
│   └── dto/
│       ├── __init__.py
│       └── producto.py      # DTOs for request/response
├── domain/                  # Domain Layer (Business Logic)
│   ├── entities/
│   │   ├── __init__.py
│   │   ├── producto.py      # ProductoEntity
│   │   └── familia.py       # FamiliaEntity
│   ├── repositories/        # Repository Interfaces
│   │   ├── __init__.py
│   │   ├── producto.py      # ProductoRepositoryInterface
│   │   └── familia.py       # FamiliaRepositoryInterface
│   ├── services/            # Domain Services
│   │   ├── __init__.py
│   │   ├── producto.py      # ProductoService
│   │   └── familia.py       # FamiliaService
│   └── exceptions/          # Domain Exceptions
│       ├── __init__.py
│       └── not_found.py     # Not found exceptions
└── infrastructure/          # Infrastructure Layer (Adapters)
    ├── database/
    │   ├── __init__.py
    │   └── connection.py    # SQLAlchemy setup
    ├── models/              # SQLAlchemy Models
    │   ├── __init__.py
    │   └── producto_clean.py
    └── repositories/        # Repository Implementations
        ├── __init__.py
        ├── producto.py      # SQLAlchemyProductoRepository
        └── familia.py       # SQLAlchemyFamiliaRepository
```

## 🔗 Dependency Flow

### HTTP → Domain → Infrastructure → Database

```python
# HTTP Layer (Port)
@router.get("/api/productos/v2/list")
async def buscar_productos_v2(
    service: ProductoService = Depends(get_producto_service)  # DI
):
    # Uses domain service
    dto = ProductoSearchDTO(buscar="test", limit=10)
    entities = service.buscar_productos(dto)
    return [ProductoResponseDTO.from_entity(e) for e in entities]

# Domain Layer (Business Logic)
class ProductoService:
    def __init__(self, repository: ProductoRepositoryInterface):  # DI
        self.repository = repository
    
    def buscar_productos(self, dto: ProductoSearchDTO):
        # Business logic
        # Uses repository interface (not concrete implementation)
        return self.repository.buscar_productos(...)

# Infrastructure Layer (Adapter)
class SQLAlchemyProductoRepository(ProductoRepositoryInterface):
    def __init__(self, session: Session):  # DI
        self.session = session
    
    def buscar_productos(self, ...):
        # Database access
        return self.session.query(...).all()
```

## 🧪 Testing Approach

### Unit Tests (Domain Layer)

```python
# Test domain logic with mock repository
def test_producto_service_validation():
    mock_repo = Mock(spec=ProductoRepositoryInterface)
    service = ProductoService(mock_repo)
    
    # Test business logic
    result = service.buscar_productos(dto)
    assert result is not None
```

### Integration Tests (Full DI Flow)

```python
# Test HTTP → Depends → Service → Repository → Database
def test_di_flow_http_to_database(client):
    response = client.get("/api/productos/v2/list?buscar=test&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
```

## 🔑 Key Principles

1. **Dependency Inversion**: High-level modules (domain) don't depend on low-level modules (infrastructure)
2. **Interface Segregation**: Repository interfaces define contracts
3. **Single Responsibility**: Each layer has one clear responsibility
4. **Open/Closed**: Open for extension, closed for modification
5. **Dependency Injection**: FastAPI Depends() manages dependencies

## 📊 Migration Benefits

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Test Coverage | 39% | 49% | +10pp |
| Architecture | Monolithic | Hexagonal | ✅ |
| Testability | Hard | Easy | ✅ |
| Maintainability | Medium | High | ✅ |
| Legacy Code | 6 files | 0 files | ✅ |

## 🚀 Usage Examples

### Creating a Service

```python
from app.domain.services.producto import ProductoService
from app.infrastructure.repositories.producto import SQLAlchemyProductoRepository
from app.infrastructure.database.connection import SessionLocal

# Create service with DI
session = SessionLocal()
repository = SQLAlchemyProductoRepository(session)
service = ProductoService(repository)

# Use service
productos = service.buscar_productos(dto)
session.close()
```

### Using HTTP Endpoints

```python
import requests

# V2 endpoints (hexagonal)
response = requests.get(
    "http://localhost:8000/api/productos/v2/list",
    params={"buscar": "test", "limit": 10}
)
productos = response.json()

# V1 endpoints (backward compatible)
response = requests.get(
    "http://localhost:8000/api/productos/",
    params={"buscar": "test", "limit": 100}
)
productos = response.json()
```

## 📚 Resources

- **Hexagonal Architecture**: <https://alistair.cockburn.us/hexagonal-architecture/>
- **Ports and Adapters**: <https://herbertograca.com/2017/09/14/ports-adapters-architecture/>
- **Clean Architecture**: <https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html>

## 🔄 Migration History

- **Phase 3.4**: Hexagonal Architecture Implementation
- **Phase 3.5**: Testing Migration with TDD
- **Phase 3.6**: Migrate remaining routers (familias, bc3)
- **Phase 3.7**: Cleanup legacy code

---

**Last Updated**: 2026-07-11
**Architecture Version**: 2.0 (Hexagonal)
**Status**: ✅ Complete and Verified
