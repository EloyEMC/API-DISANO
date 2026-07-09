# 🔒 GUÍA DE SEGURIDAD - app/security/

**CUÁNDO LEER ESTE ARCHIVO:**
- Necesitas proteger un endpoint
- Quieres entender cómo funciona la autenticación
- Vas a modificar el sistema de seguridad

---

## 📁 MÓDULOS DE SEGURIDAD

```
security/
├── api_key.py              # Verificación de API keys
├── rate_limiter.py         # Rate limiting con slowapi
├── scraping_detector.py    # Detector de scraping
├── user_agent_filter.py    # Filtro de User-Agent
└── logging_config.py      # Configuración logging
```

---

## 🔑 AUTENTICACIÓN - API KEYS

### Archivo: `api_key.py`

### Función principal: `get_api_key()`
```python
from fastapi import Header, HTTPException
from typing import Annotated

X_API_KEY = Header(..., alias="X-API-Key")

def get_api_key(
    api_key: Annotated[str, X_API_KEY]
) -> str:
    """Verifica que la API key es válida."""
    settings = get_settings()

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="X-API-Key header is required"
        )

    if api_key not in settings.api_keys:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )

    return api_key
```

### Uso en endpoints
```python
from app.security.api_key import get_api_key

@router.get("/productos/")
async def listar_productos(
    api_key: str = Depends(get_api_key)  # ✅ Requiere auth
):
    return {"data": "productos"}
```

### Auth admin (escritura)
```python
def verify_admin_key(
    api_key: Annotated[str, X_API_KEY]
) -> str:
    """Verifica API key de administrador."""
    settings = get_settings()

    if api_key not in settings.admin_api_keys:
        raise HTTPException(
            status_code=403,
            detail="Admin API key required"
        )

    return api_key

# Uso
@router.post("/admin/productos")
async def crear_producto(
    api_key: str = Depends(verify_admin_key)  # ✅ Admin only
):
    pass
```

---

## ⏱️ RATE LIMITING

### Archivo: `rate_limiter.py`

### Sistema: slowapi
```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.config import get_settings

# Rate limiter configurado
rate_limiter = Limiter(key_func=get_remote_address)

def check_rate_limit(api_key: str, settings):
    """Verifica rate limit."""
    # Rate limit por cliente
    @rate_limiter.limit(f"{settings.rate_limit_per_client}/minute")
    def limit_func():
        return True

    # Rate limit global
    @rate_limiter.limit(f"{settings.rate_limit_global}/minute")
    def global_func():
        return True

    return True
```

### Uso en endpoints
```python
from app.security.rate_limiter import check_rate_limit
from app.config import get_settings

@router.get("/productos/")
async def listar_productos(
    api_key: str = Depends(get_api_key),
    settings = Depends(get_settings)
):
    check_rate_limit(api_key, settings)  # ✅ Verificar
    return {"data": "productos"}
```

### Configuración en .env
```bash
RATE_LIMIT_PER_CLIENT=30    # 30 requests/minuto por cliente
RATE_LIMIT_GLOBAL=1000       # 1000 requests/minuto global
RATE_LIMIT_BURST=10          # 10 en burst
```

### Respuesta 429
```json
{
  "detail": "Rate limit exceeded",
  "retry-after": 60
}
```

---

## 🤖 ANTI-SCRAPING

### Archivo: `scraping_detector.py`

### Función: `detect_scraping_pattern()`
```python
from collections import defaultdict
from datetime import datetime, timedelta
from app.security.logging_config import logger

# Almacenar requests por IP
request_history = defaultdict(list)

def detect_scraping_pattern(client_ip: str) -> bool:
    """Detecta patrones de scraping."""
    now = datetime.now()

    # Limpiar historial antiguo (> 1 hora)
    request_history[client_ip] = [
        req_time for req_time in request_history[client_ip]
        if now - req_time < timedelta(hours=1)
    ]

    # Contar requests en último minuto
    recent_requests = sum(
        1 for req_time in request_history[client_ip]
        if now - req_time < timedelta(minutes=1)
    )

    # Detectar patrón sospechoso
    if recent_requests > 100:  # Umbral
        logger.warning(f"Scraping detectado: {client_ip}")
        return True  # Es scraping

    request_history[client_ip].append(now)
    return False
```

### Uso
```python
from app.security.scraping_detector import detect_scraping_pattern
from fastapi import Request

@router.get("/productos/")
async def listar_productos(
    request: Request,  # Para obtener IP
    api_key: str = Depends(get_api_key)
):
    client_ip = request.client.host
    if detect_scraping_pattern(client_ip):
        raise HTTPException(
            status_code=403,
            detail="Scraping detected"
        )
```

---

## 🌐 USER AGENT FILTER

### Archivo: `user_agent_filter.py`

