# 📦 API DISANO - Documentación del Proyecto

> **Versión:** 2.0
> **Fecha:** 2026-07-08
> **Estado:** ✅ Producción Activa (En migración a V2.1)
> **Stack:** FastAPI, PostgreSQL 15+, Pydantic, Gunicorn, Nginx
> **URL:** <https://api.eloymartinezcuesta.com>

---

## 🎯 Propósito del Proyecto

API REST FastAPI para gestionar un catálogo eléctrico de productos **DISANO/FOSNOVA** con:

- Consultas de productos con filtros avanzados
- Gestión CRUD de productos (solo admin)
- Generación de archivos BC3 (FIEBDC-3)
- Integración con BC3-Suite
- Autenticación robusta (API Key + 2FA/OTP)
- Versionado de API (V1 backward compatible, V2 snake_case)

---

## 🏗️ Arquitectura del Proyecto

### Stack Tecnológico

| Componente | Tecnología | Versión | Propósito |
|------------|------------|---------|-----------|
| **Backend** | FastAPI | 0.115.0 | API REST con validación automática |
| **Base de datos** | PostgreSQL | 15+ | Almacenamiento de productos (migrando desde SQLite) |
| **WSGI Server** | Gunicorn | 21.2+ | Producción con múltiples workers |
| **Web Server** | Nginx | 1.24+ | Reverse proxy + SSL |
| **ORM** | SQLAlchemy | 2.0+ | Abstracción de base de datos |
| **Validación** | Pydantic | 2.5.0 | Validación de datos y settings |
| **Testing** | pytest | 7.4+ | Tests automatizados |
| **Rate Limiting** | slowapi + Redis | 0.1.9+ | Control de solicitudes |
| **Logging** | loguru | 0.7.2 | Logging estructurado |
| **Security** | Argon2, Flask-Talisman | - | Hashing, headers |

### Arquitectura Hexagonal (Meta: Fase 4)

**Actual:** Monolítica con routers y middleware
**Meta:** Capas limpias y testables

```
API-DISANO/
├── app/
│   ├── api/                    # HTTP Layer (después de Fase 4)
│   │   ├── v1/
│   │   │   ├── productos.py
│   │   │   ├── familias.py
│   │   │   └── bc3.py
│   │   └── v2/
│   │       └── productos.py
│   ├── domain/                 # Business Logic (después de Fase 4)
│   │   ├── producto/
│   │   │   ├── models.py
│   │   │   ├── services.py
│   │   │   └── exceptions.py
│   │   └── security/
│   │       ├── api_key.py
│   │       └── rbac.py
│   ├── infrastructure/         # Data Access (después de Fase 4)
│   │   ├── repositories/
│   │   │   └── producto_repository.py
│   │   └── database/
│   │       └── connection.py
│   ├── routers/                # Actual (legacy)
│   │   ├── productos.py
│   │   ├── familias.py
│   │   └── bc3.py
│   ├── security/               # Sistema de seguridad
│   │   ├── api_key.py          # API Key verification
│   │   ├── rate_limiter.py     # Rate limiting
│   │   ├── user_agent_filter.py # Anti-scraping
│   │   ├── scraping_detector.py # Detection patterns
│   │   ├── logging_config.py   # Logging estructurado
│   │   └── __init__.py
│   ├── config.py               # ⚠️ Configuración centralizada
│   ├── models.py               # Modelos Pydantic
│   ├── database.py             # Conexión PostgreSQL
│   ├── middleware.py           # Middlewares (security, rate limiting)
│   ├── security.py             # Legacy (a eliminar)
│   └── main.py                 # Punto de entrada FastAPI
├── tests/                      # Tests (después de Fase 2)
│   ├── unit/
│   ├── integration/
│   └── factories/
├── docs/                       # Documentación
├── scripts/                    # Scripts de despliegue
├── database/                   # SQLite (legacy, migrando a PostgreSQL)
├── .env                        # Variables de entorno (NO en git)
├── .env.example                # Ejemplo de variables
├── requirements.txt            # Dependencias Python
└── wsgi.py                     # Entrada Gunicorn
```

