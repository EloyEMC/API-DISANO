# 🚀 GUÍA DE DESPLIEGUE - API DISANO EN PRODUCCIÓN

## 📋 INFORMACIÓN DEL DESPLIEGUE

**Fecha**: 1 de febrero de 2026
**Servidor**: Hetzner VPS (46.62.227.64)
**Sistema**: Ubuntu 22.04.5 LTS
**Subdominio**: api.eloymartinezcuesta.com
**URL**: https://api.eloymartinezcuesta.com

---

## ✅ ESTADO ACTUAL

| Componente | Estado | Detalles |
|------------|--------|----------|
| **API FastAPI** | ✅ Funcionando | Puerto 8000 (localhost) |
| **Nginx** | ✅ Configurado | Proxy reverse a localhost:8000 |
| **SSL** | ✅ Instalado | Let's Encrypt para api.eloymartinezcuesta.com |
| **Systemd** | ✅ Activo | Servicio api-disano.service |
| **Base de datos** | ✅ Conectada | 8,288 productos en SQLite |

---

## 📁 ARCHIVOS Y RUTAS

### En el servidor (VPS)

| Archivo/Directorio | Ruta |
|--------------------|------|
| **Código de la API** | `/var/www/API-DISANO/` |
| **Entorno virtual** | `/var/www/API-DISANO/venv/` |
| **Base de datos** | `/var/www/API-DISANO/database/tarifa_disano.db` |
| **Configuración** | `/var/www/API-DISANO/.env` |
| **Logs** | `/var/www/API-DISANO/logs/` |
| **Servicio systemd** | `/etc/systemd/system/api-disano.service` |
| **Configuración Nginx** | `/etc/nginx/sites-available/api-disano` |
| **Certificado SSL** | `/etc/letsencrypt/live/api.eloymartinezcuesta.com/` |

### En local (Mac)

| Directorio | Ruta |
|------------|------|
| **Repositorio** | `/Volumes/WEBS/API_DISANO/` |
| **GitHub** | https://github.com/EloyEMC/API-DISANO |

---

## 🔧 CONFIGURACIÓN ACTUAL

### Servicio Systemd

**Archivo**: `/etc/systemd/system/api-disano.service`

```ini
[Unit]
Description=API Disano
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/API-DISANO
Environment="PATH=/var/www/API-DISANO/venv/bin"
EnvironmentFile=/var/www/API-DISANO/.env
ExecStart=/var/www/API-DISANO/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Características de reinicio**:
- ✅ `Restart=always` - Reinicia automáticamente si falla
- ✅ `RestartSec=10` - Espera 10 segundos antes de reiniciar
- ✅ `enabled` - Se inicia automáticamente al arrancar el servidor

### Configuración Nginx

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

**Nota**: Let's Encrypt ha añadido automáticamente la configuración HTTPS.

### Variables de Entorno (.env)

**Archivo**: `/var/www/API-DISANO/.env`

```bash
ENVIRONMENT=production
API_HOST=127.0.0.1
API_PORT=8000
```

---

## 🌐 ENDPOINTS DE LA API

### Endpoints públicos (actualmente sin autenticación)

```
GET /health                           - Health check
GET /                                 - Información de la API
GET /docs                            - Documentación interactiva (Swagger UI)
GET /redoc                           - Documentación alternativa (ReDoc)

GET /api/productos/                  - Listado de productos
GET /api/productos/{codigo}          - Detalle de un producto
GET /api/familias/                   - Listado de familias
GET /api/bc3/                        - Datos para BC3
```

### Ejemplos de uso

```bash
# Health check
curl https://api.eloymartinezcuesta.com/health

# Obtener primeros 5 productos
curl https://api.eloymartinezcuesta.com/api/productos/?limit=5

# Buscar producto por código
curl https://api.eloymartinezcuesta.com/api/productos/11253300

# Ver documentación interactiva
# Abrir en navegador: https://api.eloymartinezcuesta.com/docs
```

---

## 🔄 GESTIÓN DEL SERVICIO

### Ver estado del servicio

```bash
# Ver estado completo
systemctl status api-disano

# Ver si está habilitado para auto-inicio
systemctl is-enabled api-disano

# Ver si está corriendo
systemctl is-active api-disano
```

### Comandos de control

```bash
# Iniciar servicio
systemctl start api-disano

# Detener servicio
systemctl stop api-disano

# Reiniciar servicio
systemctl restart api-disano

# Recargar configuración
systemctl daemon-reload
```

### Ver logs

```bash
# Logs del servicio systemd
journalctl -u api-disano -f

# Últimas 50 líneas
journalctl -u api-disano -n 50

# Logs de hoy
journalctl -u api-disano --since today

# Logs con errores
journalctl -u api-disano -p err
```

---

## 🧪 PRUEBAS DE VERIFICACIÓN

### 1. Verificar que el servicio está activo

```bash
systemctl status api-disano
```

**Debe mostrar**:
- `Loaded: loaded` y `enabled`
- `Active: active (running)`
- Logs con "Application startup complete"

### 2. Verificar auto-reinicio

```bash
# Matar el proceso manualmente
kill -9 $(pidof uvicorn)

# Esperar 10 segundos
sleep 10

