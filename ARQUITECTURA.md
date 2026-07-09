# 🏗️ ARQUITECTURA FINAL - API DISANO

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CAPAS DE SEGURIDAD                             │
└─────────────────────────────────────────────────────────────────────────────┘

CLIENTE (App Flask / Frontend Astro / Móvil)
    ↓
    Header: X-API-Key: KlawgIxZIDTWbqaqSW2P-9miD-RwnW2HD7fMdjBtdlE
    User-Agent: Mozilla/5.0 (compatible; MyApp/1.0)
    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  0. NGINX (Producción)                                                     │
│     ├─ SSL/TLS (Let's Encrypt)                                            │
│     ├─ Rate Limit: 10 req/s                                               │
│     ├─ User-Agent Block                                                   │
│     └─ Headers: HSTS, X-Frame-Options, etc.                              │
└─────────────────────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. FASTAPI - SecurityMiddleware (main.py)                                │
│     ├─► User-Agent Filter     → Bloquea curl, python-requests, wget       │
│     ├─► Honeypot Detection    → /api/sitemap.xml → Ban permanente          │
│     ├─► Scraping Detector     → Patrones sospechosos (timing, sequential) │
│     └─► Request Logging       → logs/api.log + logs/security.log          │
└─────────────────────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  2. ENDPOINT DEPENDENCY - verify_api_key (api_key.py)                     │
│     ├─► Lee header X-API-Key                                              │
│     ├─► Si no existe → 401 Unauthorized                                   │
│     ├─► Si inválida → 401 Unauthorized                                    │
│     └─► Si válida → Continúa                                              │
└─────────────────────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  3. RATE LIMITING - slowapi (rate_limiter.py)                             │
│     ├─► Cuenta por API Key (no por IP)                                    │
│     ├─► 30 peticiones / minuto                                            │
│     ├─► 10 peticiones / 10 segundos (burst)                               │
│     └─► Si excede → 429 Too Many Requests                                 │
└─────────────────────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  4. BUSINESS LOGIC - Routers (productos.py, familias.py, bc3.py)          │
│     ├─► Validar parámetros (limit ≤ 100)                                  │
│     ├─► Consultar SQLite                                                  │
│     ├─► Aplicar filtros                                                   │
│     ├─► Paginar resultados                                                │
│     └─► Retornar JSON                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
    ↓
RESPUESTA HTTP 200 OK
    {
      "productos": [...],
      "total": 8288,
      "X-Process-Time": "0.123s",
      "X-Request-ID": "140123456789"
    }
```

---

## 📊 MAPA DE ARCHIVOS

```
/Volumes/WEBS/API_DISANO/
│
├── 📄 app/main.py                          ⚡ Punto de entrada
│    ├─ Imports de seguridad
│    ├─ SecurityMiddleware class
│    ├─ FastAPI app config (docs deshabilitados)
│    ├─ Router includes con dependencies
│    └─ Event handlers (startup/shutdown)
│
├── ⚙️ app/config.py                       📋 Configuración
│    ├─ Settings class (pydantic-settings)
│    ├─ Variables de entorno
│    └─ Validación automática
│
├── 🔒 app/security/                       Módulo de seguridad
│    │
│    ├── api_key.py                        🔑 Autenticación
│    │   └─ verify_api_key() dependency
│    │
│    ├── rate_limiter.py                   ⏱️ Rate Limiting
│    │   ├─ limiter instance
│    │   ├─ get_api_key_identifier()
│    │   └─ rate_limit_exceeded_handler()
│    │
│    ├── user_agent_filter.py              🤖 UA Filter
│    │   ├─ is_user_agent_allowed()
│    │   └─ get_user_agent_info()
│    │
│    ├── scraping_detector.py              🔍 Scraping Detection
│    │   ├─ ScrapingDetector class
│    │   ├─ analyze_request()
│    │   ├─ is_suspicious_request()
│    │   └─ is_honeypot_access()
│    │
│    └── logging_config.py                 📊 Logging
│        ├─ setup_logging()
│        ├─ logger instance
│        └─ Log handlers (console + file)
│
├── 🛣️ app/routers/                       Endpoints
│    ├── productos.py                      /v1/internal/products
│    ├── familias.py                       /v1/internal/families
│    └── bc3.py                            /v1/internal/bc3
│
├── 💾 database/tarifa_disano.db           SQLite (8,288 productos)
│
├── 📝 logs/                               Logs
│    ├── api.log                           Todos los accesos
│    └── security.log                      Eventos de seguridad
│
├── 🛠️ scripts/                            Scripts
│    ├── setup.sh                          Configuración inicial
│    └── verify_security.sh                Verificación
│
├── 🔐 .env                                Variables (NO en git)
├── 📋 .env.example                        Plantilla
├── 📦 requirements.txt                    Dependencias
└── 📖 SECURITY_README.md                  Guía de uso
```

---

## 🔄 FLUJO DE DATOS

```
┌──────────────────┐
│  Flask App       │
│  (pdf-to-bc3)    │
└────────┬─────────┘
         │
         │ requests.get()
         │ headers={"X-API-Key": "..."}
         ↓
┌─────────────────────────────────────────────────────────────┐
│  API DISANO (FastAPI)                                       │
│                                                             │
│  1. SecurityMiddleware                                      │
│     ├─ User-Agent OK? ✓                                    │
│     ├─ Honeypot? No ✓                                      │
│     └─ Scraping? No ✓                                      │
│                                                             │
│  2. verify_api_key                                         │
│     └─ API Key válida? ✓                                   │
│                                                             │
│  3. rate_limiter                                           │
│     └─ < 30/min? ✓                                        │
│                                                             │
│  4. productos.py router                                     │
│     ├─ GET /v1/internal/products                           │
│     ├─ Query params: limit=100                             │
│     ├─ SQLite: SELECT * FROM productos LIMIT 100           │
│     └─ Return JSON                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │
         │ Response 200 + JSON
         ↓
┌──────────────────┐
│  Flask App       │
│  Recibe datos    │
│  Genera BC3      │
└──────────────────┘
```

---

## 🛡️ MATRIZ DE PROTECCIÓN

| Amenaza | Protección | Archivo |
|---------|-----------|---------|
| Acceso sin autorización | API Key required | `api_key.py` |
| Scraping básico (curl) | User-Agent filter | `user_agent_filter.py` |
| Scraping (python) | User-Agent filter | `user_agent_filter.py` |
| Scraping masivo | Rate limiting (30/min) | `rate_limiter.py` |
| Scraping inteligente | Scraping detector | `scraping_detector.py` |
| Descubrimiento automático | /docs deshabilitado | `main.py` |
| Fuzzing de endpoints | Prefijos personalizados | `main.py` |
| Indexación en Google | robots.txt | `main.py` |
| DoS | Rate limiting global | `rate_limiter.py` |
| Abuso de API | Ban automático | `scraping_detector.py` |

---

## 📈 MÉTRICAS DE SEGURIDAD

### Tiempo para descargar 8,288 productos

| Método | Sin protección | Con protección |
|--------|---------------|----------------|
| Paginación 100 | 8 segundos | 3 minutos |
| Paginación 10 | 83 segundos | 28 minutos |

**Conclusión:** Scraping es **22x más lento** con protección.

### Dificultad de descubrimiento

| Aspecto | Sin protección | Con protección |
|---------|---------------|----------------|
| Encontrar docs | Visitar `/docs` | ❌ No existe |
| Enumerar endpoints | `/openapi.json` | ❌ No existe |
| Identificar stack | Headers delatan FastAPI | `Server: Web Server` |
| Fuzzing `/api/*` | Fácil, estándar | 🔒 Prefijo `/v1/internal/*` |

---

## 🎯 PRÓXIMOS PASOS

### Inmediato (Hoy)

1. **Ejecutar setup**
   ```bash
   cd /Volumes/WEBS/API_DISANO
   bash scripts/setup.sh
   ```

2. **Iniciar servidor**
   ```bash
   source venv/bin/activate
   python -m uvicorn app.main:app --reload
   ```

3. **Verificar seguridad**
   ```bash
   export API_URL='http://127.0.0.1:8000'
   export API_KEY='KlawgIxZIDTWbqaqSW2P-9miD-RwnW2HD7fMdjBtdlE'
   bash scripts/verify_security.sh
   ```

### Corto Plazo (Esta semana)

4. **Push a GitHub**
   - Revisar `.gitignore`
   - Commit con mensaje claro
   - Push a `https://github.com/EloyEMC/API-DISANO.git`

5. **Desplegar en Hetzner**
   - Configurar VPS
   - Instalar dependencias
   - Configurar Nginx + HTTPS
   - Crear servicio systemd

### Medio Plazo (Próximas 2 semanas)

6. **Integrar con app Flask**
   - Añadir API key a variables de entorno
   - Actualizar endpoints (`/api/*` → `/v1/internal/*`)
   - Implementar reintentos con exponential backoff

7. **Crear frontend Astro**
   - Catálogo de productos
   - Búsqueda y filtros
   - Añadir al presupuesto

---

## 📞 REFERENCIAS RÁPIDAS

### Comandos útiles

```bash
# Ver logs en tiempo real
tail -f logs/api.log
tail -f logs/security.log

# Ver IPs baneadas
# (Revisar security.log y buscar "IP baneada")

# Generar nueva API key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Verificar sintaxis
python -m py_compile app/main.py

# Test rápido de API key
curl -H "X-API-Key: tu-key" http://localhost:8000/health
```

### Archivos clave

- Configuración: `app/config.py`
- Seguridad: `app/security/`
- Endpoints: `app/main.py` (routers)
- Logs: `logs/api.log`, `logs/security.log`
- Tests: `scripts/verify_security.sh`
- Setup: `scripts/setup.sh`

### Variables de entorno críticas

```bash
API_KEYS=tu-api-key-aqui                    # 🔑 OBLIGATORIO
CORS_ORIGINS=https://tu-dominio.com        # 🌐 Producción
ENVIRONMENT=production                      # ⚙️ Producción
RATE_LIMIT_PER_CLIENT=30                    # ⏱️ Ajustar si necesario
LOG_LEVEL=INFO                              # 📊 DEBUG para desarrollo
```
