# 📦 API DISANO

API REST FastAPI para catálogo eléctrico DISANO/FOSNOVA con autenticación y BC3.

---

## 🚀 QUICK START

```bash
# 1. Clonar
git clone https://github.com/EloyEMC/API-DISANO.git
cd API-DISANO

# 2. Entorno virtual
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configurar
cp .env.example .env
nano .env  # Editar API_KEYS

# 4. Ejecutar
uvicorn app.main:app --reload
```

📍 **URL local:** http://localhost:8000
📍 **API docs:** http://localhost:8000/docs

---

## 📖 GUÍAS DE DOCUMENTACIÓN

**Para trabajar eficientemente con este proyecto:**

| Archivo | Cuándo leerlo |
|---------|---------------|
| **PROYECTO.md** | 🎯 PUNTO DE PARTIDA - Contexto general para la IA |
| **VARIABLES_ENTORNO.md** | 🔐 Configurar variables de entorno |
| **app/GUIA_DESARROLLO.md** | 📝 Modificar código en `app/` |
| **app/routers/GUIA_ENDPOINTS.md** | 🛣️ Crear/modificar endpoints |
| **app/security/GUIA_SEGURIDAD.md** | 🔒 Sistema de seguridad |
| **ACCESO_VPS.md** | 🌐 Desplegar en servidor Hetzner |

---

## 🌐 PRODUCCIÓN

**URL:** https://api.eloymartinezcuesta.com

**Ejemplo de uso:**
```bash
curl -H "X-API-Key: tu-api-key" \
     https://api.eloymartinezcuesta.com/api/productos/?limit=5
```

**Documentación producción:** `README_PRODUCTION.md`

---

## 📡 ENDPOINTS PRINCIPALES

| Endpoint | Auth | Descripción |
|----------|------|-------------|
| `GET /health` | ❌ | Health check |
| `GET /api/productos/` | ✅ | Listar productos (filtros: limit, marca, familia, buscar) |
| `GET /api/productos/{codigo}` | ✅ | Obtener producto por código |
| `POST /api/admin/productos` | 🔒 | Crear producto (admin) |
| `PUT /api/admin/productos/{codigo}` | 🔒 | Actualizar producto (admin) |
| `GET /api/familias/` | ✅ | Listar familias |
| `GET /api/bc3/{codigo}` | ✅ | Datos BC3 |

**Leyenda:** ❌ Público | ✅ API Key | 🔒 Admin Key

---

## 🗄️ BASE DE DATOS

**Sistema:** SQLite
**Ubicación:** `database/tarifa_disano.db`
**Productos:** ~8,288
**Campos:** 38 por producto

**Campos importantes:**
- `CÓDIGO` - Código único del producto
- `DESCRIPCION` - Descripción completa
- `PVP_26_01_26` - Precio de venta
- `MARCA` - Disano o Fosnova
- `Familia_WEB` - Familia web
- `RAEE_A`, `RAEE_L` - Residuos RAEE
- `bc3_descripcion_corta` - Descripción BC3

---

## 🔒 SEGURIDAD

### Autenticación
- **Header:** `X-API-Key`
- **Dos niveles:** Normal (consultas) / Admin (CRUD)

### Rate Limiting
- **Por cliente:** 30 requests/min
- **Global:** 1000 requests/min
- **Burst:** 10 requests

### Protección anti-scraping
- Detección de patrones
- Filtrado de User-Agent
- Bloqueo automático

**Detalles:** `app/security/GUIA_SEGURIDAD.md`

---

## 🏗️ ARQUITECTURA

```
API_DISANO/
├── app/                    # Código principal
│   ├── config.py           # ⚠️ Configuración centralizada
│   ├── models.py           # Modelos Pydantic
│   ├── main.py              # Punto de entrada
│   ├── routers/            # Endpoints API
│   └── security/           # 🔒 Sistema de seguridad
├── database/               # SQLite
├── scripts/               # Despliegue
├── .env.example           # Variables de entorno
└── requirements.txt        # Dependencias
```

**Documentación estructura:** `PROYECTO.md`

---

## 🛠️ DESARROLLO

### Modificar código
```bash
# Ver guía completa
cat app/GUIA_DESARROLLO.md

# Ejemplo rápido
uvicorn app.main:app --reload
# Editar archivos en app/
# Los cambios se recargan automáticamente
```

### Añadir endpoint
```python
# app/routers/mis_endpoints.py
from fastapi import APIRouter
from app.security.api_key import get_api_key

router = APIRouter()

@router.get("/nuevo-endpoint")
async def mi_endpoint(api_key: str = Depends(get_api_key)):
    return {"mensaje": "ok"}
```

### Testing
```bash
# Sin auth (401)
curl http://localhost:8000/api/productos/

# Con auth
curl -H "X-API-Key: tu-key" http://localhost:8000/api/productos/

# Con filtros
curl -H "X-API-Key: tu-key" \
     "http://localhost:8000/api/productos/?limit=5&marca=Disano"
```

---

## 🚀 DESPLIEGUE

### Local
```bash
uvicorn app.main:app --reload
```

### Producción (Hetzner VPS)
```bash
# Ver guía completa
cat ACCESO_VPS.md

# Resumen rápido
ssh root@46.62.227.64
cd /var/www/API-DISANO
git pull
systemctl restart api-disano
```

**Detalles:** `ACCESO_VPS.md` y `DEPLOYMENT_GUIDE.md`

---

## 📝 REGLAS DE CONTRIBUTIÓN

### ✅ HACER
1. Usar `app/config.py` para configuración
2. Validar con Pydantic (`app/models.py`)
3. Usar `app/security/` para seguridad
4. Commitear cambios: `git commit -m "feat: descripción"`

### ❌ NO HACER
1. NO hardcodear configuración
2. NO usar `app/security.py` (legacy)
3. NO repetir lógica de validación
4. NO commitear `.env` (está en .gitignore)

---

## 🧪 TESTING

### pytest (pendiente)
```bash
pytest tests/
pytest --cov=app tests/
```

### curl
```bash
# Health
curl http://localhost:8000/health

# Productos
curl -H "X-API-Key: your-key" \
     http://localhost:8000/api/productos/?limit=1
```

---

## 📚 DOCUMENTACIÓN ADICIONAL

| Archivo | Contenido |
|---------|-----------|
| `README_PRODUCTION.md` | Guía de producción completa |
| `DEPLOYMENT_GUIDE.md` | Guía técnica de despliegue |
| `ARQUITECTURA.md` | Arquitectura detallada |
| `ACCESO_VPS.md` | Credenciales y acceso VPS |

---

## 📄 LICENCIA

**Todos los derechos reservados** - Proyecto privado y confidencial.

---

**Última actualización:** 14 Feb 2026
**Estado:** ✅ Activo en producción
**Versión:** 2.0
