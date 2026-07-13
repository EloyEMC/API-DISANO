# Fase 3: Architecture Hexagonal Migration Plan

## 🎯 OBJETIVO

Migrar **API-DISANO** de arquitectura monolítica a **Arquitectura Hexagonal** siguiendo patrones BC3-Suite.

## 📊 ESTADO ACTUAL vs OBJETIVO

### **Arquitectura Actual (Monolítica):**

```
app/
├── main.py                    # FastAPI app
├── routers/                   # Routers directos a DB
│   ├── productos.py           # Lógica mezclada con DB
│   ├── familias.py            # Same pattern
│   └── bc3.py                 # BC3 generation logic
├── models.py                  # SQLAlchemy models
├── database.py                # Database connection
├── security/                  # Security modules
├── middleware.py              # Middleware
└── config.py                  # Settings
```

**Problemas:**

- ❌ Routers tienen lógica de negocio + DB mezclados
- ❌ No hay services layer
- ❌ No hay repositories abstracción
- ❌ No hay domain models separados
- ❌ No hay dependency injection
- ❌ Test difícil (requiere DB real)
- ❌ Lógica de negocio acoplada a FastAPI/SQLAlchemy

### **Arquitectura Objetivo (Hexagonal):**

```
app/
├── domain/                    # LÓGICA DE NEGOCIO (Core)
│   ├── entities/              # Domain models (Pydantic/Base)
│   │   ├── producto.py        # ProductoEntity
│   │   ├── familia.py         # FamiliaEntity
│   │   └── bc3_suite.py       # BC3SuiteMappingEntity
│   ├── repositories/          # Repository interfaces
│   │   ├── producto.py        # ProductoRepositoryInterface
│   │   ├── familia.py         # FamiliaRepositoryInterface
│   │   └── bc3_suite.py       # BC3SuiteRepositoryInterface
│   ├── services/              # Business logic services
│   │   ├── producto.py        # ProductoService
│   │   ├── familia.py         # FamiliaService
│   │   └── bc3_suite.py       # BC3SuiteService
│   └── exceptions/            # Domain exceptions
│       ├── validation.py      # Validation errors
│       └── not_found.py       # Not found errors
│
├── infrastructure/            # INFRASTRUCTURA (Implementations)
│   ├── repositories/          # Repository implementations
│   │   ├── producto.py        # SQLAlchemyProductoRepository
│   │   ├── familia.py         # SQLAlchemiaFamiliaRepository
│   │   └── bc3_suite.py       # BC3SuiteRepository
│   ├── models/                # SQLAlchemy models
│   │   ├── producto.py        # ProductoModel
│   │   ├── familia.py         # FamiliaModel
│   │   └── bc3_suite.py       # BC3SuiteMappingModel
│   └── database/              # Database connection
│       ├── connection.py      # Session management
│       └── migrations/        # Alembic migrations
│
├── application/               # APLICACIÓN (Orchestration)
│   ├── dto/                   # Data Transfer Objects
│   │   ├── producto.py        # ProductoCreateDTO, ProductoUpdateDTO
│   │   ├── familia.py         # FamiliaDTO
│   │   └── bc3_suite.py       # BC3SuiteDTO
│   ├── commands/              # Command handlers
│   │   ├── crear_producto.py  # CrearProductoCommand
│   │   ├── actualizar_producto.py
│   │   └── generar_bc3.py     # GenerarBC3Command
│   └── queries/               # Query handlers
│       ├── buscar_productos.py
│       ├── obtener_producto.py
│       └── buscar_por_filtros.py
│
├── interfaces/                # INTERFACES (Adapters)
│   ├── http/                  # FastAPI routers
│   │   ├── productos.py       # HTTP endpoints
│   │   ├── familias.py        # HTTP endpoints
│   │   └── bc3.py             # BC3 endpoints
│   └── cli/                   # CLI commands
│       └── generar_bc3.py     # CLI generator
│
├── config.py                  # Settings
├── main.py                    # Dependency injection setup
└── security/                  # Security modules
```

