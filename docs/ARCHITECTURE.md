# Arquitectura de BC3-Suite

> **Versión**: 1.0
> **Última actualización**: 2026-04-07
> **Arquitecto**: Eloy Martínez Cuesta

## Tabla de Contenidos

1. [Visión General](#visión-general)
2. [Arquitectura Hexagonal](#arquitectura-hexagonal)
3. [Estructura de Directorios](#estructura-de-directorios)
4. [Patrones Clave](#patrones-clave)
5. [Flujo de Datos](#flujo-de-datos)
6. [Guías de Implementación](#guías-de-implementación)
7. [Gotchas Críticos](#gotchas-críticos)
8. [Ejemplos Prácticos](#ejemplos-prácticos)

---

## Visión General

BC3-Suite es un **CRM interno de DISANO ILUMINACIÓN** construido con **Flask** siguiendo el patrón de **Arquitectura Hexagonal (Clean Architecture)**. Esta arquitectura separa claramente la lógica de negocio de la infraestructura, permitiendo que el código sea testeable, mantenible y escalable.

### Principios Fundamentales

1. **Independencia del Framework**: La lógica de negocio no depende de Flask
2. **Testabilidad**: Todo se puede testear sin base de datos ni HTTP
3. **Separación de Responsabilidades**: Cada capa tiene un propósito claro
4. **Dependency Injection**: Las dependencias se inyectan, no se crean internamente

---

## Arquitectura Hexagonal

### Capas de la Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    BLUEPRINTS (HTTP)                        │
│  app/blueprints/ - Entradas HTTP, routes, controllers       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     SERVICES (Business Logic)               │
│  app/services/ - Lógica de negocio, orquestación            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   REPOSITORIES (Data Access)                │
│  app/repositories/ - Abstracción de acceso a datos          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              DATABASE MODELS (SQLAlchemy)                   │
│  app/database/models/ - ORM, persistencia en BD             │
└─────────────────────────────────────────────────────────────┘

          ↖️ (paralelo a todo) ↗️
┌─────────────────────────────────────────────────────────────┐
│              DOMAIN (Business Logic Core)                   │
│  app/domain/ - Modelos de dominio, excepciones, reglas      │
└─────────────────────────────────────────────────────────────┘
```

### Responsabilidades por Capa

#### 1. BLUEPRINTS (HTTP Layer)
- **Ubicación**: `app/blueprints/`
- **Estructura Modular**: Los blueprints complejos se organizan en sub-archivos dentro de una carpeta `routes/`.
- **Responsabilidad**: Manejar requests HTTP
- **NO debe tener**: Lógica de negocio
- **Qué hace**:
  - Recibir request
  - Validar input básico (Pydantic/Manual)
  - Llamar a services
  - Retornar response HTTP (JSON/HTML)

```python
# Ejemplo de ruta modular en app/blueprints/presupuesto/routes/budget_crud.py
@budget_crud_bp.route("/<int:id>", methods=["GET"])
def get_budget(id):
    # 1. Obtener datos y llamar a service
    service = PresupuestoService(repo)
    result = service.get_by_id(id)
    # 2. Response
    return jsonify({"status": "success", "data": result.to_dict()})
```

#### 2. SERVICES (Business Logic Layer)
- **Ubicación**: `app/services/`
- **Responsabilidad**: Lógica de negocio y orquestación
- **Qué hace**:
  - Validar reglas de negocio
  - Coordinar múltiples repositories
  - Manejar excepciones de dominio
  - ORQUESTAR, no implementar detalles de persistencia

```python
class ClienteService:
    def __init__(self, repository: ClienteRepositoryInterface):
        self.repository = repository

    def crear_cliente(self, nombre_empresa, **kwargs) -> Cliente:
        # 1. Validaciones de negocio
        if len(nombre_empresa) < 2:
            raise ValidationError("nombre_empresa", "Mínimo 2 caracteres")

        # 2. Verificar unicidad
        if self.repository.get_by_nombre(nombre_empresa):
            raise ClienteDuplicadoException("Ya existe este cliente")

        # 3. Crear entidad de dominio
        cliente = Cliente(nombre_empresa=nombre_empresa, **kwargs)

        # 4. Persistir (a través del repository)
        return self.repository.save(cliente)
```

#### 3. REPOSITORIES (Data Access Layer)
- **Ubicación**: `app/repositories/`
- **Responsabilidad**: Abstraer acceso a datos
- **Qué hace**:
  - Implementar CRUD
  - Mapear Domain Model ↔ SQLAlchemy Model
  - Manejar IntegrityError de BD
  - NO tener lógica de negocio

```python
class SQLAlchemyClienteRepository(ClienteRepositoryInterface):
    def save(self, cliente: Cliente) -> Cliente:
        # 1. Mapear Domain Model → SQLAlchemy Model
        model = ClienteModel.from_domain(cliente)

        # 2. Persistir en BD
        self.db_session.add(model)
        self.db_session.flush()  # NO commit aquí

        # 3. Actualizar domain model con ID generado
        cliente.id = model.id

        return cliente
```

#### 4. DATABASE MODELS (Persistence Layer)
- **Ubicación**: `app/database/models/`
- **Responsabilidad**: Representar tablas de BD
- **Qué hace**:
  - Definir schema de tabla
  - Relaciones SQLAlchemy
  - Conversión: `to_domain()` y `from_domain()`

```python
class Cliente(db.Model):
    __tablename__ = 'clientes'

    id = db.Column(db.Integer, primary_key=True)
    nombre_empresa = db.Column(db.String(200), nullable=False)

    def to_domain(self) -> Cliente:
        """SQLAlchemy → Domain Model"""
        from app.domain.clientes.models import Cliente as ClienteDomain
        return ClienteDomain(id=self.id, nombre_empresa=self.nombre_empresa)

    @classmethod
    def from_domain(cls, domain: Cliente):
        """Domain Model → SQLAlchemy"""
        return cls(id=domain.id, nombre_empresa=domain.nombre_empresa)
```

#### 5. DOMAIN (Business Core)
- **Ubicación**: `app/domain/`
- **Responsabilidad**: Definir entidades de negocio
- **Qué contiene**:
  - **Models**: Entidades de dominio (dataclasses)
  - **Exceptions**: Excepciones de negocio
  - **Value Objects**: Objetos de valor (si aplica)

```python
@dataclass
class Cliente:
    """Domain Model - Independiente de infraestructura"""
    id: Optional[int] = None
    nombre_empresa: str = ""
    email_general: Optional[str] = None

    def __post_init__(self):
        """Validaciones de dominio"""
        if not self.nombre_empresa or not self.nombre_empresa.strip():
            raise ValidationError("nombre_empresa", "Requerido")

    def to_dict(self) -> dict:
        """Serialización"""
        return {"id": self.id, "nombre_empresa": self.nombre_empresa}
```

---

## Estructura de Directorios

```
BC3_Suite/
├── app/
│   ├── blueprints/           # HTTP Layer - Routes modulares
│   │   ├── admin/
│   │   │   ├── routes/       # 15+ sub-blueprints (users, zones, audit)
│   │   │   └── templates/
│   │   ├── presupuesto/
│   │   │   ├── routes/       # 25+ sub-blueprints (crud, export, search)
│   │   │   └── templates/
│   │   ├── auth/             # Login, Register, Helpers
│   │   ├── clientes/         # CRUD de clientes
│   │   └── contactos/        # CRUD de contactos
│   │
│   ├── core/                 # Lógica específica del dominio (BC3, PDF, Excel)
│   │   ├── bc3/              # Generación de BC3
│   │   ├── pdf/              # Procesamiento de PDFs
│   │   └── excel/            # Importación de Excel
│   │
│   ├── database/             # Persistencia - SQLAlchemy Models
│   │   ├── models/           # Modelos ORM
│   │   │   ├── cliente.py    # Tabla clientes
│   │   │   ├── contacto.py   # Tabla contactos
│   │   │   └── presupuesto.py
│   │   └── base.py           # db = SQLAlchemy()
│   │
│   ├── domain/               # Domain Models - Lógica de negocio pura
│   │   ├── clientes/         # Dominio de clientes
│   │   │   ├── models.py     # Cliente, Contacto, Direccion (dataclasses)
│   │   │   └── exceptions.py # Excepciones de negocio
│   │   └── presupuesto/      # Dominio de presupuestos
│   │
│   ├── repositories/         # Data Access Layer - Abstracción de BD
│   │   ├── clientes/
│   │   │   ├── cliente_repository.py      # Interfaz + implementación
│   │   │   └── contacto_repository.py
│   │   └── presupuesto/
│   │
│   ├── services/             # Business Logic Layer - Orquestación
│   │   ├── cliente_service.py        # Lógica de negocio de clientes
│   │   ├── contacto_service.py       # Lógica de negocio de contactos
│   │   └── presupuesto_service.py
│   │
│   ├── utils/                # Utilidades
│   │   ├── auth.py           # Helpers de autenticación
│   │   ├── api_disano_client.py
│   │   └── helpers.py
│   │
│   ├── static/               # CSS, JS, imágenes
│   ├── templates/            # Templates Jinja2
│   └── tests/                # Tests (estructura espeja app/)
│
├── config.py                 # Configuración Flask
├── wsgi.py                   # Entry point WSGI
└── requirements.txt          # Dependencias
```

### Qué va en cada directorio

| Directorio | Qué contiene | Ejemplo |
|------------|--------------|---------|
| `blueprints/` | Routes HTTP | `clientes_bp.route("", methods=["POST"])` |
| `core/` | Lógica específica del dominio | `generar_bc3()`, `procesar_pdf()` |
| `database/models/` | Modelos SQLAlchemy | `class Cliente(db.Model)` |
| `domain/` | Modelos de dominio | `@dataclass class Cliente` |
| `repositories/` | Acceso a datos | `class SQLAlchemyClienteRepository` |
| `services/` | Lógica de negocio | `class ClienteService` |
| `utils/` | Helpers genéricos | `obtener_usuario_id()` |

---

## Organización Territorial y Visibilidad

El sistema implementa una **Jerarquía de Visibilidad** basada en el territorio (**Zonas**), permitiendo que el CRM escale a múltiples delegaciones comerciales.

### 🌍 Modelo de Zonas
- **Zona**: Entidad que agrupa usuarios por territorio (Ej: Madrid, Barcelona, Sur).
- **Roles en Zona**:
    - `coordinador`: Puede ver todos los presupuestos de su zona + los propios.
    - `miembro`: Solo ve sus propios presupuestos (sales standard).

### 🔐 Lógica de Visibilidad (Row-Level Security)
Esta lógica reside en el `SQLAlchemyPresupuestoRepository` y se aplica dinámicamente según el usuario que realiza la petición:
1. **Super Admin / Dirección**: Acceso total (sin filtros de zona).
2. **Coordinador**: Filtro `WHERE (usuario_id = actual OR usuario_id IN (miembros_zona))`.
3. **Sales**: Filtro `WHERE usuario_id = actual`.

---

## Patrones Clave

### 1. Repository Pattern

**Propósito**: Abstraer el acceso a datos de la lógica de negocio.

**Implementación**:

```python
# 1. Definir interfaz (contrato)
class ClienteRepositoryInterface(ABC):
    @abstractmethod
    def save(self, cliente: Cliente) -> Cliente:
        pass

    @abstractmethod
    def get_by_id(self, cliente_id: int) -> Optional[Cliente]:
        pass

# 2. Implementar con SQLAlchemy
class SQLAlchemyClienteRepository(ClienteRepositoryInterface):
    def __init__(self, db_session):
        self.db_session = db_session

    def save(self, cliente: Cliente) -> Cliente:
        model = ClienteModel.from_domain(cliente)
        self.db_session.add(model)
        self.db_session.flush()  # Genera ID sin hacer commit
        cliente.id = model.id
        return cliente

    def get_by_id(self, cliente_id: int) -> Optional[Cliente]:
        model = self.db_session.query(ClienteModel).filter_by(id=cliente_id).first()
        if not model:
            return None
        return self._model_to_domain(model)
```

**Beneficios**:
- Tests: Se puede mockear fácilmente
- Cambio de implementación: Se puede cambiar a MongoDB sin tocar services
- Separación: La lógica de negocio no sabe de SQLAlchemy

### 2. Service Layer

**Propósito**: Orquestar lógica de negocio y coordinar repositories.

**Implementación**:

```python
class ClienteService:
    def __init__(self, repository: ClienteRepositoryInterface):
        self.repository = repository

    def crear_cliente(self, nombre_empresa: str, **kwargs) -> Cliente:
        # 1. Validaciones de negocio
        if len(nombre_empresa) < 2:
            raise ValidationError("nombre_empresa", "Mínimo 2 caracteres")

        # 2. Reglas de negocio
        existing = self.repository.get_by_nombre(nombre_empresa)
        if existing:
            raise ClienteDuplicadoException("Ya existe este cliente")

        # 3. Crear entidad
        cliente = Cliente(nombre_empresa=nombre_empresa, **kwargs)

        # 4. Persistir
        return self.repository.save(cliente)
```

**Beneficios**:
- Lógica reutilizable (se puede llamar desde HTTP, CLI, tests)
- Testeable sin HTTP
- Fácil de extender

### 3. Domain Models (Dataclasses)

**Propósito**: Representar entidades de negocio sin dependencias de infraestructura.

**Implementación**:

```python
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Cliente:
    """Domain Model - Independiente de BD, Flask, etc."""
    id: Optional[int] = None
    nombre_empresa: str = ""
    email_general: Optional[str] = None
    activo: bool = True
    fecha_creacion: Optional[datetime] = None

    def __post_init__(self):
        """Validaciones de dominio"""
        if not self.nombre_empresa or not self.nombre_empresa.strip():
            raise ValidationError("nombre_empresa", "Requerido")

    def to_dict(self) -> dict:
        """Serialización para responses JSON"""
        return {
            "id": self.id,
            "nombre_empresa": self.nombre_empresa,
            "email_general": self.email_general,
        }
```

**Beneficios**:
- Inmutabilidad (opcional con `frozen=True`)
- Validaciones en `__post_init__`
- Serialización con `to_dict()`
- NO dependen de SQLAlchemy ni Flask

### 4. Dependency Injection

**Propósito**: Inyectar dependencias en lugar de crearlas internamente.

**Implementación**:

```python
# ❌ MAL - Service crea su propia dependencia
class ClienteService:
    def __init__(self):
        self.repository = SQLAlchemyClienteRepository(db.session)  # Acoplado

# ✅ BIEN - Service recibe dependencia
class ClienteService:
    def __init__(self, repository: ClienteRepositoryInterface):
        self.repository = repository  # Desacoplado

# Uso en blueprint
repo = SQLAlchemyClienteRepository(db.session)
service = ClienteService(repo)
cliente = service.crear_cliente(nombre_empresa="ACME")
```

**Beneficios**:
- Testeable: Se puede inyectar un mock
- Flexible: Se puede cambiar la implementación
- Explícito: Las dependencias son visibles

---

## Flujo de Datos

### Request → Response (Crear Cliente)

```
1. HTTP Request
   POST /api/clientes
   Body: {"nombre_empresa": "ACME", "email": "info@acme.com"}

   ↓

2. Blueprint (app/blueprints/clientes/routes.py)
   - Recibe request
   - Valida input básico
   - Crea service con repository
   - Llama: service.crear_cliente(**data)

   ↓

3. Service (app/services/cliente_service.py)
   - Valida reglas de negocio (nombre único, longitud)
   - Crea Domain Model: Cliente(nombre_empresa="ACME")
   - Llama: repository.save(cliente)

   ↓

4. Repository (app/repositories/clientes/cliente_repository.py)
   - Convierte Domain Model → SQLAlchemy Model
   - db.session.add(model)
   - db.session.flush()  # Genera ID
   - Actualiza domain model con ID
   - Retorna domain model

   ↓

5. Blueprint (de nuevo)
   - db.session.commit()  # CONFIRMA transacción
   - Retorna response HTTP 201
   - Body: {"status": "success", "data": cliente.to_dict()}

   ↓

6. HTTP Response
   201 Created
   Body: {"status": "success", "data": {"id": 1, "nombre_empresa": "ACME"}}
```

### Manejo de Errores

```
ValidationError (dominio)
   ↓
Service levanta ValidationError
   ↓
Blueprint catch → 400 Bad Request

ClienteDuplicadoException (repositorio)
   ↓
Repository catch IntegrityError → levanta ClienteDuplicadoException
   ↓
Service no catch, propaga
   ↓
Blueprint catch → 409 Conflict

Exception genérica
   ↓
Blueprint catch → db.session.rollback()
   ↓
Retorna 500 Internal Server Error
```

---

## Guías de Implementación

### Cómo Agregar una Nueva Feature

#### Escenario: Agregar módulo de "Productos"

##### Paso 1: Crear Domain Model

```python
# app/domain/productos/models.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class Producto:
    """Domain Model de Producto"""
    id: Optional[int] = None
    codigo: str = ""
    nombre: str = ""
    pvp: float = 0.0
    activo: bool = True

    def __post_init__(self):
        if not self.codigo:
            raise ValidationError("codigo", "Requerido")
        if self.pvp < 0:
            raise ValidationError("pvp", "Debe ser >= 0")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "codigo": self.codigo,
            "nombre": self.nombre,
            "pvp": self.pvp,
        }
```

```python
# app/domain/productos/exceptions.py
class ProductoNotFound(Exception):
    pass

class ProductoDuplicadoException(Exception):
    pass
```

##### Paso 2: Crear SQLAlchemy Model

```python
# app/database/models/producto.py
from app.database.base import db

class Producto(db.Model):
    __tablename__ = 'productos'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    pvp = db.Column(db.Float, nullable=False)
    activo = db.Column(db.Boolean, default=True)

    def to_domain(self):
        from app.domain.productos.models import Producto as ProductoDomain
        return ProductoDomain(
            id=self.id,
            codigo=self.codigo,
            nombre=self.nombre,
            pvp=self.pvp,
            activo=self.activo,
        )

    @classmethod
    def from_domain(cls, domain):
        return cls(
            id=domain.id,
            codigo=domain.codigo,
            nombre=domain.nombre,
            pvp=domain.pvp,
            activo=domain.activo,
        )
```

##### Paso 3: Crear Repository

```python
# app/repositories/productos/producto_repository.py
from abc import ABC, abstractmethod
from typing import Optional

class ProductoRepositoryInterface(ABC):
    @abstractmethod
    def save(self, producto: Producto) -> Producto:
        pass

    @abstractmethod
    def get_by_id(self, producto_id: int) -> Optional[Producto]:
        pass

    @abstractmethod
    def get_by_codigo(self, codigo: str) -> Optional[Producto]:
        pass

class SQLAlchemyProductoRepository(ProductoRepositoryInterface):
    def __init__(self, db_session):
        self.db_session = db_session

    def save(self, producto: Producto) -> Producto:
        from app.database.models.producto import Producto as ProductoModel
        from sqlalchemy.exc import IntegrityError

        is_new = producto.id is None

        if is_new:
            model = ProductoModel.from_domain(producto)
            self.db_session.add(model)
            self.db_session.flush()
            producto.id = model.id
        else:
            model = self.db_session.query(ProductoModel).filter_by(id=producto.id).first()
            if not model:
                raise ProductoNotFound(f"Producto {producto.id} no encontrado")
            model.codigo = producto.codigo
            model.nombre = producto.nombre
            model.pvp = producto.pvp
            self.db_session.flush()

        return producto

    def get_by_id(self, producto_id: int) -> Optional[Producto]:
        from app.database.models.producto import Producto as ProductoModel

        model = self.db_session.query(ProductoModel).filter_by(id=producto_id).first()
        if not model:
            return None
        return model.to_domain()

    def get_by_codigo(self, codigo: str) -> Optional[Producto]:
        from app.database.models.producto import Producto as ProductoModel

        model = self.db_session.query(ProductoModel).filter_by(codigo=codigo).first()
        if not model:
            return None
        return model.to_domain()
```

##### Paso 4: Crear Service

```python
# app/services/producto_service.py
import logging
from app.domain.productos.models import Producto
from app.domain.productos.exceptions import ProductoNotFound, ProductoDuplicadoException, ValidationError
from app.repositories.productos.producto_repository import ProductoRepositoryInterface

logger = logging.getLogger(__name__)

class ProductoService:
    def __init__(self, repository: ProductoRepositoryInterface):
        self.repository = repository

    def crear_producto(self, codigo: str, nombre: str, pvp: float) -> Producto:
        # Validaciones
        if not codigo or not codigo.strip():
            raise ValidationError("codigo", "Requerido")

        if pvp < 0:
            raise ValidationError("pvp", "Debe ser >= 0")

        # Verificar unicidad
        existing = self.repository.get_by_codigo(codigo)
        if existing:
            raise ProductoDuplicadoException(f"Ya existe producto con código {codigo}")

        # Crear entidad
        producto = Producto(codigo=codigo, nombre=nombre, pvp=pvp)

        # Persistir
        return self.repository.save(producto)

    def obtener_producto(self, producto_id: int) -> Producto:
        producto = self.repository.get_by_id(producto_id)
        if not producto:
            raise ProductoNotFound(f"Producto {producto_id} no encontrado")
        return producto
```

##### Paso 5: Crear Blueprint

```python
# app/blueprints/productos/routes.py
from flask import Blueprint, request, jsonify, current_app
from app import db
from app.services.producto_service import ProductoService
from app.repositories.productos.producto_repository import SQLAlchemyProductoRepository
from app.domain.productos.exceptions import ProductoNotFound, ProductoDuplicadoException

productos_bp = Blueprint("productos_bp", __name__, url_prefix="/api/productos")

@productos_bp.route("", methods=["POST"])
def crear_producto():
    try:
        data = request.json

        # Validar input
        if not data.get("codigo"):
            return jsonify({"status": "error", "message": "codigo requerido"}), 400

        # Crear service
        repo = SQLAlchemyProductoRepository(db.session)
        service = ProductoService(repo)

        # Crear producto
        producto = service.crear_producto(
            codigo=data["codigo"],
            nombre=data.get("nombre", ""),
            pvp=data.get("pvp", 0.0),
        )

        # Commit
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Producto creado",
            "data": producto.to_dict()
        }), 201

    except ProductoDuplicadoException as e:
        return jsonify({"status": "error", "message": str(e)}), 409
    except ValidationError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creando producto: {e}")
        return jsonify({"status": "error", "message": "Error interno"}), 500

@productos_bp.route("/<int:producto_id>", methods=["GET"])
def obtener_producto(producto_id):
    try:
        repo = SQLAlchemyProductoRepository(db.session)
        service = ProductoService(repo)

        producto = service.obtener_producto(producto_id)

        return jsonify({
            "status": "success",
            "data": producto.to_dict()
        }), 200

    except ProductoNotFound as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Error obteniendo producto: {e}")
        return jsonify({"status": "error", "message": "Error interno"}), 500
```

##### Paso 6: Registrar Blueprint

```python
# app/__init__.py o app/blueprints/__init__.py
from app.blueprints.productos.routes import productos_bp

app.register_blueprint(productos_bp)
```

---

## Gotchas Críticos

### 1. `db.session.commit()` es OBLIGATORIO

**Problema**: Los cambios no se persisten si no hay commit.

**Dónde**: En los blueprints, después de llamar al service.

```python
# ❌ MAL - Sin commit
repo = SQLAlchemyClienteRepository(db.session)
service = ClienteService(repo)
cliente = service.crear_cliente(nombre_empresa="ACME")
return jsonify({"data": cliente.to_dict()}), 201  # NO se guardó

# ✅ BIEN - Con commit
repo = SQLAlchemyClienteRepository(db.session)
service = ClienteService(repo)
cliente = service.crear_cliente(nombre_empresa="ACME")
db.session.commit()  # OBLIGATORIO
return jsonify({"data": cliente.to_dict()}), 201
```

**Por qué**:
- Repositories solo hacen `flush()` (genera ID, pero no confirma transacción)
- El commit lo hace el blueprint para controlar cuándo se persiste
- Permite rollback si hay error

### 2. Services Necesitan TODOS los Repositories

**Problema**: Si un service necesita 2 repositories, debe recibir ambos.

**Ejemplo**: `ContactoService` necesita `ContactoRepository` y `ClienteRepository`.

```python
# ❌ MAL - Service crea su propia dependencia
class ContactoService:
    def __init__(self, contacto_repo):
        self.contacto_repo = contacto_repo
        self.cliente_repo = SQLAlchemyClienteRepository(db.session)  # Acoplado

# ✅ BIEN - Service recibe todas las dependencias
class ContactoService:
    def __init__(
        self,
        contacto_repo: ContactoRepositoryInterface,
        cliente_repo: ClienteRepositoryInterface,  # Inyectado
    ):
        self.contacto_repo = contacto_repo
        self.cliente_repo = cliente_repo

    def crear_contacto(self, cliente_id: int, **kwargs):
        # Validar que cliente existe
        cliente = self.cliente_repo.get_by_id(cliente_id)
        if not cliente:
            raise ClienteNotFound(f"Cliente {cliente_id} no existe")

        # Crear contacto
        contacto = Contacto(cliente_id=cliente_id, **kwargs)
        return self.contacto_repo.save(contacto)
```

**Por qué**:
- Permite testear con mocks de ambos repositories
- Hace explícitas las dependencias
- Permite cambiar implementaciones sin tocar el service

### 3. `ValidationError` vs `Exception`

**Problema**: Diferenciar errores de validación vs errores técnicos.

**Regla**:
- **ValidationError**: Input inválido (400 Bad Request)
- **NotFound**: Recurso no existe (404 Not Found)
- **DuplicadoException**: Conflicto de unicidad (409 Conflict)
- **Exception genérica**: Error técnico (500 Internal Server Error)

```python
# En service
def crear_cliente(self, nombre_empresa: str) -> Cliente:
    if not nombre_empresa:
        raise ValidationError("nombre_empresa", "Requerido")  # 400

    if len(nombre_empresa) > 200:
        raise ValidationError("nombre_empresa", "Máximo 200 caracteres")  # 400

    existing = self.repository.get_by_nombre(nombre_empresa)
    if existing:
        raise ClienteDuplicadoException("Ya existe")  # 409

    cliente = self.repository.save(Cliente(nombre_empresa))
    return cliente

# En blueprint
try:
    cliente = service.crear_cliente(data["nombre_empresa"])
    db.session.commit()
    return jsonify({"data": cliente.to_dict()}), 201

except ValidationError as e:
    return jsonify({"status": "error", "message": str(e)}), 400

except ClienteDuplicadoException as e:
    return jsonify({"status": "error", "message": str(e)}), 409

except Exception as e:
    db.session.rollback()
    current_app.logger.error(f"Error: {e}")
    return jsonify({"status": "error", "message": "Error interno"}), 500
```

### 4. `flush()` vs `commit()` en Repositories

**Problema**: Los repositories NO deben hacer commit.

**Regla**:
- **flush()**: Genera IDs, valida constraints, pero NO confirma transacción
- **commit()**: Confirma transacción (solo en blueprints)

```python
# ❌ MAL - Repository hace commit
class SQLAlchemyClienteRepository:
    def save(self, cliente: Cliente):
        model = ClienteModel.from_domain(cliente)
        self.db_session.add(model)
        self.db_session.commit()  # NO hacer esto
        return cliente

# ✅ BIEN - Repository solo hace flush
class SQLAlchemyClienteRepository:
    def save(self, cliente: Cliente):
        model = ClienteModel.from_domain(cliente)
        self.db_session.add(model)
        self.db_session.flush()  # Genera ID sin confirmar
        cliente.id = model.id
        return cliente
```

**Por qué**:
- El blueprint controla la transacción
- Permite rollback si hay error
- Permite hacer múltiples operaciones en una sola transacción

### 5. Domain Models NO deben tener dependencias de infraestructura

**Problema**: Domain models acoplados a SQLAlchemy o Flask.

**Regla**: Domain models deben ser puros (solo Python standard lib).

```python
# ❌ MAL - Domain model con dependencia de SQLAlchemy
from dataclasses import dataclass
from sqlalchemy.orm import relationship  # Dependencia de infraestructura

@dataclass
class Cliente:
    id: Optional[int] = None
    nombre_empresa: str = ""
    contactos = relationship("Contacto")  # NO

# ✅ BIEN - Domain model puro
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Cliente:
    id: Optional[int] = None
    nombre_empresa: str = ""
    contactos: List[Contacto] = field(default_factory=list)  # Lista Python
```

### 6. `rollback()` en Blueprint al capturar Exception

**Problema**: Si hay error, la sesión queda sucia.

**Regla**: Siempre hacer rollback en el except genérico.

```python
try:
    cliente = service.crear_cliente(**data)
    db.session.commit()
    return jsonify({"data": cliente.to_dict()}), 201

except ValidationError as e:
    return jsonify({"error": str(e)}), 400

except Exception as e:
    db.session.rollback()  # OBLIGATORIO
    current_app.logger.error(f"Error: {e}")
    return jsonify({"error": "Error interno"}), 500
```

---

## Ejemplos Prácticos

### Ejemplo 1: ContactoService con 2 Repositories

**Escenario**: `ContactoService` necesita validar que el cliente existe antes de crear un contacto.

```python
# app/services/contacto_service.py
class ContactoService:
    def __init__(
        self,
        contacto_repo: ContactoRepositoryInterface,
        cliente_repo: ClienteRepositoryInterface,  # Necesario para validar
    ):
        self.contacto_repo = contacto_repo
        self.cliente_repo = cliente_repo

    def crear_contacto(
        self,
        cliente_id: int,
        nombre: str,
        email: str,
    ) -> Contacto:
        # 1. Validar que cliente existe
        cliente = self.cliente_repo.get_by_id(cliente_id)
        if not cliente:
            raise ClienteNotFound(f"Cliente {cliente_id} no existe")

        # 2. Validar input
        if not nombre:
            raise ValidationError("nombre", "Requerido")

        # 3. Crear contacto
        contacto = Contacto(
            cliente_id=cliente_id,
            nombre=nombre,
            email=email,
        )

        # 4. Persistir
        return self.contacto_repo.save(contacto)
```

**Uso en blueprint**:

```python
# app/blueprints/clientes/routes.py
@clientes_bp.route("/<int:cliente_id>/contactos", methods=["POST"])
def crear_contacto(cliente_id):
    try:
        data = request.json

        # Crear repositories
        contacto_repo = SQLAlchemyContactoRepository(db.session)
        cliente_repo = SQLAlchemyClienteRepository(db.session)

        # Crear service con ambas dependencias
        service = ContactoService(contacto_repo, cliente_repo)

        # Crear contacto
        contacto = service.crear_contacto(
            cliente_id=cliente_id,
            nombre=data["nombre"],
            email=data["email"],
        )

        # Commit
        db.session.commit()

        return jsonify({
            "status": "success",
            "data": contacto.to_dict()
        }), 201

    except ClienteNotFound as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error: {e}")
        return jsonify({"status": "error", "message": "Error interno"}), 500
```

### Ejemplo 2: Paginación con Visibility Filter

**Escenario**: Listar clientes con filtros de visibilidad por rol de usuario.

**Service**:

```python
# app/services/cliente_service.py
def listar_clientes(
    self,
    usuario_id: Optional[int] = None,
    es_admin: bool = False,
    page: Optional[int] = None,
    per_page: Optional[int] = None,
    search: Optional[str] = None,
) -> Tuple[List[Cliente], int]:
    """
    Listar clientes con filtros de visibilidad.

    Reglas de visibilidad:
    - Admin: ve todos los clientes
    - Sales: ve solo sus clientes + importados (created_by=NULL)
    """
    if page is not None and per_page is not None:
        # Con paginación
        clientes, total = self.repository.list_with_visibility(
            usuario_id=usuario_id,
            es_admin=es_admin,
            page=page,
            per_page=per_page,
            search=search,
        )
        return clientes, total
    else:
        # Sin paginación
        clientes = self.repository.get_all(activo=True)
        return clientes
```

**Repository**:

```python
# app/repositories/clientes/cliente_repository.py
def list_with_visibility(
    self,
    usuario_id: int,
    es_admin: bool,
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
    activo: bool = True
) -> Tuple[List[Cliente], int]:
    from sqlalchemy import or_

    # Base query
    query = self.db_session.query(ClienteModel).filter_by(activo=activo)

    # Filtro de visibilidad
    if es_admin:
        # Admin ve todo
        pass
    else:
        # Sales ve solo sus clientes + importados
        query = query.filter(
            or_(
                ClienteModel.created_by == usuario_id,
                ClienteModel.created_by == None,
            )
        )

    # Search
    if search:
        query = query.filter(
            func.lower(ClienteModel.nombre_empresa).contains(func.lower(search))
        )

    # Count
    total = query.count()

    # Paginate
    models = query.order_by(ClienteModel.nombre_empresa)\
        .offset((page - 1) * per_page)\
        .limit(per_page)\
        .all()

    clientes = [self._model_to_domain(m) for m in models]
    return clientes, total
```

**Blueprint**:

```python
# app/blueprints/clientes/routes.py
@clientes_bp.route("", methods=["GET"])
@login_required
def listar_clientes():
    try:
        # Obtener usuario
        usuario_id = obtener_usuario_id()

        # Determinar si es admin
        from flask_login import current_user
        es_admin = current_user.role in ['admin', 'super_admin']

        # Parse query params
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        search = request.args.get('search')

        # Crear service
        repo = SQLAlchemyClienteRepository(db.session)
        service = ClienteService(repo)

        # Listar
        clientes, total = service.listar_clientes(
            usuario_id=usuario_id,
            es_admin=es_admin,
            page=page,
            per_page=per_page,
            search=search,
        )

        total_pages = (total + per_page - 1) // per_page

        return jsonify({
            "status": "success",
            "data": {
                "items": [c.to_dict() for c in clientes],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "pages": total_pages,
                }
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error: {e}")
        return jsonify({"status": "error", "message": "Error interno"}), 500
```

---

## Resumen de Conceptos Clave

### Principio de Responsabilidad Única

Cada capa hace UNA cosa bien:

| Capa | Responsabilidad | NO hace |
|------|-----------------|---------|
| Blueprint | Manejar HTTP | Lógica de negocio |
| Service | Lógica de negocio | Acceso a datos |
| Repository | Acceso a datos | Lógica de negocio |
| Domain Model | Representar entidad | Saber de BD o HTTP |

### Flujo de Datos

```
HTTP Request → Blueprint → Service → Repository → Database
                ↓           ↓          ↓
             Response    Domain    SQLAlchemy
```

### Reglas de Oro

1. **Blueprints NO tienen lógica de negocio**
2. **Services NO acceden directamente a la BD**
3. **Repositories NO tienen lógica de negocio**
4. **Domain Models son puros (sin dependencias)**
5. **SIEMPRE hacer `db.session.commit()` en blueprints**
6. **SIEMPRE hacer `db.session.rollback()` en except genérico**

---

## Recursos Adicionales

### Documentación del Proyecto

- [GEMINI.md](../GEMINI.md) - Guía de buenas prácticas (Source of Truth)
- [BC3_SUITE_DEFINITION.md](BC3_SUITE_DEFINITION.md) - Definición del producto
- [TASK_BREAKDOWN_BUSINESS_PRIORITY.md](TASK_BREAKDOWN_BUSINESS_PRIORITY.md) - Plan de trabajo

### Patrones de Diseño

- Repository Pattern: Abstrae acceso a datos
- Service Layer: Orquesta lógica de negocio
- Dependency Injection: Inyecta dependencias
- Dataclass: Domain models inmutables

### Testing

```python
# Test de service con mock repository
def test_crear_cliente_con_exito(mock_repository):
    # Arrange
    mock_repository.get_by_nombre.return_value = None
    mock_repository.save.return_value = Cliente(id=1, nombre_empresa="ACME")

    service = ClienteService(mock_repository)

    # Act
    cliente = service.crear_cliente(nombre_empresa="ACME")

    # Assert
    assert cliente.nombre_empresa == "ACME"
    mock_repository.save.assert_called_once()
```

---

**Fin del documento**

Para preguntas o sugerencias, contactar a: Eloy Martínez Cuesta
