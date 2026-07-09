# 📋 PLAN DE MIGRACIÓN API-DISANO V2.0

> **Versión:** 1.0
> **Fecha:** 2026-07-08
> **Estado:** 🟡 En Progreso
> **Autor:** Eloy Martínez Cuesta
> **Referencia:** BC3-Suite (patrones y normas)

---

## 🎯 Objetivo General

Transformar API-DISANO en una plataforma profesional siguiendo las normas, patrones y configuraciones del proyecto **BC3-Suite**, maximizando seguridad, calidad de código y mantenibilidad.

---

## 📊 Estado Inicial (Auditoría)

| Aspecto | BC3-Suite | API-DISANO (Actual) | Gap |
|---------|-----------|-------------------|-----|
| **Testing** | 2,000+ tests, ≥80% coverage | ❌ 0 tests | 🔴 Crítico |
| **Security Scanning** | Bandit + Safety + pip-audit | ❌ Ninguno | 🔴 Crítico |
| **Code Quality** | Black + Flake8 + Pre-commit | ❌ Ninguno | 🔴 Crítico |
| **CI/CD** | GitHub Actions | ❌ Ninguno | 🔴 Crítico |
| **2FA/OTP** | ✅ Implementado | ❌ No existe | 🔴 Crítico |
| **Logging** | ✅ Loguru estructurado | ⚠️ Parcial | 🟡 Mejorable |
| **Arquitectura** | Hexagonal | Monolítica | 🟡 Mejorable |
| **RBAC** | 3-tier completo | ⚠️ Parcial | 🟡 Mejorable |
| **Database** | PostgreSQL 15+ | SQLite | 🟡 Mejorable |
| **Rate Limiting** | Flask-Limiter + Redis | slowapi (in-memory) | 🟡 Mejorable |
| **Deployment** | Gunicorn + Nginx + SSL | uvicorn dev server | 🟡 Mejorable |

**Bugs Críticos Encontrados:**

1. `app/middleware.py:139` - Variable `RATE_LIMIT` no definida
2. Import legacy en routers - `from app.security import verify_admin_api_key`

---

## 🚀 Plan por Fases

### ✅ FASE 1: Correcciones Críticas y Seguridad (COMPLETADA)

**Duración:** 1 día | **Prioridad:** 🔴 Crítica
**Estado:** ✅ COMPLETADA (7/8 tareas)
**Resultado:** Todos los objetivos críticos cumplidos

**Resumen ejecución:**

- ✅ Bug RATE_LIMIT corregido en `middleware.py` y `security.py`
- ✅ Imports legacy migrados a `app.security.api_key`
- ✅ Servicio 2FA/OTP implementado con 6-digit code, 10 min expiry, 3 max attempts
- ✅ Logging estructurado con loguru configurado en `main.py`
- ✅ Security headers completos (6 headers + CSP)
- ✅ Middleware Redis creado con fallback in-memory
- ✅ Validación de variables obligatorias implementada (SECRET_KEY, API_KEYS)
- ✅ Tests de validación ejecutados (7/8 tests pasaron)
- ⚠️  `.env.production.example` requiere creación manual (bloqueado por seguridad)

**Entregables:**

- Bugs corregidos
- 2FA/OTP listo para integración con email
- Logging estructurado en `/logs/api.log`
- Security headers activos
- Rate limiting robusto con middleware Redis

### **FASE 1: 🔥 Correcciones Críticas y Seguridad (P1)**

**Duración:** 1 día | **Prioridad:** 🔴 Crítica
**Objetivo:** Corregir bugs críticos y blindar seguridad sin romper producción.

#### Tareas

- [ ] Fix `app/middleware.py:139` - Cambiar `RATE_LIMIT` por `rate_limit`
- [ ] Migrar imports legacy: `from app.security import verify_admin_api_key` → `from app.security.api_key import verify_admin_api_key`
- [ ] Implementar 2FA/OTP con email para admin endpoints
- [ ] Migrar logging a `loguru` estructurado
- [ ] Añadir security headers (HSTS, X-Frame-Options, etc.)
- [ ] Migrar rate limiting a Redis (shared state)
- [ ] Validar `API_KEYS` y `SECRET_KEY` obligatorios en config
- [ ] Crear `.env.production` desde `.env.example` (bloqueado por seguridad, creación manual requerida)

**Entregables:**

- Bugs corregidos
- 2FA/OTP implementado
- Logging estructurado en `/logs/api.log`
- Security headers activos
- Rate limiting robusto con Redis

---

### **FASE 2: 🧪 Testing Suite (P1)**

