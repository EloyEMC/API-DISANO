# 🚀 GUÍA DE DESPLIEGUE EN HETZNER

## Opción 1: Despliegue Automático (RECOMENDADO)

Esta es la forma más fácil. Solo necesitas tu VPS Hetzner funcionando.

### Paso 1: Preparativos

Asegúrate de que tienes:
- ✅ VPS Hetzner con Ubuntu 22.04 o Debian 12
- ✅ Dominio apuntando a la IP del VPS (registro A)
- ✅ Acceso SSH al VPS: `ssh root@tu-ip`

### Paso 2: Ejecutar script desde tu Mac

```bash
cd /Volumes/WEBS/API_DISANO
bash scripts/deploy-local.sh
```

El script te pedirá:
- IP de tu VPS (ej: `123.45.67.89`)
- Usuario (por defecto `root`)
- Dominio (ej: `api-disano.com`)
- Email para Let's Encrypt

### Paso 3: Esperar 5-10 minutos

El script hará todo automáticamente:
- ✅ Actualizar sistema
- ✅ Instalar dependencias
- ✅ Clonar repositorio
- ✅ Configurar entorno virtual
- ✅ Configurar Nginx
- ✅ Instalar certificado SSL
- ✅ Crear servicio systemd
- ✅ Configurar firewall

### Paso 4: ¡Listo!

Tu API estará disponible en: `https://tu-dominio.com`

---

## Opción 2: Despliegue Manual

Si prefieres hacerlo manualmente, sigue estos pasos:

### 1. Conectar al VPS

```bash
ssh root@tu-vps-ip
```

### 2. Actualizar sistema

```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv python3-certbot-nginx nginx certbot git ufw
```

### 3. Clonar repositorio

```bash
cd /var/www
git clone https://github.com/EloyEMC/API-DISANO.git
cd API-DISANO
```

### 4. Crear entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Configurar .env

```bash
nano .env
```

Copia el contenido de `.env.example` y configura:
- `ENVIRONMENT=production`
- `API_KEYS=tu-api-key-generada`
- `CORS_ORIGINS=https://tu-dominio.com`

### 6. Configurar Nginx

```bash
nano /etc/nginx/sites-available/api-disano
```

```nginx
server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
ln -s /etc/nginx/sites-available/api-disano /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
```

### 7. Configurar SSL

```bash
certbot --nginx -d tu-dominio.com -d www.tu-dominio.com
```

### 8. Crear servicio systemd

```bash
nano /etc/systemd/system/api-disano.service
```

```ini
[Unit]
Description=API Disano
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/var/www/API-DISANO
Environment="PATH=/var/www/API-DISANO/venv/bin"
EnvironmentFile=/var/www/API-DISANO/.env
ExecStart=/var/www/API-DISANO/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable api-disano
systemctl start api-disano
```

### 9. Configurar firewall

```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

### 10. Verificar

```bash
# Health check
curl https://tu-dominio.com/health

# Con API key
curl -H "X-API-Key: tu-api-key" \
  https://tu-dominio.com/v1/internal/products/?limit=5

# Ver logs
journalctl -u api-disano -f
tail -f /var/www/API-DISANO/logs/api.log
```

---

## 📋 Post-Despliegue

### Verificar que todo funciona

```bash
# 1. Health check (debe retornar 200)
curl https://tu-dominio.com/health

# 2. Sin API key (debe retornar 401)
curl https://tu-dominio.com/v1/internal/products/

# 3. Con API key (debe retornar productos)
curl -H "X-API-Key: tu-api-key" \
  https://tu-dominio.com/v1/internal/products/?limit=5

# 4. Documentación (debe retornar 404)
curl https://tu-dominio.com/docs
```

### Actualizar la API

```bash
# En el VPS
cd /var/www/API-DISANO
git pull
systemctl restart api-disano
```

### Ver logs

```bash
# Logs del servicio
journalctl -u api-disano -f

# Logs de la aplicación
tail -f /var/www/API-DISANO/logs/api.log
tail -f /var/www/API-DISANO/logs/security.log

# Logs de Nginx
tail -f /var/log/nginx/error.log
```

---

## 🔧 Solución de Problemas

### Error: 502 Bad Gateway

```bash
# Verificar que el servicio esté corriendo
systemctl status api-disano

# Ver logs
journalctl -u api-disano -n 50
```

### Error: Certificado SSL

```bash
# Renovar certificado
certbot renew
```

### Error: 401 Unauthorized

- Verificar que envías el header `X-API-Key`
- Verificar que la API key sea correcta en `.env`

---

## 📊 Archivos Importantes

| Archivo | Ubicación |
|---------|-----------|
| Configuración | `/var/www/API-DISANO/.env` |
| Logs | `/var/www/API-DISANO/logs/` |
| Servicio | `/etc/systemd/system/api-disano.service` |
| Nginx | `/etc/nginx/sites-available/api-disano` |
| Credenciales | `/root/api-disano-credentials.txt` |

---

## 🎯 Próximos Pasos

Una vez desplegada:

1. ✅ Integrar con tu app Flask (pdf-to-bc3-server)
2. ✅ Crear frontend Astro
3. ✅ Configurar monitoreo
4. ✅ Configurar backups automáticos