# Verificar que se reinició
systemctl status api-disano
```

**Debe mostrar**: El servicio sigue activo (systemd lo reinició automáticamente)

### 3. Verificar respuestas de la API

```bash
# Health check
curl https://api.eloymartinezcuesta.com/health

# Debe retornar: {"status":"ok","service":"api-disano"}

# Obtener productos
curl https://api.eloymartinezcuesta.com/api/productos/?limit=2

# Debe retornar un array con 2 productos
```

### 4. Verificar configuración Nginx

```bash
nginx -t
```

**Debe mostrar**: `syntax is ok` y `test is successful`

### 5. Verificar certificado SSL

```bash
certbot certificates
```

**Debe mostrar**: Un certificado válido para `api.eloymartinezcuesta.com`

---

## 📝 ACTUALIZAR LA API

Cuando haya cambios en el código:

### Opción 1: Actualizar desde GitHub

```bash
cd /var/www/API-DISANO
git pull origin main
systemctl restart api-disano
systemctl status api-disano
```

### Opción 2: Subir archivos manualmente

```bash
# Desde tu Mac
scp app/main.py root@46.62.227.64:/var/www/API-DISANO/app/

# En el servidor
systemctl restart api-disano
systemctl status api-disano
```

### Verificar actualización

```bash
# Ver logs después del reinicio
journalctl -u api-disano -n 50

# Probar la API
curl https://api.eloymartinezcuesta.com/health
```

---

## 🚨 SOLUCIÓN DE PROBLEMAS

### Error: 502 Bad Gateway

**Causa**: El servicio uvicorn no está corriendo

**Solución**:
```bash
# Verificar estado del servicio
systemctl status api-disano

# Si está stopped, iniciarlo
systemctl start api-disano

# Si falla al iniciar, ver logs
journalctl -u api-disano -n 50
```

### Error: 504 Gateway Timeout

**Causa**: El servicio está tardando demasiado en responder

**Solución**:
```bash
# Verificar que el servicio no esté consumiendo demasiados recursos
htop

# Reiniciar el servicio
systemctl restart api-disano
```

### Error: SSL certificate expired

**Causa**: El certificado SSL caducó

**Solución**:
```bash
# Renovar certificado
certbot renew

# Reiniciar Nginx
systemctl restart nginx
```

### Error: Cannot bind to port 8000

**Causa**: Ya hay un proceso usando el puerto 8000

**Solución**:
```bash
# Ver qué proceso está usando el puerto
lsof -i :8000

# Matar el proceso si es necesario
kill -9 <PID>

# Reiniciar el servicio
systemctl restart api-disano
```

### El servicio no inicia después de reiniciar el servidor

**Causa**: El servicio no está habilitado para auto-inicio

**Solución**:
```bash
# Habilitar el servicio
systemctl enable api-disano

# Verificar que está habilitado
systemctl is-enabled api-disano
```

---

## 🔐 SEGURIDAD - PRÓXIMOS PASOS

Actualmente la API **NO tiene seguridad** implementada. Es necesario añadir:

### 1. Autenticación con API Key
- Solo permitir acceso con header `X-API-Key`
- Crear API keys seguras con `secrets.token_urlsafe(32)`

### 2. Rate Limiting
- Limitar peticiones por cliente (30 req/min)
- Prevenir scraping masivo de datos

### 3. User-Agent Filtering
- Bloquear User-Agents sospechosos (curl, python-requests, etc.)

### 4. Ocultar documentación
- Deshabilitar `/docs` y `/redoc` en producción
- No exponer OpenAPI schema

### 5. CORS restringido
- Solo permitir acceso desde dominios autorizados

### 6. HTTPS obligatorio
- Redirigir HTTP a HTTPS
- HSTS headers

---

## 📊 INTEGRACIÓN CON APP FLASK

Para usar la API desde tu app Flask (pdf-to-bc3-server):

```python
import requests
import os

API_URL = "https://api.eloymartinezcuesta.com"
API_KEY = os.getenv("DISANO_API_KEY")  # Cuando se implemente seguridad

headers = {
    "X-API-Key": API_KEY  # Opcional hasta que se implemente seguridad
}

# Ejemplo: Obtener productos
response = requests.get(f"{API_URL}/api/productos/?limit=10", headers=headers)
productos = response.json()

# Ejemplo: Buscar producto por código
codigo = "11253300"
response = requests.get(f"{API_URL}/api/productos/{codigo}", headers=headers)
producto = response.json()
```

---

## 📞 CONTACTO Y SOPORTE

- **Repositorio GitHub**: https://github.com/EloyEMC/API-DISANO
- **Documentación adicional**: Ver archivos `.md` en el repositorio

---

## ✅ CHECKLIST POST-DESPLEGUE

- [x] API funcionando en producción
- [x] Nginx configurado como reverse proxy
- [x] Certificado SSL instalado
- [x] Servicio systemd configurado
- [ ] Verificar auto-reinicio (pendiente)
- [ ] Verificar inicio tras reinicio del servidor (pendiente)
- [ ] Implementar seguridad (API Key, rate limiting, etc.)
- [ ] Configurar CORS para dominios autorizados
- [ ] Crear sistema de backups de la base de datos
- [ ] Configurar monitoreo y alertas

---

**Última actualización**: 1 de febrero de 2026
