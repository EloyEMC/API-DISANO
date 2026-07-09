# 🚀 API DISANO - GUÍA DE PRODUCCIÓN

## 📋 INFORMACIÓN GENERAL

**URL**: https://api.eloymartinezcuesta.com
**Servidor**: Hetzner VPS (46.62.227.64)
**Entorno**: Ubuntu 22.04.5 LTS
**Base de datos**: 8,288 productos SQLite

---

## 🔐 CREDENCIALES

### API Key Actual
```
yqZ2eOmHH8y08VesvL5zalSg8lq3b7NTpuitRtWe2bs
```

**Ubicación**: Guardada en variables de entorno del servicio systemd

### SSH Access
- **Usuario**: root
- **Host**: 46.62.227.64
- **Desde tu Mac**: `ssh root@46.62.227.64`

---

## 🔒 SEGURIDAD IMPLEMENTADA

### Capas de Seguridad

| Capa | Estado | Descripción |
|------|--------|-------------|
| **API Key Authentication** | ✅ Activo | Requiere header `X-API-Key` |
| **Rate Limiting** | ✅ Activo | 30 peticiones/minuto por cliente |
| **User-Agent Filtering** | ✅ Activo | Bloquea scrapers (curl, python-requests, etc.) |
| **Security Headers** | ✅ Activo | HSTS, X-Frame-Options, X-Content-Type-Options |
| **CORS Restringido** | ✅ Activo | Solo dominios autorizados |
| **Documentación Oculta** | ✅ Activo | `/docs`, `/redoc` retornan 404 en producción |

### Endpoints Públicos (sin autenticación)
```
GET /health        - Health check
```

### Endpoints Protegidos (requieren API Key)
```
GET /api/productos/        - Listado de productos
GET /api/productos/{id}    - Detalle de producto
GET /api/familias/         - Listado de familias
GET /api/bc3/              - Datos para BC3
```

---

## 📝 USO DE LA API

### Ejemplo con curl

```bash
curl -k \
  -H "X-API-Key: yqZ2eOmHH8y08VesvL5zalSg8lq3b7NTpuitRtWe2bs" \
  -H "User-Agent: Mozilla/5.0" \
  'https://api.eloymartinezcuesta.com/api/productos/?limit=10'
```

### Ejemplo con Python

```python
import requests

API_URL = "https://api.eloymartinezcuesta.com"
API_KEY = "yqZ2eOmHH8y08VesvL5zalSg8lq3b7NTpuitRtWe2bs"

headers = {
    "X-API-Key": API_KEY,
    "User-Agent": "Mozilla/5.0"
}

# Obtener productos
response = requests.get(f"{API_URL}/api/productos/?limit=10", headers=headers)
productos = response.json()

# Buscar producto por código
codigo = "11253300"
response = requests.get(f"{API_URL}/api/productos/{codigo}", headers=headers)
producto = response.json()
```

---

## 🛠️ GESTIÓN DEL SERVIDOR

### Conexión SSH
```bash
ssh root@46.62.227.64
```

### Ver estado del servicio
```bash
systemctl status api-disano
```

### Reiniciar servicio
```bash
systemctl restart api-disano
```

### Ver logs
```bash
# Logs del servicio
journalctl -u api-disano -f

# Últimas 50 líneas
journalctl -u api-disano -n 50

# Logs de hoy
journalctl -u api-disano --since today
```

### Actualizar la API
```bash
ssh root@46.62.227.64
cd /var/www/API-DISANO
git pull origin main
systemctl restart api-disano
```

---

## 🔑 CAMBIAR API KEY

Para generar una nueva API key:

