# 🔐 VARIABLES DE ENTORNO

**Archivo de referencia:** `.env.example`

## CÓMO USAR ESTA GUÍA

1. **Copiar** el archivo example:
   ```bash
   cp .env.example .env
   ```

2. **Editar** `.env` con tus valores
3. **NUNCA** commitear `.env` (está en .gitignore)

---

## VARIABLES PRINCIPALES

### `ENVIRONMENT`
**Valores:** `development` | `production`
**Por defecto:** `development`
**Descripción:** Modo de operación de la API
**Ejemplo:**
```bash
ENVIRONMENT=production
```

---

## CLAVES DE API

### `API_KEYS`
**Descripción:** Claves para acceso NORMAL (consultas)
**Formato:** Coma-separated
**Por defecto:** (vacío - rechaza todo)
**Ejemplo:**
```bash
API_KEYS=key1,key2,key3
```
**Uso en código:**
```python
from app.config import get_settings
settings = get_settings()
api_keys = settings.api_keys  # List[str]
```

### `ADMIN_API_KEYS`
**Descripción:** Claves para acceso ADMIN (CRUD productos)
**Formato:** Coma-separated
**Por defecto:** (vacío)
**Ejemplo:**
```bash
ADMIN_API_KEYS=admin_key_1,admin_key_2
```

---

## RATE LIMITING

### `RATE_LIMIT_PER_CLIENT`
**Descripción:** Máximo de requests por minuto por cliente
**Por defecto:** `30`
**Ejemplo:**
```bash
RATE_LIMIT_PER_CLIENT=30
```

### `RATE_LIMIT_GLOBAL`
**Descripción:** Máximo global de requests por minuto
**Por defecto:** `1000`
**Ejemplo:**
```bash
RATE_LIMIT_GLOBAL=1000
```

### `RATE_LIMIT_BURST`
**Descripción:** Requests adicionales permitidos en burst
**Por defecto:** `10`
**Ejemplo:**
```bash
RATE_LIMIT_BURST=10
```

---

## SEGURIDAD - CORS

### `CORS_ORIGINS`
**Descripción:** Orígenes permitidos para CORS
**Formato:** Coma-separated (URLs completas)
**Por defecto:** (vacío - permite todos)
**Ejemplo:**
```bash
CORS_ORIGINS=https://mi-sitio.com,https://otro-sitio.com
```

**En código:**
```python
from app.config import get_settings
settings = get_settings()
origins = settings.cors_origins  # List[str]
```

---

## LOGGING

### `LOG_LEVEL`
**Valores:** `DEBUG` | `INFO` | `WARNING` | `ERROR`
**Por defecto:** `INFO`
**Ejemplo:**
```bash
LOG_LEVEL=INFO
```

### `LOG_TO_FILE`
**Descripción:** Si guardar logs en archivo
**Valores:** `true` | `false`
**Por defecto:** `true`
**Ejemplo:**
```bash
LOG_TO_FILE=true
```

### `LOG_FILE`
**Descripción:** Ruta del archivo de log
**Por defecto:** `logs/api.log`
**Ejemplo:**
```bash
LOG_FILE=logs/api.log
```

---

## HTTPS/SSL

### `HTTPS_ENABLED`
**Descripción:** Habilitar redirección a HTTPS
**Valores:** `true` | `false`
**Por defecto:** `false` (en production usar `true`)
**Ejemplo:**
```bash
HTTPS_ENABLED=true
```

---

## BASE DE DATOS

### `DATABASE_PATH`
**Descripción:** Ruta al archivo SQLite
**Por defecto:** `database/tarifa_disano.db`
**Ejemplo:**
```bash
DATABASE_PATH=database/tarifa_disano.db
```

**Uso en código:**
```python
from app.database import DB_PATH
# DB_PATH se define automáticamente
```

---

## EJEMPLO COMPLETO DE .env

```bash
# Modo de operación
ENVIRONMENT=production

# Claves de API (separadas por coma)
API_KEYS=client_key_1,client_key_2,client_key_3
ADMIN_API_KEYS=admin_master_key_1,admin_master_key_2

# Rate limiting
RATE_LIMIT_PER_CLIENT=30
RATE_LIMIT_GLOBAL=1000
RATE_LIMIT_BURST=10

# CORS
CORS_ORIGINS=https://mi-sitio.com,https://app.mi-sitio.com

# Logging
LOG_LEVEL=INFO
LOG_TO_FILE=true
LOG_FILE=logs/api.log

# HTTPS (production)
HTTPS_ENABLED=true

# Base de datos
DATABASE_PATH=database/tarifa_disano.db
```

---

## CÓMO LEER VARIABLES EN CÓDIGO

### ✅ FORMA CORRECTA

```python
from app.config import get_settings

# Obtener instancia de settings
settings = get_settings()

# Usar variables
api_keys = settings.api_keys
log_level = settings.log_level
environment = settings.environment
```

### ❌ FORMAS INCORRECTAS

```python
# ❌ NO HACER ESTO
import os

api_key = os.getenv("API_KEYS")  # Mal: no usa pydantic-settings
api_key = os.environ["API_KEYS"]  # Mal: no validación
```

---

## TESTING CON DIFERENTES CONFIGURACIONES

### Desarrollo (sin rate limiting)
```bash
ENVIRONMENT=development
RATE_LIMIT_PER_CLIENT=999999
```

### Producción (seguro)
```bash
ENVIRONMENT=production
HTTPS_ENABLED=true
RATE_LIMIT_PER_CLIENT=30
LOG_LEVEL=WARNING
```

---

## VALIDACIÓN

Pydantic valida automáticamente:

- **Tipo:** (str, int, bool, List[str])
- **Valores por defecto:** si no está definido
- **Required vs Optional:** Field(...) vs Field(None)

Si falta una variable **required**, la API fallará al iniciar con error claro.

---

**Consultar también:** `PROYECTO.md` para contexto general