**Beneficios:**

- ✅ Separación clara de responsabilidades
- ✅ Domain logic independiente de infrastructure
- ✅ Test sin BD (mock repositories)
- ✅ Facilidad de cambiar DB o API
- ✅ Business logic testeable en isolation
- ✅ Single responsibility principle

## 🔄 MIGRACIÓN INCREMENTAL

### **Fase 3.1: Domain Layer** (Week 1)

**Objetivo:** Crear modelos de dominio y repository interfaces

**Archivos nuevos:**

```
app/domain/entities/
├── producto.py                # ProductoEntity (Pydantic)
├── familia.py                 # FamiliaEntity
└── bc3_suite.py               # BC3SuiteMappingEntity

app/domain/repositories/
├── producto.py                # ProductoRepositoryInterface
├── familia.py                 # FamiliaRepositoryInterface
└── bc3_suite.py               # BC3SuiteRepositoryInterface

app/domain/exceptions/
├── validation.py              # Validation errors
└── not_found.py               # NotFound errors
```

**Tareas:**

1. ✅ Crear `ProductoEntity` con campos BC3 Suite
2. ✅ Crear repository interfaces con métodos CRUD + búsqueda
3. ✅ Crear excepciones de dominio
4. ✅ Validar que domain layer NO depende de infrastructure

**Ejemplo código:**

```python
# app/domain/entities/producto.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ProductoEntity(BaseModel):
    """Domain entity for Producto"""
    codigo: str = Field(..., min_length=1)
    descripcion: str = Field(..., min_length=1)
    marca: str = Field(..., min_length=1)
    familia: Optional[str] = None
    pvp: Optional[float] = None
    
    # BC3 Suite fields
    bc3_descripcion_corta: Optional[str] = None
    bc3_product_type: Optional[str] = None
    bc3_descripcion_completa: Optional[str] = None
    
    # Audit fields
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        frozen = True  # Immutable entity

# app/domain/repositories/producto.py
from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.producto import ProductoEntity

class ProductoRepositoryInterface(ABC):
    """Interface for Producto repository"""
    
    @abstractmethod
    def get_by_codigo(self, codigo: str) -> Optional[ProductoEntity]:
        """Get product by code"""
        pass
    
    @abstractmethod
    def buscar_productos(
        self, 
        termino: str, 
        limit: int = 10,
        marca: str = "",
        familia: str = ""
    ) -> List[ProductoEntity]:
        """Search products with filters"""
        pass
    
    @abstractmethod
    def save(self, producto: ProductoEntity) -> ProductoEntity:
        """Save product"""
        pass
    
    @abstractmethod
    def delete(self, codigo: str) -> bool:
        """Delete product"""
        pass

# app/domain/exceptions/validation.py
class ValidationException(Exception):
    """Domain validation error"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"Validation error on {field}: {message}")

class ProductoYaExisteException(ValidationException):
    """Product already exists"""
    pass
```

### **Fase 3.2: Infrastructure Layer** (Week 1-2)

**Objetivo:** Migrar SQLAlchemy models y repository implementations

**Archivos nuevos:**

```
app/infrastructure/models/
├── producto.py                # ProductoModel (SQLAlchemy)
├── familia.py                 # FamiliaModel
└── bc3_suite.py               # BC3SuiteMappingModel

app/infrastructure/repositories/
├── producto.py                # SQLAlchemyProductoRepository
├── familia.py                 # SQLAlchemyFamiliaRepository
└── bc3_suite.py               # BC3SuiteRepository

app/infrastructure/database/
├── connection.py              # Session management
└── migrations/                # Alembic migrations
```

**Tareas:**

1. ✅ Migrar `app/models.py` → `app/infrastructure/models/`
2. ✅ Crear repository implementations con SQLAlchemy
3. ✅ Mapear Entity ↔ Model bidirectional
4. ✅ Mantener tests funcionales durante migración

**Ejemplo código:**