---

## 🔒 Sistema de Seguridad

### Autenticación

**Niveles de acceso:**

1. **Público** - Sin autenticación:
   - `GET /` - Root info
   - `GET /health` - Health check

2. **Normal** - API Key:
   - `GET /api/productos/` - Listar productos
   - `GET /api/productos/{codigo}` - Obtener producto
   - `GET /api/familias/` - Listar familias
   - `GET /api/bc3/descripcion/{codigo}` - Datos BC3

3. **Admin** - Admin API Key + 2FA/OTP:
   - `POST /api/admin/productos` - Crear producto
   - `PUT /api/admin/productos/{codigo}` - Actualizar producto
   - `DELETE /api/admin/productos/{codigo}` - Eliminar producto

### 2FA/OTP (P1 - Fase 1)

**Implementación pendiente (Fase 1):**

- OTP de 6 dígitos enviado por email
- Válido por 10 minutos
- Máximo 3 intentos
- Obligatorio para endpoints admin

### Rate Limiting

**Configuración actual:**

- Por cliente: 30 requests/minuto
- Global: 1000 requests/minuto
- Burst: 10 requests

**Meta (Fase 1):** Migrar a Redis para shared state

### Anti-Scraping

**User Agents bloqueados:**

- python-requests, curl, wget
- scraper, crawler, bot, spider
- headless, phantom, selenium, scrapy

### Security Headers

**Headers implementados:**

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: no-referrer`

**Meta (Fase 1):** HSTS en producción

---

## 📡 Endpoints Principales

### API V1 (Backward Compatible)

**Disponible hasta:** 30 días después de anuncio de deprecación

| Endpoint | Método | Auth | Descripción |
|----------|--------|------|-------------|
| `/api/productos/` | GET | API Key | Listar productos V1 (mayúsculas) |
| `/api/productos/{codigo}` | GET | API Key | Producto V1 |
| `/api/productos/marca/{marca}` | GET | API Key | Productos por marca V1 |

### API V2 (Nuevo Estándar)

| Endpoint | Método | Auth | Descripción |
|----------|--------|------|-------------|
| `/api/productos/v2/list` | GET | API Key | Listar productos V2 (snake_case) |
| `/api/productos/v2/{codigo}` | GET | API Key | Producto V2 |
| `/api/productos/v2/marca/{marca}` | GET | API Key | Productos por marca V2 |
| `/api/productos/v2/familia/{familia}` | GET | API Key | Productos por familia V2 |

### Admin Endpoints

| Endpoint | Método | Auth | Descripción |
|----------|--------|------|-------------|
| `/api/admin/productos` | POST | Admin Key + 2FA | Crear producto |
| `/api/admin/productos/{codigo}` | PUT | Admin Key + 2FA | Actualizar producto |
| `/api/admin/productos/{codigo}` | DELETE | Admin Key + 2FA | Eliminar producto |
| `/api/admin/productos/{codigo}/precio` | PATCH | Admin Key + 2FA | Actualizar precio |

### Utilitarios

| Endpoint | Método | Auth | Descripción |
|----------|--------|------|-------------|
| `/` | GET | ❌ No | Info API |
| `/health` | GET | ❌ No | Health check |
| `/docs` | GET | ❌ No | Swagger UI (dev only) |

---

## 🗄️ Base de Datos

### Esquema Actual (SQLite)

**Ubicación:** `database/tarifa_disano.db`
**Registros:** ~8,288 productos
**Campos:** 38 por producto

**Campos importantes:**

- `CÓDIGO` - Código único del producto
- `DESCRIPCION` - Descripción completa
- `PVP_26_01_26` - Precio de venta
- `MARCA` - Disano o Fosnova
- `Familia_WEB` - Familia web
- `RAEE_A`, `RAEE_L` - Residuos RAEE
- `bc3_descripcion_corta` - Descripción BC3
- `img_url` - URL de imagen

### Meta: PostgreSQL (Fase 5)

**Características:**

- Base de datos: `api_disano_db`
- Usuario: `api_disano_user` (permisos limitados)
- Conexiones pooling: SQLAlchemy
- Migración automática de datos
- Backup automático diario

---

## 🔄 Versionado de API

### V1 → V2 Migration

**Cambios principales:**

| V1 (Old) | V2 (New) | Tipo |
|----------|----------|------|
| `CÓDIGO` | `codigo` | String |
| `DESCRIPCION` | `descripcion` | String |
| `PVP_26_01_26` | `pvp` | Float (static) |
| `MARCA` | `marca` | String |
| `Familia_WEB` | `familia_web` | String |
| `Url_ficha_tec` | `url_ficha_tec` | String |

**Ambos campos PVP mantenidos:**

- `pvp`: Nuevo campo estático
- `PVP_26_01_26`: Campo histórico (audit)

### Timeline

- **V1 Disponible:** Hasta deprecación + 30 días
- **V2 Disponible:** Ahora (recomendado)
- **V1 Deprecación:** TBD + 30 días
- **V1 Sunset:** TBD + 60 días

---

## 🚀 Despliegue en Producción

### Arquitectura de Producción

```
Internet
    ↓
