# Project-Specific Skills - API-DISANO

These skills are specifically tailored for the API-DISANO project, following BC3-Suite patterns and conventions.

---

## Loading Protocol

When working on this project:

1. Match task context against these triggers
2. Load the matching skill file before editing code
3. Follow the patterns described in the skill
4. If no project skill matches, fall back to global skills

---

## Skill: `api-disano-security`

**Trigger:** When working with authentication, API keys, rate limiting, 2FA/OTP, or security features in this project.

**Description:** Enforce security patterns specific to API-DISANO following BC3-Suite security model:

- ALWAYS use `app/security/api_key.py` for authentication (NOT `app/security.py` - legacy)
- Use `verify_api_key()` dependency for normal endpoints
- Use `verify_admin_api_key()` for admin endpoints + 2FA/OTP
- Respect rate limiting: 30/min per client, 1000/min global
- Validate API keys against `config.py`
- Use `app/middleware.py` for rate limiting and anti-scraping
- Implement 2FA/OTP for admin endpoints (6-digit code, 10 min expiry, max 3 attempts)

**Path:** `.pi/skills/api-disano-security.md`

**Reference:** BC3-Suite `docs/SECURITY_MODEL.md`

---

## Skill: `api-disano-config`

**Trigger:** When modifying configuration, environment variables, or settings.

**Description:** Centralized configuration patterns following BC3-Suite config structure:

- ALWAYS use `app/config.py` for configuration (no hardcoded values)
- Use Pydantic Settings for type-safe configuration
- Read from environment variables using `.env` file
- NEVER commit `.env` (in `.gitignore`)
- Copy `.env.example` to `.env` and edit for local dev
- Validate required settings on startup (`SECRET_KEY`, `API_KEYS`)
- Use `get_settings()` cached with `@lru_cache()`

**Path:** `.pi/skills/api-disano-config.md`

**Reference:** BC3-Suite `config.py`

---

## Skill: `api-disano-pydantic`

**Trigger:** When working with models, validation, or request/response schemas.

**Description:** Pydantic patterns for API-DISANO following BC3-Suite conventions:

- Define models in `app/models.py` (V1 legacy) and `app/domain/producto/models.py` (V2 hexagonal)
- Use Pydantic v2.5.0+ patterns with `field_validator`
- Use Pydantic Settings for configuration models
- Validate all input/output with Pydantic models
- Use snake_case for field names in V2 (V1 backward compatible with UPPERCASE)
- Define custom exceptions as Pydantic models

**Path:** `.pi/skills/api-disano-pydantic.md`

**Reference:** BC3-Suite `PATTERNS.md` - Domain Model section

---

## Skill: `api-disano-router`

**Trigger:** When creating or modifying API endpoints.

**Description:** Router patterns for API-DISANO following BC3-Suite blueprint conventions:

- Create routers in `app/routers/` (current) or `app/api/v{N}/` (post-hexagonal)
- Use `APIRouter()` from FastAPI
- Import routers in `app/main.py`
- Add versioning: `/api/v2/...` for new endpoints
- Maintain backward compatibility for V1 endpoints
- Validate input at router level (format, required fields)
- Delegate business logic to services (post-hexagonal)
- Return consistent JSON responses: `{status, message, data}`
- Use appropriate HTTP status codes

**Path:** `.pi/skills/api-disano-router.md`

**Reference:** BC3-Suite `PATTERNS.md` - Blueprint section

---

## Skill: `api-disano-hexagonal`

**Trigger:** When implementing or refactoring to hexagonal architecture.

**Description:** Follow BC3-Suite hexagonal architecture patterns:

- **HTTP Layer (`app/api/`)**: Routes, controllers, request/response handling
- **Domain Layer (`app/domain/`)**: Business logic, entities, domain exceptions
- **Infrastructure Layer (`app/infrastructure/`)**: Data access, repositories, DB connections

**Rules:**

- HTTP Layer NEVER has business logic
- Domain Layer NEVER knows about HTTP or DB
- Infrastructure Layer NEVER has business logic
- Services coordinate Repositories (no direct DB access in Services)
- Use dataclasses for Domain Models with `__post_init__` validation
- Repository pattern: `save()`, `get_by_id()`, `list()`, `delete()`

**Path:** `.pi/skills/api-disano-hexagonal.md`

**Reference:** BC3-Suite `docs/ARCHITECTURE.md` and `PATTERNS.md`

---

## Skill: `api-disano-testing`

**Trigger:** When writing or running tests.

**Description:** Follow BC3-Suite testing patterns:

- Use pytest with AAA pattern (Arrange, Act, Assert)
- Use factories for test data (no hardcoded values)
- Mock external APIs (DISANO API, email service)
- Test structure: `tests/unit/`, `tests/integration/`, `tests/factories/`
- Fixtures: `client`, `db_session`, `auth_headers`, `admin_headers`
- Test coverage target: ≥80%
- Write negative tests for authorization (IDOR closure)
- Test both V1 (legacy) and V2 (hexagonal) endpoints

**Path:** `.pi/skills/api-disano-testing.md`

**Reference:** BC3-Suite `PATTERNS.md` - Testing section

---

## Skill: `api-disano-database`

**Trigger:** When working with database operations or migrations.

**Description:** Database patterns for API-DISANO:

