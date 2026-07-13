# API DISANO V2 - Guía de Migración para BC3 Suite App

## 🎯 OBJETIVO

Actualizar BC3 Suite App para usar **endpoints V2** de API DISANO con mejor estructura, filtros y compatibilidad BC3 Suite schema.

## 📋 URL BASE CORRECTA

```javascript
const BASE_URL = "http://localhost:8000";  // Desarrollo
const BASE_URL = "https://api-disano-production.com";  // Producción
const API_BASE_URL = "/api/productos/";     // OBLIGATORIO para endpoints
```

## 🔗 ENDPOINTS V2 DISPONIBLES

### 1. **Health Check** (Validación de servicio)

```javascript
// URL
GET /health

// Ejemplo
fetch(`${BASE_URL}/health`)

// Response (200 OK)
{
  "status": "ok",
  "service": "api-disano"
}
```

### 2. **Búsqueda V1 (Backward Compatible)**

```javascript
// URL
GET /api/productos/?buscar={termino}&limit={limit}

// Ejemplo
fetch(`${BASE_URL}${API_BASE_URL}?buscar=toledo&limit=10`)

// Response (200 OK)
[
  {
    "codigo": "112533-00",
    "descripcion": "621 SAFETY-S.E. -S.A. 1H LED 2/3/4 CLD-E BLANCO",
    "marca": "Disano",
    "pvp": 85.50,
    // ... campos estándar
  },
  // ... más resultados
]
```

### 3. **V2 List - Búsqueda Mejorada** ⭐ **RECOMENDADO**

```javascript
// URL
GET /api/productos/v2/list?buscar={termino}&limit={limit}&marca={marca}&familia={familia}

// Ejemplo - Búsqueda simple
fetch(`${BASE_URL}${API_BASE_URL}v2/list?buscar=toledo&limit=10`)

// Ejemplo - Con filtros
fetch(`${BASE_URL}${API_BASE_URL}v2/list?buscar=toledo&limit=10&marca=Disano&familia=interiores`)

// Response (200 OK)
[
  {
    "codigo": "112533-00",
    "descripcion": "621 SAFETY-S.E. -S.A. 1H LED 2/3/4 CLD-E BLANCO",
    "marca": "Disano",
    "familia": "interiores",
    "pvp": 85.50,
    "bc3_descripcion_corta": "621 SAFETY LED",
    "bc3_product_type": "iluminacion",
    "bc3_descripcion_completa": "Lámpara de seguridad...",
    // ... campos BC3 Suite
  },
  // ... más resultados
]
```

### 4. **V2 Individual - Producto por Código**

```javascript
// URL
GET /api/productos/v2/{codigo}

// Ejemplo
fetch(`${BASE_URL}${API_BASE_URL}v2/11253300`)

// Response (200 OK)
{
  "codigo": "11253300",
  "descripcion": "621 SAFETY-S.E. -S.A. 1H LED 2/3/4 CLD-E BLANCO",
  "marca": "Disano",
  "familia": "interiores",
  "pvp": 85.50,
  "bc3_descripcion_corta": "621 SAFETY LED",
  "bc3_product_type": "iluminacion",
  "bc3_descripcion_completa": "Lámpara de seguridad...",
  // ... todos los campos disponibles
}

// Response (404 Not Found)
{
  "detail": "Producto no encontrado"
}
```

### 5. **V2 Filtro Marca**

```javascript
// URL
GET /api/productos/v2/marca/{marca}?limit={limit}

// Ejemplo
fetch(`${BASE_URL}${API_BASE_URL}v2/marca/Disano?limit=10`)

// Response (200 OK)
[
  {
    "codigo": "112533-00",
    "marca": "Disano",
    "familia": "interiores",
    "pvp": 85.50,
    "bc3_descripcion_corta": "621 SAFETY LED",
    "bc3_product_type": "iluminacion",
    // ... campos BC3 Suite
  },
  // ... más resultados Disano
]
```

### 6. **V2 Filtro Familia**