```python
# app/infrastructure/models/producto.py
from sqlalchemy import Column, String, Float, DateTime
from app.infrastructure.database.connection import Base

class ProductoModel(Base):
    """SQLAlchemy model for Producto"""
    __tablename__ = "productos"
    
    codigo = Column(String, primary_key=True)
    descripcion = Column(String, nullable=False)
    marca = Column(String, nullable=False)
    familia = Column(String, nullable=True)
    pvp = Column(Float, nullable=True)
    
    # BC3 Suite fields
    bc3_descripcion_corta = Column(String, nullable=True)
    bc3_product_type = Column(String, nullable=True)
    bc3_descripcion_completa = Column(String, nullable=True)
    
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    
    def to_entity(self) -> ProductoEntity:
        """Convert to domain entity"""
        return ProductoEntity(
            codigo=self.codigo,
            descripcion=self.descripcion,
            marca=self.marca,
            familia=self.familia,
            pvp=self.pvp,
            bc3_descripcion_corta=self.bc3_descripcion_corta,
            bc3_product_type=self.bc3_product_type,
            bc3_descripcion_completa=self.bc3_descripcion_completa,
            created_at=self.created_at,
            updated_at=self.updated_at
        )
    
    @classmethod
    def from_entity(cls, entity: ProductoEntity) -> "ProductoModel":
        """Create from domain entity"""
        return cls(
            codigo=entity.codigo,
            descripcion=entity.descripcion,
            marca=entity.marca,
            familia=entity.familia,
            pvp=entity.pvp,
            bc3_descripcion_corta=entity.bc3_descripcion_corta,
            bc3_product_type=entity.bc3_product_type,
            bc3_descripcion_completa=entity.bc3_descripcion_completa,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

# app/infrastructure/repositories/producto.py
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.domain.repositories.producto import ProductoRepositoryInterface
from app.domain.entities.producto import ProductoEntity
from app.infrastructure.models.producto import ProductoModel
from app.domain.exceptions.not_found import ProductoNotFoundException

class SQLAlchemyProductoRepository(ProductoRepositoryInterface):
    """SQLAlchemy implementation of Producto repository"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_codigo(self, codigo: str) -> Optional[ProductoEntity]:
        """Get product by code"""
        model = self.session.query(ProductoModel).filter(
            ProductoModel.codigo == codigo
        ).first()
        
        if not model:
            raise ProductoNotFoundException(codigo)
        
        return model.to_entity()
    
    def buscar_productos(
        self, 
        termino: str, 
        limit: int = 10,
        marca: str = "",
        familia: str = ""
    ) -> List[ProductoEntity]:
        """Search products with filters"""
        query = self.session.query(ProductoModel)
        
        # Apply text search
        if termino:
            search_pattern = f"%{termino}%"
            query = query.filter(
                or_(
                    ProductoModel.descripcion.ilike(search_pattern),
                    ProductoModel.codigo.ilike(search_pattern),
                    ProductoModel.bc3_descripcion_corta.ilike(search_pattern),
                    ProductoModel.bc3_descripcion_completa.ilike(search_pattern)
                )
            )
        
        # Apply filters
        if marca:
            query = query.filter(ProductoModel.marca == marca)
        
        if familia:
            query = query.filter(ProductoModel.familia == familia)
        
        # Apply limit
        query = query.limit(limit)
        
        # Return entities
        return [model.to_entity() for model in query.all()]
    
    def save(self, producto: ProductoEntity) -> ProductoEntity:
        """Save product (create or update)"""
        model = ProductoModel.from_entity(producto)
        
        self.session.merge(model)
        self.session.flush()  # Flush without commit
        
        return model.to_entity()
    
    def delete(self, codigo: str) -> bool:
        """Delete product"""
        model = self.session.query(ProductoModel).filter(
            ProductoModel.codigo == codigo
        ).first()
        
        if not model:
            return False
        
        self.session.delete(model)
        self.session.flush()
        
        return True
```

### **Fase 3.3: Application Layer** (Week 2)