- Development: SQLite (`database/tarifa_disano.db`)
- Production: PostgreSQL 15+ (`api_disano_db`)
- Testing: PostgreSQL test database (`api_disano_test_db`)
- Use SQLAlchemy 2.0+ with async support
- Use context managers for connections (`with get_db_connection()`)
- Use parameterized queries (prevent SQL injection)
- Plan migration: SQLite → PostgreSQL (Fase 5)
- Backup strategy: Daily PostgreSQL dumps

**Path:** `.pi/skills/api-disano-database.md`

---

## Skill: `api-disano-deployment`

**Trigger:** When deploying to production or configuring servers.

**Description:** Deployment patterns following BC3-Suite runbook:

- Stack: Gunicorn + Nginx + SSL
- Systemd service: `/etc/systemd/system/api-disano.service`
- Gunicorn config: 4 workers, UvicornWorker, 127.0.0.1:8000
- Nginx: Reverse proxy, SSL with Let's Encrypt, security headers
- Logs: `/var/log/api-disano/` (access, error, security)
- Health check: `/health`
- Deployment pattern: Pull → Backup → Install → Tests → Restart → Verify → Rollback if needed

**Path:** `.pi/skills/api-disano-deployment.md`

**Reference:** BC3-Suite `docs/DEPLOYMENT_RUNBOOK.md`

---

## Skill: `api-disano-code-quality`

**Trigger:** When writing code or setting up quality gates.

**Description:** Follow BC3-Suite code quality standards:

- **Formatter**: Black 23.12.1, line-length=100
- **Linter**: Flake8 6.1.0, PEP 8 compliance
- **Docstrings**: Pydocstyle 6.3.0, Google convention
- **Pre-commit hooks**: Black, Flake8, Pydocstyle, Bandit
- **CI/CD**: GitHub Actions (Tests, Linting, Security Scanning)
- **Security scanning**: Bandit, Safety, pip-audit
- **No print()** in production code
- **No debug code** (pdb, breakpoint())

**Path:** `.pi/skills/api-disano-code-quality.md`

**Reference:** BC3-Suite `.pre-commit-config.yaml`

---

## Skill: `api-disano-rbac`

**Trigger:** When implementing authorization or access control.

**Description:** Follow BC3-Suite 3-tier RBAC model:

- **Level 1 (Admin)**: Full access to all resources
- **Level 2 (Coordinator)**: Zone + own resources (read), own (write)
- **Level 3 (Sales)**: Own resources only

**Rules:**

- Check access at ROUTE level, never in service
- Return HTTP 404 on denial (never 403 - hides existence)
- Single-writer principle: one authorization check per handler
- Use canonical API: `app/domain/*/visibility.py`

**Path:** `.pi/skills/api-disano-rbac.md`

**Reference:** BC3-Suite `docs/SECURITY_MODEL.md`

---

## Skill: `zai-integration`

**Trigger:** When integrating Z.ai LLM provider or AI features.

**Description:** Z.ai provider integration for API-DISANO:

- **Provider**: Z.ai (configured in `.pi/settings.json`)
- **Models**:
  - Default: `zai-sonnet` (balanced reasoning + speed)
  - Fast: `zai-haiku` (quick responses)
  - Code: `zai-sonnet` (code generation)
  - Reasoning: `zai-opus` (deep analysis)
- **Features**:
  - Streaming enabled
  - Function calling enabled
  - JSON mode enabled
  - Temperature: 0.7 (balanced)
- **Usage**: AI-powered features like BC3 description generation

**Path:** `.pi/skills/zai-integration.md`

---

## Skill: `api-disano-error-handling`

**Trigger:** When implementing error handling or custom exceptions.

**Description:** Error handling patterns following BC3-Suite conventions:

- Define domain exceptions in `app/domain/*/exceptions.py`
- HTTP Layer handles HTTP errors (400, 401, 403, 404, 409, 500)
- Service Layer throws domain exceptions
- Repository Layer throws data exceptions
- Consistent JSON error responses: `{status: "error", message: "...", errors: {}}`
- Log unexpected errors with context
- Never ignore exceptions

**Path:** `.pi/skills/api-disano-error-handling.md`

**Reference:** BC3-Suite `PATTERNS.md` - Error Handling section

---

## 🔄 Integration with BC3-Suite Patterns

API-DISANO adopts these patterns from BC3-Suite:

| Pattern | BC3-Suite Location | API-DISANO Implementation |
|---------|-------------------|-------------------------|
| **Arquitectura Hexagonal** | `docs/ARCHITECTURE.md` | Fase 4 - Full migration |
| **Repository Pattern** | `PATTERNS.md` | `app/infrastructure/repositories/` |
| **Service Layer** | `PATTERNS.md` | `app/domain/*/services.py` |
| **Domain Models** | `PATTERNS.md` | `app/domain/*/models.py` |
| **3-tier RBAC** | `docs/SECURITY_MODEL.md` | `app/domain/security/rbac.py` |
| **AAA Testing** | `PATTERNS.md` | `tests/` structure |
| **Pre-commit Hooks** | `.pre-commit-config.yaml` | `.pre-commit-config.yaml` |
| **CI/CD** | `.github/workflows/` | `.github/workflows/tests.yml` |

---

**Last updated:** 2026-07-08
**Reference Project:** BC3-Suite (<https://github.com/EloyEMC/BC3-Suite>)