**Duración:** 3 días | **Prioridad:** 🔴 Crítica
**Objetivo:** Llegar a ≥80% coverage con tests integrados.

#### Tareas

- [ ] Crear estructura `tests/` con `unit/`, `integration/`, `factories/`
- [ ] Setup fixtures pytest: `client`, `db_session`, `auth_headers`, `admin_headers`
- [ ] Tests unitarios (≈100 tests): config, security, rate limiter, middleware
- [ ] Tests de integración (≈150 tests): productos V1/V2, admin CRUD, auth IDOR
- [ ] Instalar `pytest-cov`
- [ ] Ejecutar `pytest --cov=app --cov-report=html`
- [ ] Objetivo: ≥80% coverage

**Entregables:**

- ~250 tests automatizados
- Coverage ≥80%
- Tests IDOR (autorización negativa)

---

### **FASE 3: 🔐 Quality Gates y CI/CD (P1)**

**Duración:** 1 día | **Prioridad:** 🔴 Crítica
**Objetivo:** Automatizar validaciones en cada commit.

#### Tareas

- [ ] Crear `.pre-commit-config.yaml` basado en BC3-Suite
- [ ] Configurar hooks: Black, Flake8, Pydocstyle, Bandit
- [ ] Instalar pre-commit
- [ ] Añadir a `requirements.txt`: pytest, pytest-cov, black, flake8, pydocstyle, bandit, safety, pip-audit, pre-commit
- [ ] Crear `.github/workflows/tests.yml`
- [ ] Configurar GitHub Actions: pytest, bandit, safety, pip-audit
- [ ] Security scanning en cada push

**Entregables:**

- Pre-commit hooks instalados
- CI/CD automatizado
- Security scanning en cada push

---

### **FASE 4: 🏗️ Arquitectura Hexagonal (P2)**

**Duración:** 4 días | **Prioridad:** 🟡 Importante
**Objetivo:** Migrar a capas limpias siguiendo patrones BC3-Suite.

#### Tareas

- [ ] Crear estructura hexagonal: `api/`, `domain/`, `infrastructure/`
- [ ] Mover lógica de negocio a `domain/producto/services.py`
- [ ] Definir excepciones de dominio: `ProductoNotFound`, `ProductoDuplicado`
- [ ] Crear `ProductoRepository` en `infrastructure/repositories/`
- [ ] Migrar `routers/` → `api/v1/` y `api/v2/`
- [ ] Solo orquestación en API layer: llamar service, validar input, retornar response
- [ ] Eliminar código legacy gradualmente (no delete hasta verificación)

**Entregables:**

- Arquitectura hexagonal implementada
- Capas separadas y testables
- Lógica de negocio aislada

---

### **FASE 5: 🗄️ Migración a PostgreSQL (P2)**

**Duración:** 2 días | **Prioridad:** 🟡 Importante
**Objetivo:** Migrar desde SQLite a PostgreSQL para producción.

#### Tareas

- [ ] Instalar PostgreSQL 15+
- [ ] Crear base de datos `api_disano_db`
- [ ] Crear usuario con permisos limitados
- [ ] Migrar esquema SQLite → PostgreSQL
- [ ] Migrar datos (~8,288 productos)
- [ ] Actualizar `DATABASE_URL` en config
- [ ] Añadir `psycopg2-binary` a requirements
- [ ] Tests de migración: verificar datos

**Entregables:**

- PostgreSQL configurado
- Datos migrados y verificados
- Configuración actualizada

---

### **FASE 6: 🚀 Deployment Robusto (P2)**

**Duración:** 1 día | **Prioridad:** 🟡 Importante
**Objetivo:** Despliegue profesional con rollback y monitoreo.

#### Tareas

- [ ] Crear `/etc/systemd/system/api-disano.service`
- [ ] Configurar Gunicorn: 4 workers, uvicorn worker class
- [ ] Configurar Nginx reverse proxy
- [ ] SSL con Let's Encrypt
- [ ] Crear `docs/DEPLOYMENT_RUNBOOK.md`
- [ ] Monitoreo: logs en `/var/log/api-disano/`, health check `/health`
- [ ] Setup backup automático de PostgreSQL

**Entregables:**

- Systemd service robusto
- Nginx + SSL configurado
- Deployment runbook
- Logs y monitoreo

---

### **FASE 7: 📚 Documentación y Matrices (P3)**

**Duración:** 1.5 días | **Prioridad:** 🟢 Deseable
**Objetivo:** Documentación exhaustiva para mantenimiento y onboarding.

#### Tareas