```javascript
// URL
GET /api/productos/v2/familia/{familia}?limit={limit}

// Ejemplo
fetch(`${BASE_URL}${API_BASE_URL}v2/familia/interiores?limit=10`)

// Response (200 OK)
[
  {
    "codigo": "112533-00",
    "marca": "Disano",
    "familia": "interiores",
    "pvp": 85.50,
    "bc3_descripcion_corta": "621 SAFETY LED",
    "bc3_product_type": "iluminacion",
    // ... campos BC3 Suite
  },
  // ... más resultados interiores
]
```

## 🔄 MIGRACIÓN: V1 → V2

### **ARCHIVOS BC3 SUITE A ACTUALIZAR:**

1. **`app/utils/api_disano_client.py`** - Backend Python
2. **`app/static/js/api-disano-helper.js`** - Frontend JS (deprecated)
3. **`app/static/js/busqueda_disano.js`** - Lógica de búsqueda
4. **`app/static/js/buscar_productos.js`** - UI de búsqueda

### **MIGRACIÓN Paso a Paso:**

#### **Paso 1: Actualizar `api_disano_client.py`**

```python
# ANTES (V1)
# app/utils/api_disano_client.py

def buscar_producto_por_codigo(self, codigo: str) -> dict:
    response = requests.get(f"{self.api_url}/api/productos/{codigo}")
    # ...

def buscar_productos(self, termino: str, opciones: dict = None) -> list:
    url = f"{self.api_url}/api/productos/"
    params = {"buscar": termino}
    # ...

# DESPUÉS (V2)
def buscar_producto_por_codigo(self, codigo: str) -> dict:
    response = requests.get(f"{self.api_url}/api/productos/v2/{codigo}")
    # ...

def buscar_productos(self, termino: str, opciones: dict = None) -> list:
    opciones = opciones or {}
    params = {
        "buscar": termino,
        "limit": opciones.get("limit", 10),
        "marca": opciones.get("marca", ""),
        "familia": opciones.get("familia", ""),
    }
    response = requests.get(f"{self.api_url}/api/productos/v2/list", params=params)
    # ...

def buscar_productos_por_marca(self, marca: str, limit: int = 10) -> list:
    response = requests.get(f"{self.api_url}/api/productos/v2/marca/{marca}", params={"limit": limit})
    # ...

def buscar_productos_por_familia(self, familia: str, limit: int = 10) -> list:
    response = requests.get(f"{self.api_url}/api/productos/v2/familia/{familia}", params={"limit": limit})
    # ...
```

#### **Paso 2: Actualizar `api-disano-helper.js`**

```javascript
// ANTES (deprecated)
// app/static/js/api-disano-helper.js

async function buscarProductos(termino, opciones = {}) {
    // ... deprecated logic
}

// DESPUÉS (V2)
const ApiDisano = (function() {
    'use strict';

    async function buscarProductosV2(termino, opciones = {}) {
        const { limit = 10, marca = '', familia = '' } = opciones;
        const params = new URLSearchParams({
            buscar: termino,
            limit: limit.toString(),
            ...(marca && { marca }),
            ...(familia && { familia })
        });

        const response = await fetch(`/api/productos/v2/list?${params}`);
        if (!response.ok) throw new Error(`Error: ${response.status}`);
        return await response.json();
    }

    async function buscarProductoPorCodigoV2(codigo) {
        const response = await fetch(`/api/productos/v2/${codigo}`);
        if (!response.ok) throw new Error(`Error: ${response.status}`);
        return await response.json();
    }

    async function buscarProductosPorMarcaV2(marca, limit = 10) {
        const response = await fetch(`/api/productos/v2/marca/${encodeURIComponent(marca)}?limit=${limit}`);
        if (!response.ok) throw new Error(`Error: ${response.status}`);
        return await response.json();
    }

    async function buscarProductosPorFamiliaV2(familia, limit = 10) {
        const response = await fetch(`/api/productos/v2/familia/${encodeURIComponent(familia)}?limit=${limit}`);
        if (!response.ok) throw new Error(`Error: ${response.status}`);
        return await response.json();
    }

    // Export API V2
    return {
        buscarProductos: buscarProductosV2,  // Main function
        buscarProducto: buscarProductoPorCodigoV2,
        buscarProductosPorMarca: buscarProductosPorMarcaV2,
        buscarProductosPorFamilia: buscarProductosPorFamiliaV2,
        setupAutocomplete: setupAutocompleteV2  // Updated autocomplete
    };
})();
```