Nginx (443/80, SSL/TLS, Static files)
    ↓
Gunicorn (4 workers, UvicornWorker, 127.0.0.1:8000)
    ↓
FastAPI App (API-DISANO v2.1)
    ↓
PostgreSQL (api_disano_db)
```

### Servicio Systemd (Gunicorn)

**Archivo:** `/etc/systemd/system/api-disano.service`

```ini
[Unit]
Description=API DISANO (FastAPI)
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/API-DISANO
Environment="PATH=/var/www/API-DISANO/venv/bin"
ExecStart=/var/www/API-DISANO/venv/bin/gunicorn \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --timeout 30 \
    --access-logfile /var/log/api-disano/access.log \
    --error-logfile /var/log/api-disano/error.log \
    wsgi:app

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### SSL/TLS con Let's Encrypt

```bash
sudo certbot --nginx -d api.eloymartinezcuesta.com
```

### Monitoreo y Logs

**Logs disponibles:**

- `/var/log/api-disano/access.log` - Requests HTTP
- `/var/log/api-disano/error.log` - Errores de aplicación
- `/var/log/api-disano/security.log` - Eventos de seguridad
- `/var/log/nginx/access.log` - Accesos al servidor web
- `/var/log/nginx/error.log` - Errores del servidor web

---

## 🛠️ Desarrollo

### Entorno Local

```bash
# 1. Entorno virtual
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar
cp .env.example .env
nano .env  # Editar API_KEYS, SECRET_KEY

# 4. Ejecutar
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing (Después de Fase 2)

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=app --cov-report=html

# Tests específicos
pytest tests/unit/test_config.py -v
pytest tests/integration/test_auth_idor.py -v

# Pre-commit
pre-commit run --all-files
```

### Linting (Después de Fase 3)

```bash
# Formatear código
black app/ tests/

# Lint
flake8 app/ tests/

# Docstrings
pydocstyle app/ tests/

# Security scan
bandit -r app/
safety check
pip-audit
```

---

## 📝 Reglas de Contribución

### ✅ HACER

1. **Usar `app/config.py`** para configuración
   - `from app.config import get_settings`
   - `settings = get_settings()`
   - NUNCA hardcodear valores

2. **Validación con Pydantic:**
   - Usar modelos de `app/models.py`
   - No validar manualmente

3. **Manejo de errores:**
   - Usar excepciones personalizadas de `app/domain/` (Fase 4)
   - Retornar `AdminResponseV2` para endpoints admin

4. **Base de datos:**
   - Usar `app.database.get_db_connection()`
   - Cerrar conexiones (context manager)

5. **Conventional Commits:**
   - `feat:` - Nueva funcionalidad
   - `fix:` - Corrección de bug
   - `refactor:` - Refactorización
   - `docs:` - Documentación
   - `test:` - Tests
   - `chore:` - Mantenimiento

### ❌ NO HACER