**Objetivo:** Crear services con lógica de negocio

**Archivos nuevos:**

```
app/domain/services/
├── producto.py                # ProductoService
├── familia.py                 # FamiliaService
└── bc3_suite.py               # BC3SuiteService

app/application/dto/
├── producto.py                # ProductoCreateDTO, ProductoUpdateDTO
├── familia.py                 # FamiliaDTO
└── bc3_suite.py               # BC3SuiteDTO

app/application/commands/
├── crear_producto.py          # CrearProductoCommand
├── actualizar_producto.py     # ActualizarProductoCommand
└── generar_bc3.py             # GenerarBC3Command

app/application/queries/
├── buscar_productos.py        # BuscarProductosQuery
├── obtener_producto.py        # ObtenerProductoQuery
└── buscar_por_filtros.py      # BuscarPorFiltrosQuery
```

**Tareas:**

1. ✅ Crear `ProductoService` con reglas de negocio
2. ✅ Crear DTOs para input/output validation
3. ✅ Implementar command/query handlers
4. ✅ Mover lógica de routers a services

**Ejemplo código:**

```python
# app/domain/services/producto.py
from typing import List, Optional
from app.domain.repositories.producto import ProductoRepositoryInterface
from app.domain.entities.producto import ProductoEntity
from app.domain.exceptions.validation import (
    ValidationException, 
    ProductoYaExisteException
)
from app.application.dto.producto import (
    ProductoCreateDTO, 
    ProductoUpdateDTO
)

class ProductoService:
    """Business logic service for Producto"""
    
    def __init__(self, repository: ProductoRepositoryInterface):
        self.repository = repository
    
    def crear_producto(self, dto: ProductoCreateDTO) -> ProductoEntity:
        """Create new product with business rules"""
        # 1. Validations
        if len(dto.descripcion) < 2:
            raise ValidationException(
                "descripcion", 
                "Mínimo 2 caracteres"
            )
        
        if dto.pvp and dto.pvp < 0:
            raise ValidationException(
                "pvp", 
                "No puede ser negativo"
            )
        
        # 2. Check uniqueness
        try:
            self.repository.get_by_codigo(dto.codigo)
            raise ProductoYaExisteException(
                dto.codigo,
                "Ya existe un producto con este código"
            )
        except ProductoNotFoundException:
            pass  # OK, product doesn't exist
        
        # 3. Create entity
        producto = ProductoEntity(
            codigo=dto.codigo,
            descripcion=dto.descripcion,
            marca=dto.marca,
            familia=dto.familia,
            pvp=dto.pvp,
            bc3_descripcion_corta=dto.bc3_descripcion_corta,
            bc3_product_type=dto.bc3_product_type,
            bc3_descripcion_completa=dto.bc3_descripcion_completa
        )
        
        # 4. Persist through repository
        return self.repository.save(producto)
    
    def actualizar_producto(
        self, 
        codigo: str, 
        dto: ProductoUpdateDTO
    ) -> ProductoEntity:
        """Update product"""
        # 1. Get existing
        producto = self.repository.get_by_codigo(codigo)
        
        # 2. Apply updates
        update_data = dto.dict(exclude_unset=True)
        updated_producto = producto.copy(update=update_data)
        
        # 3. Validations
        if updated_producto.pvp and updated_producto.pvp < 0:
            raise ValidationException(
                "pvp", 
                "No puede ser negativo"
            )
        
        # 4. Persist
        return self.repository.save(updated_producto)
    
    def buscar_productos(
        self, 
        termino: str, 
        limit: int = 10,
        marca: str = "",
        familia: str = ""
    ) -> List[ProductoEntity]:
        """Search products (delegates to repository)"""
        return self.repository.buscar_productos(
            termino=termino,
            limit=limit,
            marca=marca,
            familia=familia
        )
    
    def eliminar_producto(self, codigo: str) -> bool:
        """Delete product"""
        # 1. Verify exists
        self.repository.get_by_codigo(codigo)
        
        # 2. Delete
        return self.repository.delete(codigo)

# app/application/dto/producto.py
from pydantic import BaseModel, Field
from typing import Optional

class ProductoCreateDTO(BaseModel):
    """DTO for creating a product"""
    codigo: str = Field(..., min_length=1)
    descripcion: str = Field(..., min_length=2)
    marca: str = Field(..., min_length=1)
    familia: Optional[str] = None
    pvp: Optional[float] = None
    bc3_descripcion_corta: Optional[str] = None
    bc3_product_type: Optional[str] = None
    bc3_descripcion_completa: Optional[str] = None

class ProductoUpdateDTO(BaseModel):
    """DTO for updating a product"""
    descripcion: Optional[str] = Field(None, min_length=2)
    marca: Optional[str] = Field(None, min_length=1)
    familia: Optional[str] = None
    pvp: Optional[float] = None
    bc3_descripcion_corta: Optional[str] = None
    bc3_product_type: Optional[str] = None
    bc3_descripcion_completa: Optional[str] = None

class ProductoResponseDTO(BaseModel):
    """DTO for product response"""
    codigo: str
    descripcion: str
    marca: str
    familia: Optional[str]
    pvp: Optional[float]
    bc3_descripcion_corta: Optional[str]
    bc3_product_type: Optional[str]
    bc3_descripcion_completa: Optional[str]
```