### User-Agent sospechosos
```python
SUSPICIOUS_AGENTS = [
    "curl",
    "wget",
    "python-requests",
    "scrapy",
    "selenium",
    "phantomjs",
    "headless"
]

def is_suspicious_user_agent(user_agent: str) -> bool:
    """Detecta User-Agents sospechosos."""
    if not user_agent:
        return True  # Sin UA = sospechoso

    user_agent_lower = user_agent.lower()

    for suspicious in SUSPICIOUS_AGENTS:
        if suspicious in user_agent_lower:
            return True

    return False
```

### Uso
```python
from app.security.user_agent_filter import is_suspicious_user_agent
from fastapi import Request, Header

@router.get("/productos/")
async def listar_productos(
    request: Request,
    user_agent: str = Header(None),
    api_key: str = Depends(get_api_key)
):
    if is_suspicious_user_agent(user_agent):
        raise HTTPException(
            status_code=403,
            detail="Suspicious User-Agent"
        )
```

---

## 🔐 COMBINAR MÚLTIPLES MÉTODOS

### Endpoint totalmente protegido
```python
@router.get("/productos/")
async def listar_productos(
    request: Request,
    user_agent: str = Header(None),
    api_key: str = Depends(get_api_key),
    settings = Depends(get_settings)
):
    # 1. Verificar API key
    # (ya hecho por Depends)

    # 2. Verificar rate limit
    check_rate_limit(api_key, settings)

    # 3. Detectar scraping
    client_ip = request.client.host
    if detect_scraping_pattern(client_ip):
        raise HTTPException(403, detail="Scraping detected")

    # 4. Verificar User-Agent
    if is_suspicious_user_agent(user_agent):
        raise HTTPException(403, detail="Suspicious UA")

    # 5. Lógica del endpoint
    return {"data": "productos"}
```

---

## 📊 LOGGING DE SEGURIDAD

### Archivo: `logging_config.py`

### Configuración con loguru
```python
from loguru import logger
import sys

# Configurar loguru
logger.remove()  # Eliminar handler default
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

# Logs de seguridad en archivo separado
logger.add(
    "logs/security.log",
    level="WARNING",
    rotation="10 MB",
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)
```

### Logging de eventos de seguridad
```python
from app.security.logging_config import logger

@router.post("/admin/productos")
async def crear_producto(
    producto: ProductoCreate,
    api_key: str = Depends(verify_admin_key),
    request: Request
):
    # Log de acción admin
    logger.info(
        f"Producto creado: {producto.codigo} "
        f"por API key: {api_key[:8]}... "
        f"desde IP: {request.client.host}"
    )

    return {"mensaje": "ok"}
```

---

## 🛡️ CORS CONFIGURATION

### Configuración en main.py
```python
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### En .env
```bash
# Orígenes permitidos
CORS_ORIGINS=https://mi-sitio.com,https://app.mi-sitio.com
```

---

## 📝 CHECKLIST DE SEGURIDAD

Antes de desplegar a producción:

- [ ] Cambiar todas las API keys por defecto
- [ ] Habilitar HTTPS (`HTTPS_ENABLED=true`)
- [ ] Configurar CORS correctamente
- [ ] Verificar rate limiting apropiado
- [ ] Revisar logs de seguridad
- [ ] Probar todos los endpoints
- [ ] Verificar que no hay endpoints sin auth
- [ ] Configurar firewall (solo puertos 80, 443)

---

## 🧪 TESTING DE SEGURIDAD

### Probar autenticación
```bash
# Sin API key (debe fallar 401)
curl http://localhost:8000/api/productos/

# Con API key inválida (debe fallar 403)
curl -H "X-API-Key: invalid-key" \
     http://localhost:8000/api/productos/

# Con API key válida (debe funcionar)
curl -H "X-API-Key: tu-key-valida" \
     http://localhost:8000/api/productos/
```

### Probar rate limiting
```bash
# Hacer muchas requests rápidamente
for i in {1..50}; do
  curl -s -H "X-API-Key: tu-key" \
       http://localhost:8000/api/productos/
done
# Debería devolver 429 después de cierto punto
```

### Probar admin endpoints
```bash
# Con API key normal (debe fallar 403)
curl -X POST \
     -H "X-API-Key: normal-key" \
     -H "Content-Type: application/json" \
     -d '{"codigo":"TEST"}' \
     http://localhost:8000/api/admin/productos

# Con admin key (debe funcionar)
curl -X POST \
     -H "X-API-Key: admin-key" \
     -H "Content-Type: application/json" \
     -d '{"codigo":"TEST"}' \
     http://localhost:8000/api/admin/productos
```

---

## 📚 REFERENCIAS

- **Desarrollo general:** `../GUIA_DESARROLLO.md`
- **Endpoints:** `../routers/GUIA_ENDPOINTS.md`
- **Variables:** `../../VARIABLES_ENTORNO.md`

---

**Última actualización:** 14 Feb 2026
