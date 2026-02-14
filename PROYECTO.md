# 🎯 CONTEXTO DEL PROYECTO PARA IA

**Este archivo es el PUNTO DE PARTIDA para trabajar con este proyecto.**
Contiene solo la información esencial que necesitas saber antes de modificar cualquier cosa.

---

## 📋 QUÉ ES ESTE PROYECTO

API REST FastAPI para gestionar un catálogo eléctrico de productos DISANO/FOSNOVA con autenticación por API keys y funcionalidades BC3.

**Stack técnico:**
- Python 3.10+
- FastAPI (framework web)
- Pydantic (validación de datos)
- SQLite (base de datos)
- Uvicorn (ASGI server)
- Nginx (reverse proxy)

**Propósito:**
- Exponer catálogo de productos eléctricos
- Permitir creación de presupuestos
- Generar archivos BC3 (FIEBDC-3)
- Integración con aplicación Flask externa (pdf-to-bc3-server)

---

## 🏗️ ESTRUCTURA CLAVE

```
API_DISANO/
├── app/                    # Código principal de la aplicación
│   ├── config.py           # ⚠️ LEER PRIMERO: Configuración centralizada
│   ├── models.py           # Modelos Pydantic (datos)
│   ├── database.py         # Conexión SQLite
│   ├── security.py          # Middlewares (legacy - usar app/security/)
│   ├── main.py              # Punto de entrada
│   ├── routers/            # Endpoints API
│   │   ├── productos.py    # CRUD productos + BC3
│   │   ├── familias.py     # Consultas familias
│   │   └── bc3.py          # Endpoints BC3
│   └── security/           # ⚠️ SISTEMA DE SEGURIDAD COMPLETO
│       ├── api_key.py       # Verificación de API keys
│       ├── rate_limiter.py  # Rate limiting con slowapi
│       └── user_agent_filter.py # Anti-scraping
├── database/               # Base de datos SQLite
│   └── tarifa_disano.db   # 📦 BD con 38 campos por producto
├── scripts/               # Scripts de despliegue
├── .env                  # 🔐 Variables de entorno (VER ARCHIVO ABAJO)
└── requirements.txt        # Dependencias Python
```

---

## 🔑 VARIABLES DE ENTORNO

**Archivo de referencia:** `.env.example`

**Variables críticas:**
- `ENVIRONMENT` - `development` | `production`
- `API_KEYS` - Keys para acceso normal (separadas por coma)
- `ADMIN_API_KEYS` - Keys para acceso admin (CRUD productos)

**Ver listado completo:** `VARIABLES_ENTORNO.md`

---

## 🔒 SISTEMA DE SEGURIDAD

**1. Autenticación:**
- Header `X-API-Key` requerido
- Dos niveles: normal (consultas) y admin (escritura)

**2. Rate Limiting:**
- Por cliente: 30 requests/minuto
- Global: 1000 requests/minuto
- Burst: 10 requests

**3. Anti-Scraping:**
- Detector de patrones de scraping
- Bloqueo por User-Agent sospechoso

**4. CORS:**
- Orígenes configurables por `CORS_ORIGINS`

**Documentación detallada:** `app/security/GUIA_SEGURIDAD.md`

---

## 📊 MODELO DE DATOS (Pydantic)

**Archivo:** `app/models.py`

**Modelos principales:**
- `ProductoBase` - Campos básicos del producto
- `Producto` - Producto con campos BC3
- `ProductoCreate` - Para crear nuevos productos (admin)
- `ProductoUpdate` - Para actualizar existentes (admin)

**Campos recientes (Feb 2026):**
- `raee_a` - RAEE Aparato
- `raee_l` - RAEE Lámpara
- `descripcion_corta` - Descripción corta del producto

---

## 🛣️ ENDPOINTS PRINCIPALES

**Base URL:** `/api/`

| Endpoint | Método | Auth | Descripción |
|----------|--------|------|-------------|
| `/productos/` | GET | API Key | Listar productos (filtros: limit, marca, familia, buscar) |
| `/productos/{codigo}` | GET | API Key | Obtener un producto |
| `/admin/productos` | POST | Admin Key | Crear producto |
| `/admin/productos/{codigo}` | PUT | Admin Key | Actualizar producto |
| `/admin/productos/{codigo}` | DELETE | Admin Key | Eliminar producto |
| `/familias/` | GET | API Key | Listar familias |
| `/bc3/descripcion/{codigo}` | GET | API Key | Obtener descripción BC3 |

**Documentación de rutas:** `app/routers/GUIA_ENDPOINTS.md`

---

## 🔄 FLUJO DE TRABAJO TÍPICO

**1. Desarrollar localmente:**
```bash
cd /Volumes/WEBS/API_DISANO
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**2. Modificar código:**
- Editar archivos en `app/`
- Los cambios se recargan automáticamente (--reload)

**3. Probar:**
```bash
# Sin auth (401)
curl http://localhost:8000/api/productos/

# Con auth
curl -H "X-API-Key: tu-key" http://localhost:8000/api/productos/
```

**4. Subir a producción:**
```bash
git add .
git commit -m "descripción"
git push origin main
```

**5. Actualizar servidor (VPS Hetzner):**
```bash
ssh root@46.62.227.64  # pwd: icXvsgbi4ded
cd /var/www/API-DISANO
git pull
systemctl restart api-disano
```

**Documentación VPS:** `ACCESO_VPS.md`

---

## ⚠️ REGLAS DE ORO PARA MODIFICAR CÓDIGO

### ✅ HACER:
1. **Usar `app/config.py`** para leer configuración
   - `from app.config import get_settings`
   - `settings = get_settings()`
   - NUNCA hardcodear valores

2. **Validación con Pydantic:**
   - Usar los modelos de `app/models.py`
   - No validar manualmente

3. **Manejo de errores:**
   - Usar excepciones personalizadas de `app/security/`
   - Retornar `AdminResponse` para endpoints admin

4. **Base de datos:**
   - Usar `app.database.get_db_connection()`
   - Cerrar conexiones (context manager)

### ❌ NO HACER:
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

---

## 📁 ARCHIVOS DE REFERENCIA

**Cuando trabajes con una parte específica:**

- **Configuración/Variables:** → `VARIABLES_ENTORNO.md`
- **Desarrollo en app/:** → `app/GUIA_DESARROLLO.md`
- **Crear/Modificar endpoints:** → `app/routers/GUIA_ENDPOINTS.md`
- **Sistema de seguridad:** → `app/security/GUIA_SEGURIDAD.md`
- **Despliegue en producción:** → `ACCESO_VPS.md`
- **Base de datos:** → `database/README.md`

---

## 🐛 PROBLEMAS COMUNES Y SOLUCIONES

| Problema | Solución |
|----------|----------|
| Error 401 | Falta header `X-API-Key` |
| Error 429 | Rate limit excedido |
| 502 Bad Gateway | API no está corriendo |
| `NameError: name 'RATE_LIMIT'` | Bug en security.py línea 139 (usar `rate_limit`) |
| Campos faltantes en API | Actualizar `models.py` y reiniciar servicio |

---

## 📌 COMMIT CONVENCIONES

```
feat: nueva funcionalidad
fix: corrección de bug
docs: documentación
refactor: reestructuración (sin cambios funcionales)
style: formato/código limpio
```

---

**Última actualización:** 14 Feb 2026
**Estado:** Producción activa en https://api.eloymartinezcuesta.com
**Commit actual:** 2e4af44