### **Fase 3.4: Dependency Injection** (Week 2-3)

**Objetivo:** Configurar DI y migrar routers

**Archivos nuevos/actualizados:**

```
app/main.py                    # DI Container setup
app/containers/                # DI container (optional)
└── di_container.py            # Container configuration

app/interfaces/http/
├── productos.py               # Routers con DI
├── familias.py                # Routers con DI
└── bc3.py                     # BC3 endpoints con DI
```

**Tareas:**

1. ✅ Crear DI container (FastAPI dependencies)
2. ✅ Migrar routers a inyectar services
3. ✅ Eliminar lógica de negocio de routers
4. ✅ Configurar mock repositories para tests

**Ejemplo código:**

```python
# app/main.py (updated with DI)
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.infrastructure.database.connection import get_db
from app.infrastructure.repositories.producto import SQLAlchemyProductoRepository
from app.domain.services.producto import ProductoService
from app.interfaces.http.productos import router as productos_router

# FastAPI App
app = FastAPI(title="API DISANO V2", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DI: Repository
def get_producto_repository(
    db: Session = Depends(get_db)
) -> ProductoRepositoryInterface:
    """Get producto repository"""
    return SQLAlchemyProductoRepository(db)

# DI: Service
def get_producto_service(
    repository: ProductoRepositoryInterface = Depends(get_producto_repository)
) -> ProductoService:
    """Get producto service"""
    return ProductoService(repository)

# Include routers
app.include_router(productos_router, prefix="/api/productos", tags=["productos"])

@app.get("/health")
def health():
    """Health check"""
    return {"status": "ok", "service": "api-disano"}

# app/interfaces/http/productos.py (updated)
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from app.domain.services.producto import ProductoService
from app.application.dto.producto import ProductoResponseDTO

router = APIRouter()

@router.get("/v2/list", response_model=List[ProductoResponseDTO])
def buscar_productos(
    buscar: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=100),
    marca: str = Query("", max_length=50),
    familia: str = Query("", max_length=50),
    service: ProductoService = Depends(get_producto_service)
):
    """Search products with filters (V2)"""
    try:
        productos = service.buscar_productos(
            termino=buscar,
            limit=limit,
            marca=marca,
            familia=familia
        )
        return [ProductoResponseDTO(**p.dict()) for p in productos]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/v2/{codigo}", response_model=ProductoResponseDTO)
def obtener_producto(
    codigo: str,
    service: ProductoService = Depends(get_producto_service)
):
    """Get product by code (V2)"""
    try:
        producto = service.repository.get_by_codigo(codigo)
        return ProductoResponseDTO(**producto.dict())
    except Exception as e:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
```

