# 📖 GUÍA DE DESARROLLO - app/

**CUÁNDO LEER ESTE ARCHIVO:**
- Vas a modificar archivos dentro de `app/`
- Necesitas entender la arquitectura interna
- Quieres añadir funcionalidades o corregir bugs

---

## 📁 ESTRUCTURA DE app/

```
app/
├── config.py              # ⚠️ Configuración centralizada (Pydantic Settings)
├── models.py              # Modelos de datos (Pydantic)
├── database.py            # Conexión a SQLite
├── security.py            # ⚠️ LEGACY - No usar, prefer app/security/
├── main.py                # Punto de entrada FastAPI
├── routers/               # Endpoints de la API
│   ├── productos.py      # CRUD productos + BC3
│   ├── familias.py        # Consultas familias
│   └── bc3.py             # Endpoints específicos BC3
└── security/              # ✅ SISTEMA DE SEGURIDAD
    ├── api_key.py         # Verificación de API keys
    ├── rate_limiter.py    # Rate limiting
    ├── scraping_detector.py# Detector de scraping
    ├── user_agent_filter.py# Filtro User-Agent
    └── logging_config.py # Configuración logging
```

---

## ⚠️ REGLAS DE ORO

### ✅ HACER

1. **SIEMPRE leer configuración desde `config.py`:**
   ```python
   from app.config import get_settings
   settings = get_settings()
   api_keys = settings.api_keys
   ```

2. **Usar modelos Pydantic de `models.py`:**
   ```python
   from app.models import Producto, ProductoCreate
   ```

3. **Usar sistema de seguridad de `app/security/`:**
   ```python
   from app.security.api_key import get_api_key
   from app.security.rate_limiter import check_rate_limit
   ```

4. **Cerrar conexiones a BD:**
   ```python
   from app.database import get_db_connection
   with get_db_connection() as conn:
       cursor = conn.cursor()
       # ... operaciones
   # conn.commit() automático
   ```

### ❌ NO HACER

1. **NO usar `os.getenv()` directamente:**
   ```python
   # ❌ MAL
   api_key = os.getenv("API_KEY")

   # ✅ BIEN
   from app.config import get_settings
   settings = get_settings()
   api_key = settings.api_keys[0]
   ```

2. **NO usar `app/security.py` (legacy):**
   ```python
   # ❌ MAL
   from app.security import verify_api_key

   # ✅ BIEN
   from app.security.api_key import get_api_key
   ```

3. **NO repetir lógica de validación:**
   ```python
   # ❌ MAL (validar manualmente)
   if not producto.codigo or len(producto.codigo) > 50:
       raise HTTPException(400, "Código inválido")

   # ✅ BIEN (Pydantic valida)
   codigo: str = Field(..., min_length=1, max_length=50)
   ```

---

## 📝 AÑADIR UN NUEVO ENDPOINT

### Paso 1: Elegir ubicación

**¿Es un endpoint de productos?**
→ Ir a `app/routers/productos.py`

**¿Es un endpoint nuevo (módulo)?**
→ Crear nuevo archivo en `app/routers/`

### Paso 2: Estructura básica

```python
from fastapi import APIRouter, HTTPException, Depends
from app.config import get_settings
from app.security.api_key import get_api_key
from app.security.rate_limiter import check_rate_limit

router = APIRouter()

@router.get("/nuevo-endpoint")
async def nuevo_endpoint(
    api_key: str = Depends(get_api_key),
    settings = Depends(get_settings)
):
    # Verificar rate limit
    check_rate_limit(api_key, settings)

    # Tu lógica aquí
    return {"mensaje": "Hola"}
```

### Paso 3: Registrar en main.py

```python
from app.routers.mi_modulo import router as mi_modulo_router

app.include_router(
    mi_modulo_router,
    prefix="/api",
    tags=["mi_modulo"]
)
```

---

## 🔧 MODIFICAR UN ENDPOINT EXISTENTE

### Ejemplo: Añadir filtro de búsqueda

**Archivo:** `app/routers/productos.py`

**Antes:**
```python
@router.get("/productos/")
async def listar_productos(limit: int = 100):
    # ...
```

