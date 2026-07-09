# 🛣️ GUÍA DE ENDPOINTS - app/routers/

**CUÁNDO LEER ESTE ARCHIVO:**
- Vas a crear o modificar endpoints de la API
- Necesitas entender cómo están estructurados
- Quieres añadir nuevas rutas

---

## 📁 ARCHIVOS EN ESTA CARPETA

```
routers/
├── productos.py      # CRUD de productos + endpoints BC3
├── familias.py        # Consultas de familias
└── bc3.py             # Endpoints específicos BC3
```

---

## 📋 ESTRUCTURA DE UN ENDPOINT

### Plantilla básica
```python
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from app.config import get_settings
from app.security.api_key import get_api_key
from app.security.rate_limiter import check_rate_limit

router = APIRouter()

@router.get("/ruta")
async def endpoint_nombre(
    # Parámetros de query
    param1: str,
    param2: Optional[int] = None,
    # Dependencias (inyectadas automáticamente)
    api_key: str = Depends(get_api_key),
    settings = Depends(get_settings)
):
    # 1. Verificar rate limit
    check_rate_limit(api_key, settings)

    # 2. Lógica del endpoint
    resultado = tu_logica(param1, param2)

    # 3. Retornar respuesta
    return resultado
```

---

## 📦 ENDPOINTS DE PRODUCTOS

**Archivo:** `productos.py`

### Listar productos
```python
@router.get("/productos/")
async def listar_productos(
    limit: int = Query(100, ge=1, le=500),
    marca: Optional[str] = None,
    familia: Optional[str] = None,
    buscar: Optional[str] = None,
    api_key: str = Depends(get_api_key),
    settings = Depends(get_settings)
):
    check_rate_limit(api_key, settings)

    # Construir query dinámica
    query = "SELECT * FROM productos WHERE 1=1"
    params = {}

    if marca:
        query += " AND MARCA = :marca"
        params["marca"] = marca

    if familia:
        query += " AND Familia_WEB = :familia"
        params["familia"] = familia

    if buscar:
        query += " AND DESCRIPCION LIKE :buscar"
        params["buscar"] = f"%{buscar}%"

    query += " LIMIT :limit"
    params["limit"] = limit

    # Ejecutar
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        productos = cursor.fetchall()

    return productos
```

### Obtener un producto
```python
@router.get("/productos/{codigo}")
async def obtener_producto(
    codigo: str,
    api_key: str = Depends(get_api_key)
):
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM productos WHERE CÓDIGO = ?",
            (codigo,)
        )
        producto = cursor.fetchone()

    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    return producto
```

### Crear producto (ADMIN)
```python
from app.models import ProductoCreate
from app.security.api_key import verify_admin_key

@router.post("/admin/productos")
async def crear_producto(
    producto: ProductoCreate,
    api_key: str = Depends(verify_admin_key)
):
    # Pydantic valida automáticamente

    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO productos (CÓDIGO, DESCRIPCION, PVP_26_01_26)
                       VALUES (?, ?, ?)""",
                (producto.codigo, producto.descripcion, producto.pvp)
            )
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=400,
                detail="El código ya existe"
            )

    return {"mensaje": "Producto creado", "codigo": producto.codigo}
```

---

## 🏷️ ENDPOINTS DE FAMILIAS

**Archivo:** `familias.py`

### Listar todas las familias
```python
@router.get("/familias/")
async def listar_familias(
    api_key: str = Depends(get_api_key)
):
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT Familia_WEB FROM productos WHERE Familia_WEB IS NOT NULL"
        )
        familias = [row["Familia_WEB"] for row in cursor.fetchall()]

    return {"familias": familias}
```

### Estadísticas por familia
```python
from pydantic import BaseModel

class FamiliaStats(BaseModel):
    familia: str
    total_productos: int
    con_pvp: int

@router.get("/familias/stats")
async def stats_familias(
    api_key: str = Depends(get_api_key)
):
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """SELECT
                   Familia_WEB,
                   COUNT(*) as total,
                   COUNT(PVP_26_01_26) as con_pvp
               FROM productos
               WHERE Familia_WEB IS NOT NULL
               GROUP BY Familia_WEB"""
        )
        stats = [FamiliaStats(**row) for row in cursor.fetchall()]

    return stats
```

---

## 📄 ENDPOINTS BC3

**Archivo:** `bc3.py`