1. **NO usar** `app/security.py` (legacy)
   - Usar módulos en `app/security/` en su lugar

2. **NO hardcodear** configuración
   - No usar `os.getenv()` directamente
   - Usar `get_settings()`

3. **NO repetir** lógica de validación
   - Validar una vez en Pydantic
   - No validar nuevamente en endpoints

4. **NO ignorar** rate limiting
   - Todos los endpoints deben estar protegidos

5. **NO commitear** `.env` (está en .gitignore)

---

## 🐛 Problemas Conocidos

| Problema | Estado | Solución |
|----------|--------|----------|
| Bug `app/middleware.py:139` - `RATE_LIMIT` no definido | 🔴 Activo | Fase 1 - Fix rápido |
| Import legacy `from app.security import` | 🔴 Activo | Fase 1 - Migrar a `app.security.api_key` |
| Sin tests | 🔴 Activo | Fase 2 - Crear suite completa |
| Sin CI/CD | 🔴 Activo | Fase 3 - GitHub Actions |
| Logging no estructurado | 🟡 Parcial | Fase 1 - Loguru completo |
| Rate limiting in-memory | 🟡 Parcial | Fase 1 - Migrar a Redis |
| SQLite en producción | 🟡 Parcial | Fase 5 - Migrar a PostgreSQL |
| Sin 2FA/OTP | 🔴 Activo | Fase 1 - Implementar |

---

## 📚 Documentación Adicional

| Documento | Descripción |
|-----------|-------------|
| **MIGRATION_PLAN.md** | Plan completo de migración a V2.1 |
| **PATTERNS.md** | Patrones de código (BC3-Suite) |
| **ARCHITECTURE.md** | Arquitectura hexagonal (BC3-Suite) |
| **SECURITY_MODEL.md** | Modelo de seguridad RBAC (BC3-Suite) |
| **DEPLOYMENT_RUNBOOK.md** | Guía de despliegue en producción |

---

## 📊 Métricas del Proyecto

### Código

- **Líneas de código:** ~5,000
- **Archivos Python:** 17
- **Endpoints API:** 15+
- **Versión API:** V1 (legacy) + V2 (actual)

### Base de Datos

- **Productos:** ~8,288
- **Campos por producto:** 38
- **Familias:** ~50
- **Marcas:** 2 (Disano, Fosnova)

### Producción

- **URL:** <https://api.eloymartinezcuesta.com>
- **Uptime:** 99%+
- **Response time:** <200ms (average)
- **Rate limits:** 30/min per client, 1000/min global

### Meta (Después de migración)

- **Tests:** ≥250 tests
- **Coverage:** ≥80%
- **CI/CD:** GitHub Actions activos
- **Security:** Bandit + Safety + pip-audit

---

## 🤝 Contribuir

### Flujo de Trabajo

```bash
# 1. Crear feature branch
git checkout -b feature/nueva-funcionalidad

# 2. Trabajar y commitear
git add .
git commit -m "feat: add nueva funcionalidad"

# 3. Ejecutar tests y quality gates
pytest
pre-commit run --all-files

# 4. Crear PR
gh pr create --title "feat: add nueva funcionalidad" --base main

# 5. CI/CD corre automáticamente
# - Tests pytest
# - Coverage check
# - Linting (Black + Flake8)
# - Security scanning (Bandit + Safety + pip-audit)

# 6. Merge a main
git checkout main
git merge --no-ff feature/nueva-funcionalidad
git branch -d feature/nueva-funcionalidad
```

---

## 📧 Soporte

- **Email:** <eloy@eloymartinezcuesta.com>
- **Issues:** [GitHub Issues](https://github.com/EloyEMC/API-DISANO/issues)
- **Documentación:** [docs/](https://github.com/EloyEMC/API-DISANO/tree/main/docs)

---

## 📄 Licencia

**Todos los derechos reservados** - Proyecto privado y confidencial.

---

**Última actualización:** 2026-07-08
**Estado del proyecto:** 🟡 En migración a V2.1 (Fase 1/7)
**Versión actual:** 2.0
**Meta versión:** 2.1 (post-migración)