**Después:**
```python
@router.get("/productos/")
async def listar_productos(
    limit: int = 100,
    marca: Optional[str] = None,  # ✅ Nuevo filtro
    settings = Depends(get_settings)
):
    query = "SELECT * FROM productos WHERE 1=1"
    params = {"limit": limit}

    if marca:  # ✅ Aplicar filtro
        query += " AND marca = :marca"
        params["marca"] = marca

    # ... ejecutar query
```

---

## 🔒 AÑADIR SEGURIDAD A UN ENDPOINT

### Endpoint público (sin API key)
```python
@router.get("/publico")
async def endpoint_publico():
    return {"data": "público"}
```

### Endpoint protegido (requiere API key)
```python
from app.security.api_key import get_api_key

@router.get("/protegido")
async def endpoint_protegido(
    api_key: str = Depends(get_api_key)
):
    return {"data": "protegido", "api_key": api_key}
```

### Endpoint admin (requiere key admin)
```python
from app.security.api_key import verify_admin_key

@router.post("/admin/accion")
async def endpoint_admin(
    api_key: str = Depends(verify_admin_key)
):
    return {"mensaje": "acción admin completada"}
```

---

## 🗄️ TRABAJAR CON BASE DE DATOS

### Consulta simple
```python
from app.database import get_db_connection

def obtener_producto(codigo: str):
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM productos WHERE CÓDIGO = ?",
            (codigo,)
        )
        return cursor.fetchone()
```

### Consulta con parámetros
```python
def buscar_productos(marca: str, limit: int):
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """SELECT * FROM productos
               WHERE MARCA = ?
               LIMIT ?""",
            (marca, limit)
        )
        return cursor.fetchall()
```

### Insertar/Actualizar
```python
def crear_producto(producto: ProductoCreate):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO productos (CÓDIGO, DESCRIPCION, PVP_26_01_26)
               VALUES (?, ?, ?)""",
            (producto.codigo, producto.descripcion, producto.pvp)
        )
        # commit automático al salir del with
```

---

## 🧪 TESTING LOCAL

### Iniciar API local
```bash
cd /Volumes/WEBS/API_DISANO
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Probar endpoints
```bash
# Sin auth (401)
curl http://localhost:8000/api/productos/

# Con auth
curl -H "X-API-Key: tu-key" http://localhost:8000/api/productos/

# Con filtro
curl -H "X-API-Key: tu-key" \
     "http://localhost:8000/api/productos/?limit=5&marca=Disano"
```

---

## 🐛 DEBUGGING

### Ver logs
```bash
# Terminal 1: Ver logs en tiempo real
tail -f logs/api.log

# Terminal 2: Hacer requests
curl ...
```

### Logging en código
```python
from app.security.logging_config import logger

@router.get("/test")
async def test_endpoint():
    logger.info("Endpoint test llamado")
    logger.warning("Algo inusual")
    logger.error("Error crítico")
    return {"status": "ok"}
```

---

## 📦 USAR DEPENDENCIAS EXTERNAS

### Ejemplo: requests
```python
import requests

@router.get("/external-api")
async def consultar_api_externa():
    response = requests.get("https://api.ejemplo.com/data")
    return response.json()
```

### Ejemplo: httpx (async)
```python
import httpx

@router.get("/external-api")
async def consultar_api_externa():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.ejemplo.com/data")
        return response.json()
```

**Añadir a requirements.txt:**
```
httpx>=0.24.0
```

---

## ⚡ PERFORMANCE TIPS

1. **Usar consultas preparadas:** Para queries repetitivas
2. **Limitar resultados:** Siempre usar `LIMIT` en SELECT
3. **Índices en BD:** Para campos frecuentemente filtrados
4. **Async/await:** Para I/O operations

---

## 📚 REFERENCIAS RÁPIDAS

- **Configuración:** `../VARIABLES_ENTORNO.md`
- **Modelos:** `models.py` (ver archivo)
- **Endpoints guía:** `routers/GUIA_ENDPOINTS.md`
- **Seguridad:** `security/GUIA_SEGURIDAD.md`
- **Contexto proyecto:** `../PROYECTO.md`

---

**Última actualización:** 14 Feb 2026
