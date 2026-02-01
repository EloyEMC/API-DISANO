# 🔍 VERIFICACIÓN DE AUTO-REINICIO Y AUTO-INICIO

## 📋 OBJETIVO

Verificar que el servicio `api-disano` esté configurado correctamente para:
1. **Auto-reinicio**: Reiniciarse automáticamente si falla
2. **Auto-inicio**: Iniciarse automáticamente al arrancar el servidor

---

## 🚀 PASOS A EJECUTAR EN EL SERVIDOR

Conéctate a tu servidor por SSH y ejecuta estos comandos uno por uno:

### PASO 1: Verificar que el servicio está activo

```bash
systemctl status api-disano
```

**Debes ver**:
- `Active: active (running)`
- `Loaded: loaded (...)` y `enabled`

---

### PASO 2: Verificar que está habilitado para auto-inicio

```bash
systemctl is-enabled api-disano
```

**Debe mostrar**: `enabled`

Si muestra `disabled` o `static`, ejecuta:
```bash
systemctl enable api-disano
```

---

### PASO 3: Verificar la política de reinicio

```bash
grep -E "Restart|Enabled" /etc/systemd/system/api-disano.service
```

**Debe mostrar**:
```
Restart=always
RestartSec=10
```

Si no muestra `Restart=always`, edita el archivo:
```bash
nano /etc/systemd/system/api-disano.service
```

Asegúrate de que la sección `[Service]` contenga:
```ini
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
```

Guarda: `CTRL+O`, `Enter`, `CTRL+X`

Luego recarga:
```bash
systemctl daemon-reload
systemctl restart api-disano
```

---

### PASO 4: Probar el auto-reinicio

Esta prueba matará el proceso y verificará que systemd lo reinicie automáticamente.

```bash
# Ver PID actual
echo "PID actual: $(pidof uvicorn)"

# Matar el proceso
kill -9 $(pidof uvicorn)

# Esperar 10 segundos
echo "Esperando 10 segundos..."
sleep 10

# Verificar que se reinició
echo "Nuevo PID: $(pidof uvicorn)"
systemctl status api-disano
```

**Si funciona correctamente**:
- El nuevo PID será diferente al anterior
- `systemctl status` mostrará `Active: active (running)`
- Verás en los logs algo como "Service restarted" o "Started API Disano"

---

### PASO 5: Verificar la API responde

```bash
curl http://127.0.0.1:8000/health
```

**Debe mostrar**:
```json
{"status":"ok","service":"api-disano"}
```

---

### PASO 6: Verificar desde internet (desde tu Mac)

En tu Mac, ejecuta:

```bash
curl https://api.eloymartinezcuesta.com/health
```

**Nota**: Si curl da error de certificado SSL, usa `-k`:
```bash
curl -k https://api.eloymartinezcuesta.com/health
```

---

### PASO 7 (OPCIONAL): Probar reinicio del servidor

⚠️ **ADVERTENCIA**: Esto reiniciará todo el servidor, desconectando todas las sesiones.

Solo ejecuta si es necesario y has guardado todo tu trabajo.

```bash
reboot
```

**Luego**:
1. Espera 2-3 minutos a que el servidor reinicie
2. Conéctate de nuevo por SSH
3. Ejecuta: `systemctl status api-disano`

**Debe mostrar**: `Active: active (running)` sin que tú hayas hecho nada manualmente.

---

## ✅ CRITERIOS DE ÉXITO

✅ El servicio está `active (running)`
✅ El servicio está `enabled`
✅ Tiene `Restart=always` configurado
✅ Al matar el proceso, se reinicia automáticamente
✅ La API responde correctamente
✅ Tras reiniciar el servidor, el servicio se inicia solo

---

## 📝 COMANDOS ÚTILES

```bash
# Ver logs en tiempo real
journalctl -u api-disano -f

# Ver últimos 50 logs
journalctl -u api-disano -n 50

# Ver cuántas veces se ha reiniciado
systemctl show api-disano -p NRestarts --value

# Reiniciar servicio manualmente
systemctl restart api-disano

# Ver tiempo de actividad del servicio
systemctl show api-disano -p ActiveEnterTimestamp --value
```

---

## 🚨 SI ALGO NO FUNCIONA

### El servicio no se reinicia automáticamente

Edita el archivo del servicio:
```bash
nano /etc/systemd/system/api-disano.service
```

Asegúrate de que en la sección `[Service]` tengas:
```ini
Restart=always
RestartSec=10
```

Recarga y reinicia:
```bash
systemctl daemon-reload
systemctl restart api-disano
```

### El servicio no se inicia al arrancar el servidor

Habilita el servicio:
```bash
systemctl enable api-disano
```

Verifica:
```bash
systemctl is-enabled api-disano
```

### El servicio falla al iniciar

Revisa los logs:
```bash
journalctl -u api-disano -n 50
```

Busca errores en los logs que indiquen qué está fallando.

---

**Última actualización**: 1 de febrero de 2026
