# API Disano

API REST para consultar productos y tarifas de Disano con FastAPI y SQLite.

## 🚀 Características

- **FastAPI** - Framework moderno y rápido para APIs
- **SQLite** - Base de datos ligera con 8,288 productos
- **Documentación automática** - Swagger UI y ReDoc
- **Filtros avanzados** - Por marca, familia, búsqueda de texto
- **Descripciones BC3** - 5,286 productos con descripciones técnicas
- **CORS habilitado** - Para fácil integración frontend

## 📋 Requisitos

- Python 3.11+
- pip

## 🔧 Instalación

```bash
# Clonar o navegar al proyecto
cd /Volumes/WEBS/API_DISANO

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # macOS/Linux

# Instalar dependencias
pip install -r requirements.txt
```

## ▶️ Ejecutar

```bash
# Modo desarrollo con autoreload
python app/main.py

# O con uvicorn directamente
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

La API estará disponible en:
- **API**: http://localhost:8000
- **Documentación Swagger**: http://localhost:8000/docs
- **Documentación ReDoc**: http://localhost:8000/redoc

## 📁 Estructura del Proyecto

```
API_DISANO/
├── app/
│   ├── __init__.py
│   ├── main.py              # Aplicación FastAPI
│   ├── database.py          # Conexión SQLite
│   ├── models.py            # Modelos Pydantic
│   └── routers/             # Endpoints
│       ├── __init__.py
│       ├── productos.py     # Endpoint productos
│       ├── familias.py      # Endpoint familias
│       └── bc3.py           # Endpoint BC3
├── database/
│   └── tarifa_disano.db     # Base de datos SQLite (23MB)
├── tests/
├── docs/
├── requirements.txt
└── README.md
```

## 📊 Endpoints

### Productos (`/api/productos`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Lista de productos con filtros |
| GET | `/{codigo}` | Obtener producto por código |
| GET | `/marca/{marca}` | Productos por marca |
| GET | `/familia/{familia}` | Productos por familia |

**Filtros disponibles:**
- `skip`: Número de registros a saltar (paginación)
- `limit`: Número máximo de registros (1-500)
- `marca`: Filtrar por marca
- `familia_web`: Filtrar por familia
- `buscar`: Buscar en descripción
- `con_bc3`: Solo productos con BC3
- `con_imagen`: Solo productos con imagen

### Familias (`/api/familias`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Lista de todas las familias |
| GET | `/stats` | Estadísticas de todas las familias |
| GET | `/{familia}` | Detalles de una familia |

### BC3 (`/api/bc3`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Estadísticas generales BC3 |
| GET | `/columnas` | Productos tipo Columna |
| GET | `/articulaciones` | Productos tipo Articulación |
| GET | `/tipo/{tipo}` | Productos por tipo BC3 |
| GET | `/{codigo}` | Descripción BC3 de un producto |

## 📖 Ejemplos de Uso

### Obtener todos los productos
```bash
curl http://localhost:8000/api/productos
```

### Buscar producto por código
```bash
curl http://localhost:8000/api/productos/33036139
```

### Filtrar por marca con paginación
```bash
curl "http://localhost:8000/api/productos?marca=Disano&skip=0&limit=50"
```

### Buscar en descripciones
```bash
curl "http://localhost:8000/api/productos?buscar=led"
```

### Solo productos con BC3
```bash
curl "http://localhost:8000/api/productos?con_bc3=true"
```

### Obtener columnas
```bash
curl http://localhost:8000/api/bc3/columnas
```

### Estadísticas de familias
```bash
curl http://localhost:8000/api/familias/stats
```

## 📊 Base de Datos

- **Total productos**: 8,288
- **Con BC3**: 5,286 (63.8%)
- **Con imagen**: 7,758 (93.6%)
- **Tamaño**: 23 MB

## 🔒 Variables de Entorno (Opcional)

Crear `.env`:
```
DATABASE_PATH=database/tarifa_disano.db
API_HOST=0.0.0.0
API_PORT=8000
```

## 🧪 Testing

```bash
# Ejecutar tests
pytest

# Con cobertura
pytest --cov=app
```

## 📝 Próximos Pasos

- [ ] Añadir autenticación API Key
- [ ] Implementar caché con Redis
- [ ] Endpoints de búsqueda avanzada
- [ ] Exportación a CSV/Excel
- [ ] WebSocket para actualizaciones en tiempo real
- [ ] Dockerfile para contenedorización

## 📄 Licencia

Uso interno para gestión de productos Disano.