### **Fase 3.5: Testing Migration** (Week 3)

**Objetivo:** Adaptar tests a arquitectura hexagonal

**Archivos nuevos:**

```
tests/unit/domain/
├── test_producto_entity.py
├── test_producto_service.py
└── test_producto_repository_interface.py

tests/unit/infrastructure/
├── test_producto_repository.py
└── test_producto_model.py

tests/unit/application/
├── test_producto_commands.py
└── test_producto_queries.py

tests/integration/
├── test_producto_full_flow.py
└── test_bc3_suite_integration.py
```

**Tareas:**

1. ✅ Crear tests unitarios para domain layer
2. ✅ Crear tests de integración para infrastructure
3. ✅ Migrar tests existentes a nuevos patterns
4. ✅ Mock repositories en unit tests

**Ejemplo código:**

```python
# tests/unit/domain/test_producto_service.py
import pytest
from unittest.mock import Mock
from app.domain.services.producto import ProductoService
from app.domain.entities.producto import ProductoEntity
from app.application.dto.producto import ProductoCreateDTO
from app.domain.exceptions.not_found import ProductoNotFoundException

def test_crear_producto_success():
    """Test creating product successfully"""
    # Arrange
    mock_repo = Mock(spec=ProductoRepositoryInterface)
    mock_repo.get_by_codigo.side_effect = ProductoNotFoundException("TEST001")
    mock_repo.save.return_value = ProductoEntity(
        codigo="TEST001",
        descripcion="Test Product",
        marca="Test",
        pvp=99.99
    )
    
    service = ProductoService(mock_repo)
    dto = ProductoCreateDTO(
        codigo="TEST001",
        descripcion="Test Product",
        marca="Test",
        pvp=99.99
    )
    
    # Act
    result = service.crear_producto(dto)
    
    # Assert
    assert result.codigo == "TEST001"
    assert result.descripcion == "Test Product"
    mock_repo.save.assert_called_once()

def test_crear_producto_duplicate_code():
    """Test creating product with duplicate code raises error"""
    # Arrange
    mock_repo = Mock(spec=ProductoRepositoryInterface)
    mock_repo.get_by_codigo.return_value = ProductoEntity(
        codigo="TEST001",
        descripcion="Existing",
        marca="Test"
    )
    
    service = ProductoService(mock_repo)
    dto = ProductoCreateDTO(
        codigo="TEST001",
        descripcion="Test Product",
        marca="Test"
    )
    
    # Act & Assert
    with pytest.raises(ProductoYaExisteException):
        service.crear_producto(dto)
```

### **Fase 3.6: Documentation & Cleanup** (Week 3-4)

**Objetivo:** Documentar y limpiar código legacy

**Archivos nuevos:**

```
docs/
├── ARCHITECTURE.md            # Arquitectura hexagonal
├── DOMAIN_LAYER.md            # Domain layer docs
├── INFRASTRUCTURE_LAYER.md    # Infrastructure layer docs
├── APPLICATION_LAYER.md       # Application layer docs
└── MIGRATION_GUIDE.md         # Guía de migración

# Legacy cleanup
DELETE: app/models.py (migrated to infrastructure/models/)
DELETE: app/routers/* (migrated to interfaces/http/)
DELETE: app/database.py (migrated to infrastructure/database/)
```

**Tareas:**

1. ✅ Documentar arquitectura hexagonal
2. ✅ Crear guías de patrones
3. ✅ Eliminar código legacy
4. ✅ Actualizar documentación API

## 📋 CHECKLIST MIGRACIÓN

### **Week 1: Domain + Infrastructure**

- [ ] Crear `app/domain/entities/` con entidades
- [ ] Crear `app/domain/repositories/` con interfaces
- [ ] Crear `app/domain/exceptions/` con excepciones
- [ ] Migrar `app/models.py` → `app/infrastructure/models/`
- [ ] Crear `app/infrastructure/repositories/` implementations
- [ ] Crear `app/infrastructure/database/` connection
- [ ] Tests unitarios domain layer
- [ ] Tests infrastructure layer