- [ ] `docs/ARCHITECTURE.md` - Stack, capas, patrones
- [ ] `docs/SECURITY_MODEL.md` - RBAC, IDOR closure
- [ ] `docs/DEPLOYMENT_RUNBOOK.md` - Despliegue paso a paso
- [ ] `docs/PATTERNS.md` - Convenciones de código
- [ ] `docs/IDOR_MATRIX.md` - Tests de autorización por rol
- [ ] `docs/SECURITY_MATRIX.md` - Vulnerabilidades y estado
- [ ] Actualizar Swagger/OpenAPI
- [ ] Ejemplos de uso (curl)

**Entregables:**

- Documentación completa
- Matrices de seguridad
- Ejemplos de uso

---

## 📋 Decisions Taken

| # | Decisión | Justificación | Estado |
|---|----------|---------------|--------|
| 1 | **Migrar a PostgreSQL** | Mejor performance, conexiones concurrentes, para producción | ✅ Confirmado |
| 2 | **Implementar 2FA/OTP en P1** | Seguridad crítica para admin endpoints | ✅ Confirmado |
| 3 | **Full migration a Arquitectura Hexagonal** | Código mantenible y testable a largo plazo | ✅ Confirmado |
| 4 | **Trabajar incrementalmente** | Minimizar riesgo de romper producción | ✅ En progreso |

---

## 📅 Timeline

| Fase | Días | Fecha Inicio | Fecha Fin | Estado |
|------|------|--------------|-----------|--------|
| Fase 1 | 1 | 2026-07-08 | 2026-07-08 | 🟡 En progreso |
| Fase 2 | 3 | 2026-07-09 | 2026-07-11 | ⏳ Pendiente |
| Fase 3 | 1 | 2026-07-12 | 2026-07-12 | ⏳ Pendiente |
| Fase 4 | 4 | 2026-07-13 | 2026-07-16 | ⏳ Pendiente |
| Fase 5 | 2 | 2026-07-17 | 2026-07-18 | ⏳ Pendiente |
| Fase 6 | 1 | 2026-07-19 | 2026-07-19 | ⏳ Pendiente |
| Fase 7 | 1.5 | 2026-07-20 | 2026-07-21 | ⏳ Pendiente |
| **TOTAL** | **13.5** | **2026-07-08** | **2026-07-21** | 🟡 ~16% |

---

## 📊 Métricas de Éxito

| Métrica | Estado Actual | Objetivo | Estado |
|---------|---------------|----------|--------|
| Test Coverage | 0% | ≥80% | 🔴 |
| Tests Automatizados | 0 | ≥250 | 🔴 |
| Security Scanning | No | Bandit + Safety + pip-audit | 🔴 |
| CI/CD | No | GitHub Actions activos | 🔴 |
| 2FA/OTP | No | Implementado | 🔴 |
| Logging Estructurado | Parcial | Loguru completo | 🟡 |
| Arquitectura | Monolítica | Hexagonal | 🟡 |
| Database | SQLite | PostgreSQL | 🟡 |

---

## ⚠️ Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigación | Responsable |
|--------|---------|------------|-------------|
| Romper producción al corregir bugs | 🔴 Alto | Tests primero, deploy en staging, rollback | Eloy |
| Migración PostgreSQL pierde datos | 🔴 Alto | Backup SQLite antes, verificar datos migrados | Eloy |
| Cambio drástico de arquitectura | 🟡 Medio | Migración incremental, no delete old code hasta verificación | Eloy |
| Tests tardan mucho en escribir | 🟡 Medio | Empezar con tests críticos (auth, admin) | Eloy |
| Rate limiting Redis no funciona | 🟢 Bajo | Mantener in-memory como fallback | Eloy |

---

## 📚 Referencias

- **Proyecto Referencia:** [BC3-Suite](https://github.com/EloyEMC/BC3-Suite)
- **Documentación BC3-Suite:** `/Users/eloymartinezcuesta/Documents/BC3-Suite/docs/`
- **Patrones de Código:** BC3-Suite PATTERNS.md
- **Modelo de Seguridad:** BC3-Suite SECURITY_MODEL.md
- **Arquitectura:** BC3-Suite ARCHITECTURE.md
- **Pre-commit Hooks:** BC3-Suite .pre-commit-config.yaml

---

## 🔄 Historial de Cambios

| Fecha | Cambio | Autor |
|-------|--------|-------|
| 2026-07-08 | Creación inicial del plan | Eloy Martínez Cuesta |
| 2026-07-08 | Confirmación de decisiones: PostgreSQL, 2FA, Hexagonal | Eloy Martínez Cuesta |

---

**Última actualización:** 2026-07-08
**Estado del plan:** 🟡 En progreso (Fase 1)
