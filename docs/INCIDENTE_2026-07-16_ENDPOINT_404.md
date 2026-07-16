# 🚨 INCIDENTE FRONTEND NO MUESTRA RESULTADOS BÚSQUEDA - 2026-07-16

**STATUS:** 🟢 RESUELTO  
**FECHA:** 2026-07-16  
**TIEMPO DE RESOLUCIÓN:** ~1 hora  
**IMPACTO:** 🟡 MEDIO - Frontend mostraba 0 resultados al buscar productos

---

## 📋 PROBLEMA ENCONTRADO

### ❌ FRONTEND BC3-Suite NO MUESTRA RESULTADOS

**Síntoma:** Búsqueda de productos (ej: "toledo") devuelve 0 resultados  
**Endpoint Frontend:** `/api/buscar-productos` (POST)  
**Endpoint Backend Real:** `/api/productos/buscar-productos` (POST)  
**Estado:** 404 Not Found

**Ruta de llamada:**
```javascript
// BC3-Suite frontend (api-disano-helper.js)
const data = await this._executeWithRetry('/api/buscar-productos', {...});

// ← ERROR: 404 Not Found
// Frontend llama a endpoint que no existe
```

**Causa raíz:** 
- BC3-Suite frontend JS llama a `/api/buscar-productos`
- API DISANO backend tiene `/api/productos/buscar-productos`
- Migración a arquitectura hexagonal cambió estructura de rutas
- Frontend no actualizó a nueva estructura de rutas

**Impacto:** Usuarios no pueden buscar productos en BC3-Suite

---

## 🔧 SOLUCIONES APLICADAS

### 1. CREAR ENDPOINT POST EN API DISANO

**Archivo:** `app/interfaces/http/productos.py`  
**Endpoint:** `POST /api/productos/buscar-productos`  
**Código:**

```python
@router.post("/buscar-productos")
async def buscar_productos_post(
    request: BuscarProductosRequest,
    service: ProductoService = Depends(get_producto_service),
) -> dict:
    """
    POST endpoint for product search (BC3-Suite frontend compatibility).
    
    Wrapper of /v2/paginated that accepts JSON body.
    Maps frontend parameters → backend V2 format.
    Returns response in frontend-expected format.
    """
    try:
        # Map frontend parameters → backend V2 format
        filters = {}
        if request.termino:
            filters["buscar"] = request.termino
        if request.marca:
            filters["marca"] = request.marca
        if request.familia:
            filters["familia"] = request.familia
        if request.con_bc3:
            filters["bc3_product_type"] = "luminaria"

        # Build pagination DTO (always page 1 for frontend search)
        pagination_dto = PaginationRequestDTO(
            page=1,
            per_page=min(request.limit, 100),
        )

        # Call service with pagination and filters
        paginated_response = service.buscar_productos_paginado(
            pagination_dto, filters
        )

        # Serialize response using ProductoResponseSerializer
        response_dict = ProductoResponseSerializer.serialize_paginated_response(
            paginated_response, "producto"
        )

        # Map backend response → frontend-expected format
        frontend_response = {
            "status": "success",
            "resultados": response_dict.get("items", []),
            "count": len(response_dict.get("items", [])),
            "total": response_dict.get("total", 0),
        }

        return frontend_response

    except Exception as e:
        # Return error in frontend-expected format
        return {
            "status": "error",
            "resultados": [],
            "count": 0,
            "total": 0,
            "error": str(e),
        }
```

### 2. AGREGAR CAMPOS DE IMAGEN A MODELO

**Archivo:** `app/infrastructure/models/producto_clean.py`  
**Campos agregados:**
```python
imagen: Optional[str] = None
img_url: Optional[str] = None  
ean_13: Optional[float] = None  # SQLite REAL → conversión a String en entity
```

**Conversión en to_entity():**
```python
def to_entity(self) -> ProductoEntity:
    return ProductoEntity(
        # ... otros campos ...
        imagen=self.imagen,
        img_url=self.img_url,
        ean_13=str(self.ean_13) if self.ean_13 is not None else None,
    )
```

### 3. ACTUALIZAR FRONTEND BC3-Suite

**Archivo:** `app/static/js/api-disano-helper.js`  
**Cambios:**
```javascript
// ❌ ANTES (endpoint incorrecto)
const data = await this._executeWithRetry('/api/buscar-productos', {...});

// ✅ DESPUÉS (endpoint correcto)
const data = await this._executeWithRetry('/api/productos/buscar-productos', {...});

// Eliminado warning deprecated
console.warn('buscarProductos is deprecated...'); // ← REMOVIDO
```

### 4. DEPLOY A PRODUCCIÓN

**VPS:** `root@46.62.227.64`  
**Archivos deployados:**