### **Week 2: Application + DI**

- [ ] Crear `app/domain/services/` con lógica negocio
- [ ] Crear `app/application/dto/` con DTOs
- [ ] Crear `app/application/commands/` handlers
- [ ] Crear `app/application/queries/` handlers
- [ ] Configurar DI en `app/main.py`
- [ ] Migrar routers a `app/interfaces/http/`
- [ ] Tests application layer
- [ ] Tests DI container

### **Week 3: Testing + Documentation**

- [ ] Adaptar tests existentes a arquitectura hexagonal
- [ ] Crear tests de integración full flow
- [ ] Documentar arquitectura hexagonal
- [ ] Crear guías de patrones
- [ ] Documentar migration guide
- [ ] Validar coverage ≥80%

### **Week 4: Cleanup + Polish**

- [ ] Eliminar código legacy (models.py, old routers)
- [ ] Validar BC3 Suite integration
- [ ] Performance tuning
- [ ] Security review
- [ ] Documentation final
- [ ] Deployment preparation

## 🚀 PRÓXIMOS PASOS INMEDIATOS

### **1. Iniciar Fase 3.1 (Domain Layer):**

```bash
cd /Users/eloymartinezcuesta/Documents/API-DISANO-main

# Crear estructura de directorios
mkdir -p app/domain/entities
mkdir -p app/domain/repositories
mkdir -p app/domain/exceptions
mkdir -p app/domain/services
mkdir -p app/application/dto
mkdir -p app/application/commands
mkdir -p app/application/queries
mkdir -p app/infrastructure/models
mkdir -p app/infrastructure/repositories
mkdir -p app/infrastructure/database
mkdir -p app/interfaces/http
mkdir -p tests/unit/domain
mkdir -p tests/unit/infrastructure
mkdir -p tests/unit/application
```

### **2. Crear Domain Layer:**

```bash
# ProductoEntity
touch app/domain/entities/producto.py

# ProductoRepositoryInterface
touch app/domain/repositories/producto.py

# Domain exceptions
touch app/domain/exceptions/validation.py
touch app/domain/exceptions/not_found.py
```

### **3. Validar con Tests:**

```bash
# Correr tests existentes
python -m pytest tests/ -v

# Verificar que no rompemos funcionalidad
python -m pytest tests/unit/test_productos_router_execution.py -v
```

## 📚 REFERENCIAS

- **BC3-Suite Architecture:** `/Users/eloymartinezcuesta/Documents/BC3-Suite/docs/ARCHITECTURE.md`
- **BC3-Suite Patterns:** `/Users/eloymartinezcuesta/Documents/BC3-Suite/docs/PATTERNS.md`
- **Clean Architecture:** Robert C. Martin
- **Hexagonal Architecture:** Alistair Cockburn
- **Dependency Injection:** FastAPI docs

## ⚠️ RIESGOS Y MITIGACIÓN

| Riesgo | Impacto | Probabilidad | Mitigación |
|--------|---------|--------------|------------|
| **Rompimiento funcional** | 🟡 Medio | 🟡 Medio | Tests exhaustivos en cada fase |
| **Performance regresión** | 🟡 Medio | 🟢 Bajo | Benchmarking durante migración |
| **Tests fallidos** | 🔴 Alto | 🟡 Medio | Mock repositories, tests unitarios |
| **Dependency injection complejo** | 🟡 Medio | 🟢 Bajo | FastAPI dependencies simples |
| **Documentación obsoleta** | 🟢 Bajo | 🟡 Medio | Actualizar en cada fase |

---

**Estado:** ✅ **LISTO PARA INICIAR FASE 3.1**  
**Próxima acción:** Crear domain layer (entities + repositories)  
**Estimación:** 4 semanas total (1 por sub-fase)

**¿Quieres iniciar ahora con Fase 3.1: Domain Layer?**