```bash
ssh root@46.62.227.64
cd /var/www/API-DISANO
source venv/bin/activate
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Luego edita el servicio systemd:

```bash
nano /etc/systemd/system/api-disano.service
```

Cambia la línea:
```
Environment=API_KEYS=yqZ2eOmHH8y08VesvL5zalSg8lq3b7NTpuitRtWe2bs
```

Por la nueva key, guarda (CTRL+O, Enter, CTRL+X) y reinicia:

```bash
systemctl daemon-reload
systemctl restart api-disano
```

---

## ⚠️ SOLUCIÓN DE PROBLEMAS

### Error: 401 Unauthorized

**Causa**: API key incorrecta o no enviada

**Solución**:
- Verifica que el header `X-API-Key` se está enviando
- Verifica que la API key sea correcta
- Verifica que el User-Agent no esté bloqueado

### Error: 403 Forbidden

**Causa**: User-Agent bloqueado

**Solución**: Usa un User-Agent de navegador real:
```
User-Agent: Mozilla/5.0
```

### Error: 429 Too Many Requests

**Causa**: Excediste el rate limit (30 req/min)

**Solución**: Espera 1 minuto o implementa caching en tu aplicación

### El servicio no inicia

**Verificar**:
```bash
# Ver logs
journalctl -u api-disano -n 50

# Verificar syntax
cd /var/www/API-DISANO
source venv/bin/activate
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

---

## 📁 ESTRUCTURA DEL PROYECTO

```
API-DISANO/
├── app/
│   ├── main.py              # Aplicación FastAPI principal
│   ├── security.py          # Módulos de seguridad
│   └── routers/             # Endpoints API
│       ├── productos.py
│       ├── familias.py
│       └── bc3.py
├── database/
│   └── tarifa_disano.db     # Base de datos SQLite (8,288 productos)
├── scripts/
│   ├── setup-production.sh  # Configuración inicial
│   └── verify-deployment.sh  # Verificación de estado
├── venv/                    # Entorno virtual Python
├── .env                     # Variables de entorno (local)
├── DEPLOYMENT_GUIDE.md      # Guía completa de despliegue
├── SECURITY_DEPLOYMENT.md   # Guía de seguridad
└── README_PRODUCTION.md     # Este archivo
```

---

## 🔧 CONFIGURACIÓN DEL SERVICIO

**Archivo**: `/etc/systemd/system/api-disano.service`

```ini
[Unit]
Description=API Disano
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/API-DISANO
Environment=PATH=/var/www/API-DISANO/venv/bin
Environment=ENVIRONMENT=production
Environment=API_KEYS=yqZ2eOmHH8y08VesvL5zalSg8lq3b7NTpuitRtWe2bs
Environment=RATE_LIMIT_PER_MINUTE=30
Environment=CORS_ORIGINS=https://eloymartinezcuesta.com,https://disano.eloymartinezcuesta.com
ExecStart=/var/www/API-DISANO/venv/bin/python3 /var/www/API-DISANO/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## 🌐 CONFIGURACIÓN NGINX

**Archivo**: `/etc/nginx/sites-available/api-disano`

```nginx
server {
    listen 80;
    server_name api.eloymartinezcuesta.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

Certificado SSL: Let's Encrypt (automático con certbot)

---

## 📊 MONITOREO

### Verificar funcionamiento
```bash
curl https://api.eloymartinezcuesta.com/health
```

### Verificar seguridad
```bash
# Sin API key (debe fallar)
curl https://api.eloymartinezcuesta.com/api/productos/

# Con API key (debe funcionar)
curl -H "X-API-Key: yqZ2eOmHH8y08VesvL5zalSg8lq3b7NTpuitRtWe2bs" \
     -H "User-Agent: Mozilla/5.0" \
     https://api.eloymartinezcuesta.com/api/productos/?limit=1
```

---

## 📚 DOCUMENTACIÓN ADICIONAL

- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Guía completa de despliegue
- [SECURITY_DEPLOYMENT.md](SECURITY_DEPLOYMENT.md) - Guía de seguridad
- [VERIFICACION_SERVICIO.md](VERIFICACION_SERVICIO.md) - Verificación de auto-reinicio

---

**Última actualización**: 2 de febrero de 2026
**Estado**: ✅ Producción con seguridad activa