#### **Paso 3: Actualizar `busqueda_disano.js`**

```javascript
// ANTES
async function buscarProductos() {
    const termino = inputBuscador.value;
    const resultados = await ApiDisano.buscarProductos(termino, {
        limit: 10
    });
    // ...
}

// DESPUÉS
async function buscarProductos() {
    const termino = inputBuscador.value;
    const marcaSelect = document.getElementById('marca-select');
    const familiaSelect = document.getElementById('familia-select');

    const resultados = await ApiDisano.buscarProductos(termino, {
        limit: 10,
        marca: marcaSelect.value || '',
        familia: familiaSelect.value || ''
    });

    // ... renderizado de resultados con campos BC3 Suite
    mostrarResultados(resultados);
}

function mostrarResultados(productos) {
    resultadosContainer.innerHTML = '';

    productos.forEach(producto => {
        const card = document.createElement('div');
        card.className = 'producto-card';

        // Usar campos BC3 Suite si disponibles
        const descripcion = producto.bc3_descripcion_completa || producto.descripcion;
        const tipo = producto.bc3_product_type || 'general';

        card.innerHTML = `
            <h3>${producto.codigo}</h3>
            <p class="descripcion">${descripcion}</p>
            <p class="tipo">${tipo}</p>
            <p class="precio">PVP: €${producto.pvp}</p>
            <p class="marca-familia">
                ${producto.marca} - ${producto.familia}
            </p>
        `;

        resultadosContainer.appendChild(card);
    });
}
```

## 🎨 CAMPOS BC3 SUITE V2

### **Campos Disponibles en Respuesta V2:**

```javascript
{
  // Campos estándar
  "codigo": "11253300",
  "descripcion": "621 SAFETY-S.E. -S.A. 1H LED 2/3/4 CLD-E BLANCO",
  "marca": "Disano",
  "familia": "interiores",
  "pvp": 85.50,

  // Campos BC3 Suite (nuevos en V2)
  "bc3_descripcion_corta": "621 SAFETY LED",
  "bc3_product_type": "iluminacion",
  "bc3_descripcion_completa": "Lámpara de seguridad LED 2/3/4 CLD-E BLANCO",

  // Campos técnicos (si disponibles)
  "unidades": 10,
  "stock": true,
  // ...
}
```

## ⚡ EJEMPLOS DE USO

### **Búsqueda Simple (Frontend):**

```javascript
// App de BC3 Suite
async function buscarProductosEnApp(termino) {
    const resultados = await ApiDisano.buscarProductos(termino, {
        limit: 10
    });

    console.log('Resultados encontrados:', resultados.length);

    resultados.forEach(producto => {
        console.log('Producto:', {
            codigo: producto.codigo,
            descripcion: producto.bc3_descripcion_completa,
            marca: producto.marca,
            familia: producto.familia,
            tipo: producto.bc3_product_type
        });
    });
}

// Uso
buscarProductosEnApp('toledo');
```

### **Búsqueda con Filtros (Frontend):**

```javascript
async function buscarProductosConFiltros(termino, marca, familia) {
    const resultados = await ApiDisano.buscarProductos(termino, {
        limit: 10,
        marca: marca,      // Filtro marca
        familia: familia   // Filtro familia
    });

    return resultados;
}

// Uso
const resultados = await buscarProductosConFiltros('toledo', 'Disano', 'interiores');
```

### **Producto Individual (Backend Python):**

```python
# Flask Backend BC3 Suite
from app.utils.api_disano_client import ApiDisanoClient

client = ApiDisanoClient(api_url="http://localhost:8000")

# Obtener producto por código V2
producto = client.buscar_producto_por_codigo("11253300")

print(f"Código: {producto['codigo']}")
print(f"Descripción: {producto['bc3_descripcion_completa']}")
print(f"Tipo: {producto['bc3_product_type']}")
```

## 🚀 VALIDACIÓN DE MIGRACIÓN

### **Tests Locales:**

