# Guía de seguridad de `app/security/`

Esta guía describe las dependencias y utilidades de seguridad actuales. La migración del
módulo heredado ya terminó: la aplicación instala los middlewares desde `app/middleware.py`,
no desde `app/security.py`. El archivo `app/security.py` se conserva únicamente como
compatibilidad heredada y no debe usarse en código nuevo.

## Qué usar

| Necesidad | Interfaz actual |
| --- | --- |
| Proteger un endpoint con una API key | `app.security.api_key.verify_api_key` |
| Proteger una operación administrativa | `app.security.api_key.require_admin_api_key` |
| Configurar límites con SlowAPI | `app.security.rate_limiter.limiter` |
| Identificar clientes para rate limiting | `app.security.rate_limiter.get_api_key_identifier` |
| Evaluar un User-Agent | `app.security.user_agent_filter.is_user_agent_allowed` |
| Analizar patrones de scraping | `app.security.scraping_detector.detector` |
| Registrar eventos de seguridad | `app.security.logging_config.log_security_event` |

Los middlewares globales (`APIKeyMiddleware`, `RateLimitMiddleware`,
`UserAgentMiddleware` y `SecurityHeadersMiddleware`) pertenecen a `app/middleware.py`.
`app/main.py` activa autenticación, rate limiting y filtro de User-Agent solo en producción;
las cabeceras de seguridad se aplican en todos los entornos.

## Autenticación de endpoints

La API key normal se envía en `X-API-Key`. `verify_api_key` devuelve una vista parcial de la
key para logging y responde `401` si falta o no es válida.

```python
from fastapi import APIRouter, Depends

from app.security.api_key import verify_api_key

router = APIRouter()


@router.get("/productos")
async def list_products(api_key_preview: str = Depends(verify_api_key)):
    return {"authenticated_as": api_key_preview}
```

Las operaciones administrativas usan `X-Admin-API-Key` y la dependencia
`require_admin_api_key`:

```python
from fastapi import APIRouter, Depends

from app.security.api_key import require_admin_api_key

admin_router = APIRouter()


@admin_router.post("/admin/productos", dependencies=[Depends(require_admin_api_key)])
async def create_product():
    return {"created": True}
```

En desarrollo, la validación administrativa se omite según el contrato actual. No dependas
de ese comportamiento para probar producción.

## Rate limiting

La aplicación activa `RateLimitMiddleware` en producción. El límite por cliente proviene de
`Settings.rate_limit_per_client`; cada cliente se identifica por `X-API-Key` y, si no existe,
por su IP. Una respuesta limitada usa estado `429`, cabecera `Retry-After` y cabeceras
`X-RateLimit-*`.

Para límites específicos de un endpoint con SlowAPI:

```python
from fastapi import Request

from app.security.rate_limiter import limiter


@router.get("/productos")
@limiter.limit("30/minute")
async def list_products(request: Request):
    return {"items": []}
```

El parámetro `request` es obligatorio para que SlowAPI resuelva el cliente. El almacenamiento
configurado es en memoria; varios workers no comparten ese estado.

## User-Agent y scraping

El middleware de producción rechaza User-Agents que contienen patrones configurados como
`curl`, `wget`, `bot` o `selenium`. La utilidad equivalente para una comprobación explícita
recibe el objeto `Request` completo:

```python
from fastapi import HTTPException, Request

from app.security.user_agent_filter import is_user_agent_allowed


async def require_allowed_user_agent(request: Request) -> None:
    if not is_user_agent_allowed(request):
        raise HTTPException(status_code=403, detail="User-Agent not allowed")
```

La detección heurística se expone mediante la instancia compartida `detector`:

```python
from fastapi import HTTPException, Request

from app.security.scraping_detector import detector


async def reject_suspicious_traffic(request: Request) -> None:
    analysis = detector.analyze_request(request)
    if analysis["is_suspicious"]:
        raise HTTPException(status_code=403, detail="Suspicious activity detected")
```

Estas utilidades mantienen estado en memoria. Si se usan con varios workers, el estado debe
moverse a un almacén compartido antes de tratarlo como una protección global.

## Logging

`app/main.py` llama a `setup_logging()` al iniciar. Para eventos de seguridad, registra solo
una vista parcial o derivada de las credenciales; nunca escribas una key completa en logs.

```python
from app.security.logging_config import log_security_event

log_security_event(
    event_type="auth_failed",
    details="Invalid API key",
    client_ip="203.0.113.10",
    api_key="abcd1234...",
)
```

## Configuración relevante

La configuración se centraliza en `app.config.Settings`. Las variables principales son:

```bash
ENVIRONMENT=production
API_KEYS=replace-with-a-strong-random-key
ADMIN_API_KEYS=replace-with-a-separate-strong-random-key
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_CLIENT=30
RATE_LIMIT_GLOBAL=1000
RATE_LIMIT_BURST=10
CORS_ORIGINS=https://example.com,https://app.example.com
HTTPS_ENABLED=true
```

No reutilices keys normales como keys administrativas. En producción, el arranque valida la
configuración obligatoria mediante `Settings.validate_required()`.

## Comprobaciones manuales

Exporta valores de prueba antes de ejecutar los ejemplos. Se especifica un User-Agent de
navegador porque el middleware de producción bloquea el User-Agent predeterminado de `curl`.

```bash
export API_BASE_URL="http://localhost:8000"
export API_KEY="replace-with-a-test-key"
export ADMIN_API_KEY="replace-with-a-test-admin-key"
export INVALID_API_KEY="invalid-test-key"
export BROWSER_USER_AGENT="Mozilla/5.0 security-check"
```

```bash
# Sin key: 401 en producción.
curl -i -A "${BROWSER_USER_AGENT}" \
  "${API_BASE_URL}/api/productos/"

# Key inválida: 401.
curl -i -A "${BROWSER_USER_AGENT}" \
  -H "X-API-Key: ${INVALID_API_KEY}" \
  "${API_BASE_URL}/api/productos/"

# Key válida: el endpoint procesa la petición.
curl -i -A "${BROWSER_USER_AGENT}" \
  -H "X-API-Key: ${API_KEY}" \
  "${API_BASE_URL}/api/productos/"

# Sin key administrativa: 403 en una operación admin protegida.
curl -i -X DELETE -A "${BROWSER_USER_AGENT}" \
  -H "X-API-Key: ${API_KEY}" \
  "${API_BASE_URL}/api/admin/productos/TEST"

# Key administrativa válida: la operación alcanza el endpoint.
curl -i -X DELETE -A "${BROWSER_USER_AGENT}" \
  -H "X-Admin-API-Key: ${ADMIN_API_KEY}" \
  "${API_BASE_URL}/api/admin/productos/TEST"
```

Use credenciales y datos desechables: el último ejemplo ejecuta una operación destructiva si
el producto existe.

## Checklist de producción

- [ ] `ENVIRONMENT=production` y secretos únicos están configurados.
- [ ] Las keys normales y administrativas son distintas y no aparecen en logs ni repositorio.
- [ ] CORS contiene solo orígenes autorizados.
- [ ] HTTPS y HSTS están verificados detrás del proxy real.
- [ ] Los límites se probaron con la topología real de workers.
- [ ] Los endpoints administrativos exigen `X-Admin-API-Key`.
- [ ] Las respuestas `401`, `403` y `429` fueron verificadas en producción o staging.

## Referencias

- [Guía de desarrollo](../GUIA_DESARROLLO.md)
- [Variables de entorno](../../VARIABLES_ENTORNO.md)
