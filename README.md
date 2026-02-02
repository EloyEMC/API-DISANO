# API DISANO

API REST para consultar productos y tarifas de Disano (8,288 productos).

## 🌐 Producción

**URL**: https://api.eloymartinezcuesta.com

**Estado**: ✅ Activa con seguridad

Ver [README_PRODUCTION.md](README_PRODUCTION.md) para información completa de producción, credenciales y uso.

---

## 🚀 Inicio Rápido

### Instalación Local

```bash
# Clonar repositorio
git clone https://github.com/EloyEMC/API-DISANO.git
cd API-DISANO

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### Configuración

```bash
# Copiar archivo de entorno
cp .env.example .env

# Editar configuración
nano .env
```

### Ejecutar

```bash
# Modo desarrollo
uvicorn app.main:app --reload

# Modo producción (con seguridad)
# Editar .env: ENVIRONMENT=production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 📡 Endpoints

### Públicos (desarrollo)

```bash
GET /health          - Health check
GET /docs            - Documentación interactiva (Swagger UI)
GET /redoc           - Documentación alternativa (ReDoc)
```

### Protegidos (producción)

Requieren API Key via header `X-API-Key`.

```bash
GET /api/productos/          - Listado de productos
GET /api/productos/{codigo}  - Detalle de producto
GET /api/familias/           - Listado de familias
GET /api/bc3/                - Datos para generar BC3
```

---

## 🔒 Seguridad

### Capas de Seguridad Activas en Producción

| Capa | Descripción |
|------|-------------|
| **API Key Authentication** | Requiere header `X-API-Key` válido |
| **Rate Limiting** | 30 peticiones/minuto por cliente |
| **User-Agent Filtering** | Bloquea scrapers (curl, python-requests, etc.) |
| **Security Headers** | HSTS, X-Frame-Options, X-Content-Type-Options |
| **CORS Restringido** | Solo dominios autorizados |
| **Documentación Oculta** | `/docs` y `/redoc` retornan 404 |

### Desarrollo vs Producción

- **Desarrollo** (`ENVIRONMENT=development`):
  - Sin autenticación
  - Documentación pública
  - CORS permitido para todos los orígenes

- **Producción** (`ENVIRONMENT=production`):
  - API Key requerida
  - Documentación oculta
  - CORS restringido

---

## 📁 Estructura del Proyecto

```
API-DISANO/
├── app/
│   ├── main.py              # Aplicación FastAPI
│   ├── security.py          # Módulos de seguridad
│   ├── config.py            # Configuración (pydantic-settings)
│   └── routers/             # Endpoints
│       ├── productos.py     # Gestión de productos
│       ├── familias.py      # Gestión de familias
│       └── bc3.py           # Datos para BC3
├── database/
│   └── tarifa_disano.db     # SQLite (8,288 productos)
├── scripts/
│   ├── setup-production.sh  # Configuración de producción
│   └── verify-deployment.sh  # Verificación de estado
└── tests/                   # Tests (pendiente)
```

---

## 🛠️ Scripts Disponibles

### setup-production.sh
Configura el entorno de producción y genera API key segura.

```bash
bash scripts/setup-production.sh
```

### verify-deployment.sh
Verifica el estado del despliegue (auto-reinicio, auto-inicio).

```bash
bash scripts/verify-deployment.sh
```

---

## 📚 Documentación

- [README_PRODUCTION.md](README_PRODUCTION.md) - Guía completa de producción
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Guía técnica de despliegue
- [SECURITY_DEPLOYMENT.md](SECURITY_DEPLOYMENT.md) - Guía de seguridad
- [VERIFICACION_SERVICIO.md](VERIFICACION_SERVICIO.md) - Verificación de auto-reinicio

---

## 🧪 Ejemplos de Uso

### curl

```bash
# Health check
curl https://api.eloymartinezcuesta.com/health

# Productos (requiere API Key en producción)
curl -H "X-API-Key: TU_API_KEY" \
     -H "User-Agent: Mozilla/5.0" \
     https://api.eloymartinezcuesta.com/api/productos/?limit=10
```

### Python

```python
import requests

API_URL = "https://api.eloymartinezcuesta.com"
API_KEY = "tu-api-key-aqui"

headers = {
    "X-API-Key": API_KEY,
    "User-Agent": "Mozilla/5.0"
}

# Obtener productos
response = requests.get(f"{API_URL}/api/productos/?limit=10", headers=headers)
productos = response.json()

# Buscar por código
codigo = "11253300"
response = requests.get(f"{API_URL}/api/productos/{codigo}", headers=headers)
producto = response.json()
```

---

## 🔧 Configuración

### Variables de Entorno

```bash
# Entorno
ENVIRONMENT=production              # development | production

# API
API_HOST=127.0.0.1
API_PORT=8000

# Seguridad
API_KEYS=tu-api-key-generada-aqui
RATE_LIMIT_PER_MINUTE=30

# CORS (producción)
CORS_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com

# Base de datos
DATABASE_PATH=database/tarifa_disano.db
```

---

## 📦 Deployment

Ver [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) para instrucciones completas de despliegue.

### Resumen Rápido

1. Clonar repositorio
2. Crear entorno virtual e instalar dependencias
3. Configurar variables de entorno
4. Configurar Nginx
5. Configurar SSL (Let's Encrypt)
6. Crear servicio systemd
7. Iniciar servicio

---

## 🧪 Tests

```bash
# Ejecutar tests (pendiente de implementar)
pytest

# Con coverage
pytest --cov=app tests/
```

---

## 📄 Licencia

Este proyecto es privado y confidencial. Todos los derechos reservados.

---

## 👤 Autor

Eloy Martínez Cuesta

**Última actualización**: 2 de febrero de 2026
