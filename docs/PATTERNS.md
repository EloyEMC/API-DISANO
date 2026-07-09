# 🔧 Patrones de Código - BC3-Suite

> **Nota**: Este documento describe patrones de código aplicables a todo el proyecto.

---

## 📋 Tabla de Contenidos

- [Arquitectura Hexagonal](#arquitectura-hexagonal)
- [Patrón Repository](#patrón-repository)
- [Patrón Service](#patrón-service)
- [Patrón Domain Model](#patrón-domain-model)
- [Patrón Blueprint](#patrón-blueprint)
- [Patrón de Respuesta JSON](#patrón-de-respuesta-json)
- [Patrón de Validación](#patrón-de-validación)
- [Patrón de Error Handling](#patrón-de-error-handling)
- [Patrón de Testing](#patrón-de-testing)
- [Patrón de Auth](#patrón-de-auth)

---

## 🏗️ Arquitectura Hexagonal

### Estructura de Capas

```
┌─────────────────────────────────────┐
│  HTTP Layer (Blueprints)            │  ← Routes, Controllers
│  app/blueprints/*/routes.py         │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│  Business Logic (Services)          │  ← Lógica de negocio
│  app/services/*_service.py          │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│  Data Access (Repositories)         │  ← Acceso a datos
│  app/repositories/*/*_repository.py │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│  Database (SQLAlchemy Models)       │  ← Persistencia
│  app/database/models/*.py           │
└─────────────────────────────────────┘
```

### Regla de Oro

**Cada capa tiene SU responsabilidad y NO debe invadir las otras**:

| Capa | Responsabilidad | NO debe |
|------|-----------------|---------|
| **Blueprint** | Recibir request, llamar service, retornar response | Tener lógica de negocio |
| **Service** | Lógica de negocio, validaciones de dominio | Acceder a DB directamente |
| **Repository** | Acceso a datos (CRUD) | Tener lógica de negocio |
| **Model** | Definición de tabla SQLAlchemy | Tener lógica de negocio |

---

## 📦 Patrón Repository

### Propósito

**Abstraer el acceso a datos**. El Service no sabe si es SQLite, PostgreSQL, MySQL, etc.

### Estructura

```python
# app/repositories/presupuestos/presupuesto_repository.py

from sqlalchemy.orm import Session
from app.database.models.presupuesto import PresupuestoModel
from app.domain.presupuesto.models import Presupuesto

class SQLAlchemyPresupuestoRepository:
    """Repository de Presupuesto."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, presupuesto: Presupuesto) -> Presupuesto:
        """Guarda o actualiza un presupuesto."""
        model = PresupuestoModel(
            id=presupuesto.id,
            obra_nombre=presupuesto.obra_nombre,
            # ... mapear campos
        )
        self.session.add(model)
        self.session.flush()
        presupuesto.id = model.id
        return presupuesto

    def get_by_id(self, presupuesto_id: int) -> Optional[Presupuesto]:
        """Obtiene presupuesto por ID."""
        model = self.session.query(PresupuestoModel).filter_by(
            id=presupuesto_id
        ).first()
        if not model:
            return None
        return model.to_domain()

    def list_by_usuario(self, usuario_id: str, filters: dict) -> List[Presupuesto]:
        """Lista presupuestos de un usuario con filtros."""
        query = self.session.query(PresupuestoModel).filter_by(
            usuario_id=usuario_id
        )

        if filters.get("estado"):
            query = query.filter_by(estado=filters["estado"])

        return [m.to_domain() for m in query.all()]
```

### Patrones de Repository

#### ✅ SIEMPRE

1. **Recibir Session por constructor** (no crearla dentro)
2. **Retornar entidades de dominio** (no modelos SQLAlchemy)
3. **Métodos CRUD**: `save()`, `get_by_id()`, `list()`, `delete()`
4. **Métodos de búsqueda**: `list_by_usuario()`, `search_by_nombre()`
5. **Usar `filter_by()` y `filter()`** para queries

#### ❌ NUNCA

1. **Tener lógica de negocio** (ir a Service)
2. **Retornar modelos SQLAlchemy** (retornar domain entities)
3. **Hacer commits/rollbacks** (el Service lo hace)
4. **Crear Session dentro** (inyectarla)

---

## 🎯 Patrón Service

### Propósito

**Contener la lógica de negocio**. Coordina Repositories y aplica reglas de dominio.

### Estructura

```python
# app/services/presupuesto_service.py

from typing import Optional, List
from app.domain.presupuesto.models import Presupuesto, PresupuestoNotFound
from app.domain.presupuesto.exceptions import EstadoInvalido
from app.repositories.presupuestos.presupuesto_repository import SQLAlchemyPresupuestoRepository

class PresupuestoService:
    """Service para gestión de presupuestos."""

    def __init__(self, repository: SQLAlchemyPresupuestoRepository):
        self.repository = repository

    def crear_presupuesto(self, obra_nombre: str, usuario_id: str, **kwargs) -> Presupuesto:
        """
        Crea un nuevo presupuesto.

        Args:
            obra_nombre: Nombre de la obra
            usuario_id: ID del usuario creador
            **kwargs: Campos adicionales

        Returns:
            Presupuesto creado

        Raises:
            ValueError: Si obra_nombre está vacío
        """
        # Validaciones de negocio
        if not obra_nombre or obra_nombre.strip() == "":
            raise ValueError("obra_nombre es requerido")

        # Crear entidad de dominio
        presupuesto = Presupuesto(
            obra_nombre=obra_nombre,
            usuario_id=usuario_id,
            estado="borrador",
            **kwargs
        )

        # Persistir
        return self.repository.save(presupuesto)

    def cambiar_estado(self, presupuesto_id: int, nuevo_estado: str) -> Presupuesto:
        """
        Cambia el estado de un presupuesto.

        Args:
            presupuesto_id: ID del presupuesto
            nuevo_estado: Nuevo estado (enviado, aceptado, rechazado)

        Returns:
            Presupuesto actualizado

        Raises:
            PresupuestoNotFound: Si no existe
            EstadoInvalido: Si transición no es válida
        """
        presupuesto = self.repository.get_by_id(presupuesto_id)
        if not presupuesto:
            raise PresupuestoNotFound(f"Presupuesto {presupuesto_id} no encontrado")

        # Validar transición de estados
        transiciones_validas = {
            "borrador": ["enviado"],
            "enviado": ["aceptado", "rechazado", "borrador"]
        }

        if nuevo_estado not in transiciones_validas.get(presupuesto.estado, []):
            raise EstadoInvalido(
                f"No se puede cambiar de {presupuesto.estado} a {nuevo_estado}"
            )

        presupuesto.estado = nuevo_estado
        return self.repository.save(presupuesto)
```

### Patrones de Service

#### ✅ SIEMPRE

1. **Recibir Repository por constructor** (no crearlo dentro)
2. **Retornar entidades de dominio** (no modelos SQLAlchemy)
3. **Validar reglas de negocio** (estado, permisos, etc.)
4. **Lanzar excepciones de dominio** (`PresupuestoNotFound`, `EstadoInvalido`)
5. **Manejar transacciones** (commit/rollback) si es necesario

#### ❌ NUNCA

1. **Acceder a DB directamente** (ir a Repository)
2. **Tener lógica de HTTP/Flask** (ir a Blueprint)
3. **Retornar modelos SQLAlchemy** (retornar domain entities)
4. **Hacer validaciones de formato** (ir a Blueprint)

---

## 🧩 Patrón Domain Model

### Propósito

**Definir entidades de negocio** con validaciones y comportamiento.

### Estructura

```python
# app/domain/presupuesto/models.py

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class Presupuesto:
    """Entidad de dominio Presupuesto."""

    id: Optional[int]
    obra_nombre: str
    cliente_nombre: Optional[str]
    usuario_id: str
    estado: str
    total_importe: float
    total_productos: int
    fecha_creacion: datetime
    fecha_envio: Optional[datetime]
    lineas: List[PresupuestoLinea]

    def __post_init__(self):
        """Validaciones post-creación."""
        if not self.obra_nombre or self.obra_nombre.strip() == "":
            raise ValueError("obra_nombre es requerido")

        if self.estado not in ["borrador", "enviado", "aceptado", "rechazado"]:
            raise ValueError(f"Estado inválido: {self.estado}")

    def agregar_linea(self, linea: PresupuestoLinea):
        """Agrega una línea y recalcula totales."""
        self.lineas.append(linea)
        self.recalcular_totales()

    def recalcular_totales(self):
        """Recalcula total_importe y total_productos."""
        self.total_importe = sum(linea.subtotal for linea in self.lineas)
        self.total_productos = len(self.lineas)

    def puede_editarse(self) -> bool:
        """Verifica si el presupuesto puede editarse."""
        return self.estado in ["borrador", "enviado"]
```

### Patrones de Domain Model

#### ✅ SIEMPRE

1. **Usar `@dataclass`** para entidades inmutables
2. **Validar en `__post_init__`** (reglas de dominio)
3. **Tener comportamiento** (métodos que modifican estado)
4. **No tener dependencias de SQLAlchemy** (puro dominio)

#### ❌ NUNCA

1. **Importar SQLAlchemy** (dominio puro)
2. **Tener lógica de persistencia** (ir a Repository)
3. **Ser un DTO sin comportamiento** (son entidades, no structs)

---

## 🌐 Patrón Blueprint

### Propósito

**Manejar requests HTTP** y coordinar con Services. En módulos complejos (Admin, Presupuesto), los Blueprints se dividen en archivos granulares dentro de una carpeta `routes/`.

### Estructura Modular

```python
# app/blueprints/presupuesto/routes/api_export.py

from flask import Blueprint, request, jsonify
from app.services.presupuesto.export_service import ExportService

# Cada sub-archivo define su propio blueprint o usa uno compartido
export_bp = Blueprint("export_api", __name__)

@export_bp.route("/export/<int:id>", methods=["POST"])
def export_budget(id):
    # Lógica de orquestación...
```

### Patrones de Blueprint

#### ✅ SIEMPRE

1. **Validar input primero** (Pydantic si es posible, o manual)
2. **Obtener usuario_id con helper** (`obtener_usuario_id()`)
3. **Crear Service dentro del endpoint**
4. **Dividir Blueprints grandes** en archivos temáticos (ej: `users_create.py`, `users_list.py`)
5. **Retornar JSON consistente** (`{"status": "success/error", ...}`)
6. **Manejar excepciones de dominio** específicamente
7. **Loguear errores inesperados**

#### ❌ NUNCA

1. **Tener lógica de negocio** (ir a Service)
2. **Acceder a DB directamente** (ir a Repository)
3. **Hardear usuario_id** (usar helper)
4. **Retornar modelos SQLAlchemy** (convertir a dict)
5. **Ignorar excepciones** (siempre manejar)

---

## 📨 Patrón de Respuesta JSON

### Formato Estándar

```python
# ✅ Success
{
    "status": "success",
    "message": "Presupuesto creado exitosamente",  # Opcional
    "data": {
        "id": 1,
        "obra_nombre": "Obra Test",
        ...
    }
}

# ✅ Error
{
    "status": "error",
    "message": "obra_nombre es requerido",
    "errors": {  # Opcional, para errores de validación
        "obra_nombre": ["Este campo es requerido"]
    }
}
```

### Códigos de Estado HTTP

| Código | Cuándo usarlo | Ejemplo |
|--------|---------------|---------|
| **200** | Success (GET, PUT, DELETE) | Presupuesto actualizado |
| **201** | Resource created (POST) | Presupuesto creado |
| **204** | Success sin contenido (DELETE) | Presupuesto eliminado |
| **400** | Bad request (validación) | Campo requerido faltante |
| **401** | Unauthorized (no auth) | Token inválido |
| **403** | Forbidden (sin permisos) | Usuario no puede ver esto |
| **404** | Not found | Presupuesto no existe |
| **409** | Conflict (duplicado) | Email ya existe |
| **500** | Internal server error | Error inesperado |

---

## ✅ Patrón de Validación

### Validación en Blueprint

```python
# ✅ BIEN: Validar en blueprint (formato, campos requeridos)
@bp.route("/api/presupuestos", methods=["POST"])
def crear_presupuesto():
    data = request.json

    # Validar campos requeridos
    if not data.get("obra_nombre"):
        return jsonify({
            "status": "error",
            "message": "obra_nombre es requerido"
        }), 400

    # Validar tipos
    if not isinstance(data.get("cantidad"), (int, float)):
        return jsonify({
            "status": "error",
            "message": "cantidad debe ser numérica"
        }), 400

    # Validar rangos
    if data.get("cantidad", 0) <= 0:
        return jsonify({
            "status": "error",
            "message": "cantidad debe ser mayor a 0"
        }), 400

    # ... llamar a service
```

### Validación en Service (Dominio)

```python
# ✅ BIEN: Validar en service (reglas de negocio)
def crear_presupuesto(self, obra_nombre: str, usuario_id: str) -> Presupuesto:
    # Validar regla de negocio
    presupuesto_existente = self.repository.get_by_obra_and_usuario(
        obra_nombre, usuario_id
    )
    if presupuesto_existente:
        raise ValueError(f"Ya existe un presupuesto para {obra_nombre}")

    # ... crear presupuesto
```

### Validación en Domain Model

```python
# ✅ BIEN: Validar en domain model (invariantes)
@dataclass
class Presupuesto:
    estado: str

    def __post_init__(self):
        if self.estado not in ["borrador", "enviado", "aceptado", "rechazado"]:
            raise ValueError(f"Estado inválido: {self.estado}")
```

---

## 🚨 Patrón de Error Handling

### Estrategia

1. **Blueprint**: Maneja errores de HTTP y validación
2. **Service**: Maneja errores de dominio (lanza excepciones)
3. **Repository**: Maneja errores de datos (lanza excepciones)

### Tipos de Excepciones

```python
# Excepciones de dominio (app/domain/*/exceptions.py)
class PresupuestoNotFound(Exception):
    """Presupuesto no encontrado."""
    pass

class EstadoInvalido(Exception):
    """Transición de estado inválida."""
    pass

class ClienteDuplicado(Exception):
    """Cliente con mismo nombre ya existe."""
    pass
```

### Manejo en Blueprint

```python
@bp.route("/api/presupuestos/<int:id>", methods=["PUT"])
def actualizar_presupuesto(id):
    try:
        # ... código
    except PresupuestoNotFound as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except EstadoInvalido as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error inesperado: {e}")
        return jsonify({
            "status": "error",
            "message": "Error interno del servidor"
        }), 500
```

---

## 🧪 Patrón de Testing

### Estructura de Tests

```python
# tests/integration/api/test_presupuesto_crud.py

import pytest
from app import db
from app.factories import PresupuestoFactory

class TestPresupuestoCRUD:
    """Tests CRUD de Presupuestos."""

    def test_crear_presupuesto(self, client, authenticated_user):
        """Test crear presupuesto nuevo."""
        # Arrange
        data = {
            "obra_nombre": "Obra Test",
            "cliente_nombre": "Cliente Test"
        }

        # Act
        response = client.post("/api/presupuestos", json=data)

        # Assert
        assert response.status_code == 201
        json_data = response.get_json()
        assert json_data["status"] == "success"
        assert json_data["data"]["obra_nombre"] == "Obra Test"

    def test_crear_presupuesto_sin_obra_falla(self, client):
        """Test que crear presupuesto sin obra_nombre falla."""
        # Arrange
        data = {"cliente_nombre": "Cliente Test"}

        # Act
        response = client.post("/api/presupuestos", json=data)

        # Assert
        assert response.status_code == 400
        json_data = response.get_json()
        assert json_data["status"] == "error"
```

### Patrones de Testing

#### ✅ SIEMPRE

1. **AAA Pattern** (Arrange, Act, Assert)
2. **Usar factories** (no crear datos manualmente)
3. **Tests descriptivos** (`test_crear_presupuesto_sin_obra_falla`)
4. **Mocks de APIs externas** (no llamar APIs reales)

#### ❌ NUNCA

1. **Tests interdependientes** (cada test es independiente)
2. **Hardear datos** (usar factories)
3. **Llamar APIs externas** (mockear todo)

---

## 🔐 Patrón de Auth

### Obtener Usuario ID

```python
# ✅ SIEMPRE usar este helper
from app.blueprints.auth.routes import obtener_usuario_id

try:
    usuario_id = obtener_usuario_id()
except ValueError:
    return jsonify({
        "status": "error",
        "message": "Authentication required"
    }), 401
```

### Decoradores

```python
from flask_login import login_required, current_user

@bp.route("/api/presupuestos")
@login_required  # ✅ Requiere auth
def listar_presupuestos():
    # current_user tiene el usuario autenticado
    usuario_id = current_user.id
    # ...
```

### Roles

```python
# ✅ Verificar rol en blueprint
@bp.route("/admin/usuarios")
@login_required
def admin_usuarios():
    if current_user.role not in ["admin", "super_admin"]:
        return jsonify({
            "status": "error",
            "message": "Permission denied"
        }), 403
    # ...
```

---

## 📚 Referencias

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Arquitectura hexagonal detallada
- **[GEMINI.md](../GEMINI.md)** - Reglas universales para AI tools
- **[GOTCHAS.md](GOTCHAS.md)** - Gotchas y anti-patrones

---

**Última actualización**: 2026-04-14
**Versión**: 1.0