```bash
# API DISANO (producción)
/var/www/API-DISANO/app/interfaces/http/productos.py
/var/www/API-DISANO/app/infrastructure/models/producto_clean.py
/var/www/API-DISANO/database/tarifa_disano.db (vista productos_clean actualizada)

# BC3-Suite (producción)
/var/www/pdf-to-bc3/app/static/js/api-disano-helper.js

# Restart servicios
systemctl restart api-disano.service
systemctl restart pdfbudgets.service
```

---

## ✅ VERIFICACIÓN

### Test en Producción

```bash
# Test endpoint POST con búsqueda "toledo"
curl -X POST https://api.eloymartinezcuesta.com/api/productos/buscar-productos \
  -H "Content-Type: application/json" \
  -H "X-API-Key: TU_API_KEY" \
  -d '{"termino":"toledo","limit":20}'

# Resultado esperado:
{
  "status": "success",
  "resultados": [
    {
      "codigo": "2202430100",
      "nombre": "MUELLES TOLEDO 0243 PARA ENCASTRAR",
      "imagen": "IP_springtol.jpg",
      "img_url": "/images/products/IP_springtol.jpg",
      "imagen_url": "/images/products/IP_springtol.jpg",
      "ean_13": "8016535134525",
      ...
    }
    # ... más productos toledo (20 total)
  ],
  "count": 20,
  "total": 20
}
```

**Resultado obtenido:** ✅ 20 productos Toledo con imágenes

---

## 📊 CAMBIOS REALIZADOS

### Commits

**API-DISANO (4139a54):**
```
feat: agregar endpoint POST /api/productos/buscar-productos y modelo con campos de imagen

- Crear endpoint POST /api/productos/buscar-productos para compatibilidad frontend
- Agregar campos imagen, img_url, ean_13 a ProductoModelClean
- Convertir ean_13 Float → String (SQLite REAL a String entity)
- Mapear termino → buscar, limit → per_page en wrapper
- Devolver formato frontend: {status, resultados, count, total}

Resuelve: Frontend BC3-Suite muestra 0 resultados
Validado: Toledo devuelve 20 productos con imágenes en producción
```

**BC3-Suite (5a901a6e):**
```
fix: actualizar endpoint búsqueda de productos a /api/productos/buscar-productos

- Cambiar endpoint de /api/buscar-productos a /api/productos/buscar-productos
- Eliminar warning deprecated de buscarProductos
- Mapeo directo a ApiDisanoEnhanced.buscarProductos sin console.warn
- Compatible con API DISANO producción (endpoint POST funcional)

Resuelve: 404 Not Found al buscar productos en frontend
Validado: Toledo devuelve 20 resultados con imágenes
```

### Archivos modificados

**API-DISANO:**
- `app/interfaces/http/productos.py` (endpoint POST)
- `app/infrastructure/models/producto_clean.py` (campos imagen)
- `database/tarifa_disano.db` (vista productos_clean)

**BC3-Suite:**
- `app/static/js/api-disano-helper.js` (endpoint + warning fix)

---

## 🔒 LESSONS LEARNED

### Qué salió bien

- ✅ Diagnóstico rápido (log de frontend mostraba 404)
- ✅ Comunicación local-producción verificada
- ✅ Endpoints probados en producción antes de deploy
- ✅ Validación con datos reales (búsqueda Toledo)

### Qué mejoraría

- ❌ Tests de integración frontend-backend
- ❌ Documentación de rutas API más explícita
- ❌ Monitoreo de errores 404 en producción
- ❌ Validación automática de endpoints después de deploy

### Recomendaciones futuras

1. Crear contrato de API explícito (OpenAPI/Swagger)
2. Implementar tests de integración E2E
3. Monitorear logs 404 en producción (alertas)
4. Documentar cambios de rutas en CHANGELOG.md
5. Validar compatibilidad frontend-backend en CI/CD

---

## 📚 REFERENCIAS

**GitHub:**
- API-DISANO commit: https://github.com/EloyEMC/API-DISANO/commit/4139a54
- BC3-Suite commit: https://github.com/EloyEMC/BC3-Suite/commit/5a901a6e

**Issues:**
- API-DISANO Issue #2: https://github.com/EloyEMC/API-DISANO/issues/2
- BC3-Suite Issue #8: https://github.com/EloyEMC/BC3-Suite/issues/8

**Documentación relacionada:**
- `README.md` - API documentation
- `ARCHITECTURE.md` - Arquitectura hexagonal
- `SECURITY_MODEL.md` - Autenticación API Keys

**Credenciales:**
- VPS: root@46.62.227.64
- API Production: https://api.eloymartinezcuesta.com

---

**Creado:** 2026-07-16 12:00 UTC  
**Última actualización:** 2026-07-16 12:40 UTC  
**Responsable:** Eloy Martínez Cuesta  
**Estado:** 🟢 RESUELTO Y VALIDADO EN PRODUCCIÓN

