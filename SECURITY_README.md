# API DISANO - Guía de Instalación y Uso

## 🚀 Instalación Rápida

### 1. Instalar dependencias

```bash
# Crear virtual environment
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env y generar API Keys
# Generar API key con:
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Configurar en .env:
# API_KEYS=${API_KEY}
# ENVIRONMENT=development  # Cambiar a production en despliegue
# CORS_ORIGINS=http://localhost:3000  # Tu frontend
```

### 3. Ejecutar en desarrollo

```bash
# Modo desarrollo
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📡 Nuevos Endpoints (con prefijos personalizados)

La API ahora usa prefijos personalizados para dificultar descubrimiento:

| Antiguo endpoint | Nuevo endpoint (seguro) |
|------------------|-------------------------|
| `/api/productos` | `/v1/internal/products` |
| `/api/familias` | `/v1/internal/families` |
| `/api/bc3` | `/v1/internal/bc3` |

## 🔐 Autenticación

Todos los endpoints requieren API Key en el header `X-API-Key`:

```bash
# Sin API key (fallará con 401)
curl http://localhost:8000/v1/internal/products/

# Con API key válida
curl -H "X-API-Key: ${API_KEY}" \
  http://localhost:8000/v1/internal/products/
```

## ✅ Verificar Seguridad

```bash
# Configurar variables
export API_URL='http://localhost:8000'
export API_KEY="${API_KEY:?Set API_KEY in your environment}"

# Ejecutar script de verificación
bash scripts/verify_security.sh
```

El script verificará:

- ✅ Documentación oculta (/docs, /openapi.json → 404)
- ✅ Autenticación requerida (401 sin API key)
- ✅ Rate limiting funcionando (429 después de N peticiones)
- ✅ User-Agent filtering activo
- ✅ Robots.txt bloqueando indexación

## 📊 Logs

Los logs se guardan en `logs/`:

- `logs/api.log` - Todos los accesos y eventos
- `logs/security.log` - Solo eventos de seguridad (WARNING+)

```bash
# Ver logs en tiempo real
tail -f logs/api.log
tail -f logs/security.log
```

## 🚀 Despliegue en Producción

### 1. Configurar para producción

```bash
# Editar .env
ENVIRONMENT=production
CORS_ORIGINS=https://tu-dominio.com
HTTPS_ENABLED=true
```

### 2. Configurar Nginx

Ver `docs/nginx_config.md` para configuración completa de Nginx con HTTPS, HSTS, y headers de seguridad.

### 3. Crear servicio systemd

```bash
# /etc/systemd/system/api-disano.service
[Unit]
Description=API Disano
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/var/www/api-disano
Environment="PATH=/var/www/api-disano/venv/bin"
EnvironmentFile=/var/www/api-disano/.env
ExecStart=/var/www/api-disano/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### 4. Iniciar servicio

```bash
sudo systemctl daemon-reload
sudo systemctl enable api-disano
sudo systemctl start api-disano
sudo systemctl status api-disano
```

## 🔧 Solución de Problemas

### Error: No module named 'loguru'

```bash
# Activar venv e instalar dependencias
source venv/bin/activate
pip install -r requirements.txt
```

### Error: 401 Unauthorized

- Verificar que `.env` existe y tiene `API_KEYS` configurado
- Verificar que envías header `X-API-Key`

### Error: 429 Too Many Requests

- Has excedido el rate limit. Espera 60 segundos o ajusta `RATE_LIMIT_PER_CLIENT` en `.env`

### Error: 403 Forbidden

- User-Agent bloqueado. Tu cliente debe enviar un User-Agent legítimo de navegador

## 📚 Estructura del Proyecto

```
/Volumes/WEBS/API_DISANO/
├── app/
│   ├── main.py                 # Punto de entrada con seguridad integrada
│   ├── config.py               # Configuración centralizada
│   ├── database.py             # Conexión a BD
│   ├── models.py               # Modelos Pydantic
│   ├── security/               # 🆕 Módulo de seguridad
│   │   ├── api_key.py          # Validación API Keys
│   │   ├── rate_limiter.py     # Rate limiting
│   │   ├── user_agent_filter.py # Filtro UA
│   │   ├── scraping_detector.py # Detección scraping
│   │   └── logging_config.py   # Sistema de logs
│   └── routers/
│       ├── productos.py
│       ├── familias.py
│       └── bc3.py
├── logs/                       # 🆕 Directorio de logs
├── scripts/
│   └── verify_security.sh      # 🆕 Script de verificación
├── .env                        # Variables de entorno (NO en git)
├── .env.example                # Plantilla de configuración
├── requirements.txt            # Dependencias actualizadas
└── README.md                   # Este archivo
```

## 🎯 Checklist Pre-Producción

- [ ] API key generada con `secrets.token_urlsafe(32)`
- [ ] `.env` creado y **NO** subido a git
- [ ] Documentación deshabilitada (`docs_url=None`)
- [ ] Prefijos personalizados activos
- [ ] Rate limiting configurado (30/min)
- [ ] CORS restringido a dominios específicos
- [ ] User-Agent filtering activado
- [ ] Logs de seguridad configurados
- [ ] Script de verificación ejecutado exitosamente
- [ ] Nginx configurado con HTTPS
- [ ] Firewall configurado (solo puertos 80, 443, 22)
- [ ] Backups automáticos configurados

## 🆘 Soporte

Si encuentras algún problema o tienes preguntas, revisa:

1. Los logs en `logs/api.log` y `logs/security.log`
2. El plan de seguridad en `docs/PLAN_SEGURIDAD.md`
3. Ejecuta `bash scripts/verify_security.sh` para diagnosticar