```bash
# 1. Iniciar servidor
cd /Users/eloymartinezcuesta/Documents/API-DISANO-main
source .venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# 2. Probar endpoints
# Health check
curl http://localhost:8000/health

# V2 List
curl "http://localhost:8000/api/productos/v2/list?buscar=toledo&limit=5"

# V2 Individual
curl http://localhost:8000/api/productos/v2/11253300

# V2 Marca
curl "http://localhost:8000/api/productos/v2/marca/Disano?limit=5"

# V2 Familia
curl "http://localhost:8000/api/productos/v2/familia/interiores?limit=5"
```

### **Tests BC3 Suite App:**

```javascript
// En Browser Console (BC3 Suite App)
const resultados = await ApiDisano.buscarProductos('toledo', { limit: 10 });
console.log('V2 resultados:', resultados.length);

const producto = await ApiDisano.buscarProducto('11253300');
console.log('V2 producto:', producto.bc3_descripcion_completa);

const marca = await ApiDisano.buscarProductosPorMarca('Disano', 5);
console.log('V2 marca:', marca.length);
```

## 📊 COMPARACIÓN V1 vs V2

| Feature | V1 | V2 (Nuevo) |
|---------|----|-----------|
| **Búsqueda** | `?buscar=X&limit=Y` | `?buscar=X&limit=Y&marca=M&familia=F` |
| **Individual** | `/api/productos/{codigo}` | `/api/productos/v2/{codigo}` |
| **Filtros** | Solo búsqueda | Búsqueda + marca + familia |
| **Schema** | Estándar | BC3 Suite schema completo |
| **Campos BC3** | Parcial | Completo (corta, type, completa) |
| **Estructura** | Flat | Enriched + BC3 fields |

## ⚠️ ERRORES COMUNES Y SOLUCIONES

### **Error: 404 Not Found**

**Causa:** URL sin prefijo `/api/productos/`

**Solución:**

```javascript
// ❌ MAL
fetch(`${BASE_URL}/v2/list?buscar=toledo`)

// ✅ BIEN
fetch(`${BASE_URL}/api/productos/v2/list?buscar=toledo`)
```

### **Error: 500 Server Error**

**Causa:** Dependencias faltantes (loguru)

**Solución:**

```bash
cd /Users/eloymartinezcuesta/Documents/API-DISANO-main
source .venv/bin/activate
pip install loguru
```

### **Error: Schema mismatch**

**Causa:** Map row to V2 usa brackets `[CÓDIGO WEB]`

**Solución:** Ya corregido en Fase 2 (brackets eliminados)

## ✅ CHECKLIST MIGRACIÓN

- [ ] Actualizar `app/utils/api_disano_client.py` con endpoints V2
- [ ] Actualizar `app/static/js/api-disano-helper.js` con funciones V2
- [ ] Actualizar `app/static/js/busqueda_disano.js` con nuevos filtros
- [ ] Actualizar `app/static/js/buscar_productos.js` si lo usa
- [ ] Testear endpoints V2 localmente (curl o fetch)
- [ ] Validar que BC3 Suite App muestra campos BC3 Suite
- [ ] Verificar que filtros de marca/familia funcionan
- [ ] Commit y push de cambios a BC3 Suite repo

## 📚 REFERENCIAS

- **API DISANO V2:** <http://localhost:8000> (dev) / <https://api-disano-production.com> (prod)
- **BC3 Suite Project:** /Users/eloymartinezcuesta/Documents/BC3-Suite
- **BC3 Suite Patterns:** /Users/eloymartinezcuesta/Documents/BC3-Suite/docs/PATTERNS.md
- **Fase 2 Docs:** /Users/eloymartinezcuesta/Documents/API-DISANO-main/docs/MIGRATION_PLAN.md

## 🎯 PRÓXIMOS PASOS

1. **Copy este doc** a carpeta BC3 Suite: `docs/API_DISANO_V2_MIGRATION.md`
2. **Migrar archivos** según guía paso a paso
3. **Testear** con endpoints V2 locales
4. **Validar** que BC3 Suite App funciona correctamente
5. **Deploy** actualización BC3 Suite App

---

**Generado:** 2026-07-10  
**Estado:** API DISANO V2 validado ✅  
**BC3 Suite App:** Pendiente migración por usuario