### Obtener descripción BC3
```python
@router.get("/bc3/descripcion/{codigo}")
async def obtener_bc3(
    codigo: str,
    api_key: str = Depends(get_api_key)
):
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """SELECT bc3_descripcion_corta,
                      bc3_descripcion_larga,
                      bc3_product_type
               FROM productos
               WHERE CÓDIGO = ?""",
            (codigo,)
        )
        resultado = cursor.fetchone()

    if not resultado or not resultado["bc3_descripcion_corta"]:
        raise HTTPException(status_code=404, detail="BC3 no disponible")

    return {
        "codigo": codigo,
        "descripcion_corta": resultado["bc3_descripcion_corta"],
        "descripcion_larga": resultado["bc3_descripcion_larga"],
        "product_type": resultado["bc3_product_type"]
    }
```

---

## 🎯 PARÁMETROS DE QUERY

### Query parameters (opcional)
```python
@router.get("/productos/")
async def listar(
    # Opcional, string
    marca: Optional[str] = None,
    # Con valor por defecto
    limit: int = 100,
    # Con validación
    offset: int = Query(0, ge=0),
    # Múltiples valores
    etiquetas: Optional[List[str]] = Query(None)
):
    pass
```

### Path parameters (requerido)
```python
@router.get("/productos/{codigo}")
async def obtener(
    codigo: str,  # Requerido, en la URL
    subcampo: Optional[str] = None  # Opcional
):
    pass
```

---

## 🔄 RESPONSES HTTP

### Retornar datos simples
```python
return {"mensaje": "ok", "total": 42}
```

### Retornar lista
```python
return [item1, item2, item3]
```

### Con código de status
```python
from fastapi import status

return {"mensaje": "creado"}, status.HTTP_201_CREATED
```

---

## ⚠️ ERRORES HTTP

### Usar HTTPException
```python
from fastapi import HTTPException

@router.get("/productos/{codigo}")
async def obtener_producto(codigo: str):
    producto = buscar_en_bd(codigo)

    if not producto:
        raise HTTPException(
            status_code=404,
            detail="Producto no encontrado"
        )

    return producto
```

### Códigos comunes
| Código | Uso |
|--------|-----|
| 200 | OK (éxito) |
| 201 | Created (recurso creado) |
| 400 | Bad Request (datos inválidos) |
| 401 | Unauthorized (sin API key) |
| 403 | Forbidden (sin permisos) |
| 404 | Not Found (recurso no existe) |
| 422 | Unprocessable Entity (validación Pydantic falló) |
| 429 | Too Many Requests (rate limit) |
| 500 | Internal Server Error |

---

## 🧪 TESTING ENDPOINTS

### Con curl
```bash
# GET básico
curl -H "X-API-Key: tu-key" \
     http://localhost:8000/api/productos/

# Con parámetros
curl -H "X-API-Key: tu-key" \
     "http://localhost:8000/api/productos/?limit=5&marca=Disano"

# POST
curl -X POST \
     -H "X-API-Key: admin-key" \
     -H "Content-Type: application/json" \
     -d '{"codigo":"TEST","descripcion":"Producto test","pvp":10.5}' \
     http://localhost:8000/api/admin/productos

# PUT
curl -X PUT \
     -H "X-API-Key: admin-key" \
     -H "Content-Type: application/json" \
     -d '{"pvp":15.99}' \
     http://localhost:8000/api/admin/productos/TEST

# DELETE
curl -X DELETE \
     -H "X-API-Key: admin-key" \
     http://localhost:8000/api/admin/productos/TEST
```

### Con Python requests
```python
import requests

headers = {"X-API-Key": "tu-key"}

# GET
response = requests.get(
    "http://localhost:8000/api/productos/",
    headers=headers,
    params={"limit": 10, "marca": "Disano"}
)
productos = response.json()

# POST
response = requests.post(
    "http://localhost:8000/api/admin/productos",
    headers={"X-API-Key": "admin-key"},
    json={
        "codigo": "TEST",
        "descripcion": "Producto test",
        "pvp": 10.5
    }
)
```

---

## 📚 REFERENCIAS

- **Desarrollo general:** `../GUIA_DESARROLLO.md`
- **Modelos de datos:** `../models.py`
- **Seguridad:** `../security/GUIA_SEGURIDAD.md`
- **Variables entorno:** `../../VARIABLES_ENTORNO.md`

---

**Última actualización:** 14 Feb 2026
