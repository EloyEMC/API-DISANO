# 🔑 ACCESO AL SERVIDOR VPS HETZNER

## Información de Conexión

**Servidor:** API DISANO en Hetzner VPS
**IP:** `46.62.227.64`
**Usuario:** `root`
**Contraseña:** `icXvsgbi4ded`

## Conexión SSH

### Desde terminal local:
```bash
ssh root@46.62.227.64
# Introducir contraseña: icXvsgbi4ded
```

### Con expect (para scripts automatizados):
```bash
expect << 'EXPECT_EOF'
set timeout 30
spawn ssh -o StrictHostKeyChecking=no root@46.62.227.64 "comando"
expect {
    "(yes/no)?" { send "yes\r"; exp_continue }
    "password:" { send "icXvsgbi4ded\r"; exp_continue }
    eof
}
EXPECT_EOF
```

## Ubicaciones Importantes en el Servidor

| Ruta | Descripción |
|------|-------------|
| `/var/www/API-DISANO/` | Directorio principal de la API |
| `/var/www/API-DISANO/.env` | Archivo de configuración (API keys, etc) |
| `/var/www/API-DISANO/venv/` | Entorno virtual Python |
| `/var/www/API-DISANO/logs/` | Logs de la aplicación |
| `/etc/systemd/system/api-disano.service` | Servicio systemd |
| `/etc/nginx/sites-available/api-disano` | Configuración Nginx |

## Comandos Frequentes

### Actualizar la API desde GitHub:
```bash
cd /var/www/API-DISANO
git pull
```

### Reiniciar el servicio:
```bash
systemctl restart api-disano
```

### Ver estado del servicio:
```bash
systemctl status api-disano
```

### Ver logs de la API:
```bash
# Logs del servicio systemd
journalctl -u api-disano -f

# Logs de la aplicación
tail -f /var/www/API-DISANO/logs/api.log
```

### Ver logs de Nginx:
```bash
tail -f /var/log/nginx/error.log
```

### Probar la API localmente:
```bash
curl -H "X-API-Key: yqZ2eOmHH8y08VesvL5zalSg8lq3b7NTpuitRtWe2bs" \
     -H "User-Agent: Mozilla/5.0" \
     http://127.0.0.1:8000/api/productos/?limit=1
```

## Flujo de Actualización Tipico

Cuando haces cambios en el código local:

1. **Hacer commit y push a GitHub:**
   ```bash
   git add .
   git commit -m "Descripción de cambios"
   git push origin main
   ```

2. **Conectar al VPS:**
   ```bash
   ssh root@46.62.227.64
   ```

3. **Actualizar código:**
   ```bash
   cd /var/www/API-DISANO
   git pull
   ```

4. **Reiniciar servicio:**
   ```bash
   systemctl restart api-disano
   ```

5. **Verificar estado:**
   ```bash
   systemctl status api-disano
   journalctl -u api-disano -n 20
   ```

## URL Pública

- **Producción:** `https://api.eloymartinezcuesta.com`
- **Health check:** `https://api.eloymartinezcuesta.com/health`
- **API productos:** `https://api.eloymartinezcuesta.com/api/productos/`

## Seguridad

- La API usa **X-API-Key** para autenticación
- La key de producción está en `/var/www/API-DISANO/.env`
- Nginx maneja SSL con Let's Encrypt
- Firewall UFW habilitado (puertos 22, 80, 443)

## Solución de Problemas Comunes

### Error: "NameError: name 'RATE_LIMIT' is not defined"
**Solución:** Ya corregido en security.py línea 139 y 153
```bash
sed -i 's/RATE_LIMIT/rate_limit/g' /var/www/API-DISANO/app/security.py
systemctl restart api-disano
```

### Error: 502 Bad Gateway
**Causa:** La API no está corriendo
**Solución:**
```bash
systemctl status api-disano
journalctl -u api-disano -n 50
```

### Error: Certificado SSL
**Solución:**
```bash
certbot --nginx -d api.eloymartinezcuesta.com -d www.api.eloymartinezcuesta.com
```

---

**Última actualización:** 14 Feb 2026
**Estado:** ✅ Activo y funcionando
**Commit actual:** 9311049
