# 🔐 DESPLIEGUE DE SEGURIDAD EN PRODUCCIÓN

## 📋 RESUMEN DE SEGURIDAD IMPLEMENTADA

He añadido 4 capas de seguridad a la API:

| Capa | Función | Estado |
|------|---------|--------|
| **API Key Authentication** | Solo permite acceso con header `X-API-Key` | ✅ Implementado |
| **Rate Limiting** | Máximo 30 peticiones/minuto por cliente | ✅ Implementado |
| **User-Agent Filtering** | Bloquea scrapers (curl, python-requests, etc.) | ✅ Implementado |
| **Security Headers** | HSTS, X-Frame-Options, etc. | ✅ Implementado |

### Características adicionales:

- 📝 **Documentación oculta** en producción: `/docs` y `/redoc` retornan 404
- 🔒 **CORS restringido** en producción: solo dominios autorizados
- 🚫 **Sin información de versión** en headers para no delatar tecnología

---

## 🚀 PASOS PARA DESPLEGAR EN PRODUCCIÓN

### PASO 1: Actualizar código en el servidor

En la consola del servidor, ejecuta:

```bash
cd /var/www/API-DISANO
git pull origin main
```

---

### PASO 2: Ejecutar script de configuración de producción

```bash
bash scripts/setup-production.sh
```

**Este script hará:**
- ✅ Generar una API key segura (32 caracteres aleatorios)
- ✅ Crear archivo `.env` con configuración de producción
- ✅ Guardar la API key en `/root/api-disano-api-key.txt`
- ✅ Reiniciar el servicio

---

### PASO 3: Verificar que funciona

```bash
# 1. Verificar que el servicio está activo
systemctl status api-disano
```

---

### PASO 4: Probar la seguridad

#### Test 1: Sin API key (debe fallar con 401)

```bash
curl https://api.eloymartinezcuesta.com/api/productos/?limit=2
```

**Debe retornar**:
```json
{"detail":"API Key is required. Use X-API-Key header."}
```

#### Test 2: Con API key correcta (debe funcionar)

```bash
curl -H "X-API-Key: TU_API_KEY_AQUI" \
     https://api.eloymartinezcuesta.com/api/productos/?limit=2
```

**Debe retornar**: Array con 2 productos

#### Test 3: Documentación oculta (debe retornar 404)

```bash
curl https://api.eloymartinezcuesta.com/docs
```

**Debe retornar**: 404 Not Found

#### Test 4: Rate limiting (hacer 35 peticiones rápidas)

```bash
for i in {1..35}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
       -H "X-API-Key: TU_API_KEY_AQUI" \
       https://api.eloymartinezcuesta.com/api/productos/?limit=2
done
```

**Después de 30 peticiones** debe retornar: 429 Too Many Requests

#### Test 5: Health check siempre accesible

```bash
curl https://api.eloymartinezcuesta.com/health
```

**Debe retornar**:
```json
{"status":"ok","service":"api-disano"}
```

---

## 📝 OBTENER LA API KEY

Después de ejecutar el script `setup-production.sh`, la API key se guardará en:

```bash
cat /root/api-disano-api-key.txt
```

O puedes generar una nueva:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🔧 CONFIGURACIÓN MANUAL (OPCIONAL)

Si prefieres configurar manualmente en lugar de usar el script:

### 1. Editar .env

```bash
nano /var/www/API-DISANO/.env
```

Contenido:

```bash
# Production Configuration
ENVIRONMENT=production
API_HOST=127.0.0.1
API_PORT=8000

# API Keys (separadas por comas si hay múltiples)
API_KEYS=tu-api-key-generada-aqui

# Rate Limiting
RATE_LIMIT_PER_MINUTE=30

# CORS (solo dominios autorizados)
CORS_ORIGINS=https://eloymartinezcuesta.com,https://disano.eloymartinezcuesta.com

# Database
DATABASE_PATH=database/tarifa_disano.db
```

### 2. Reiniciar servicio

```bash
systemctl restart api-disano
systemctl status api-disano
```

---

## 🚨 SOLUCIÓN DE PROBLEMAS

### Error: 401 Unauthorized

**Causa**: No estás enviando la API key o es incorrecta

**Solución**:
```bash
# Verificar tu API key
cat /root/api-disano-api-key.txt

# Usar la API key correcta
curl -H "X-API-Key: TU_API_KEY" https://api.eloymartinezcuesta.com/api/productos/
```

### Error: 429 Too Many Requests

**Causa**: Has excedido el rate limit (30 peticiones/minuto)

**Solución**: Espera 1 minuto y vuelve a intentar, o implementa caching en tu app Flask.

### La documentación sigue accesible

**Causa**: El `.env` no tiene `ENVIRONMENT=production`

**Solución**:
```bash
# Verificar environment
grep ENVIRONMENT /var/www/API-DISANO/.env

# Debe mostrar: ENVIRONMENT=production
```

### Error: ImportError al iniciar el servicio

**Causa**: El código nuevo no se ha instalado correctamente

**Solución**:
```bash
cd /var/www/API-DISANO
git pull origin main
systemctl restart api-disano
journalctl -u api-disano -n 50
```

---

## 📊 EJEMPLO DE INTEGRACIÓN DESDE FLASK

```python
import requests
import os

# Configuración
API_URL = "https://api.eloymartinezcuesta.com"
API_KEY = os.getenv("DISANO_API_KEY")  # Tu API key

# Headers con autenticación
headers = {
    "X-API-Key": API_KEY
}

# Ejemplo 1: Obtener productos
def get_productos(limit=10):
    response = requests.get(
        f"{API_URL}/api/productos/?limit={limit}",
        headers=headers
    )
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        raise Exception("API Key inválida")
    elif response.status_code == 429:
        raise Exception("Rate limit excedido")
    else:
        raise Exception(f"Error: {response.status_code}")

# Ejemplo 2: Buscar producto por código
def get_producto(codigo):
    response = requests.get(
        f"{API_URL}/api/productos/{codigo}",
        headers=headers
    )
    return response.json()

# Ejemplo 3: Obtener familias
def get_familias():
    response = requests.get(
        f"{API_URL}/api/familias/",
        headers=headers
    )
    return response.json()
```

---

## ✅ CHECKLIST POST-DESPLEGUE

- [ ] Código actualizado con `git pull`
- [ ] Script `setup-production.sh` ejecutado
- [ ] API key guardada en lugar seguro
- [ ] Test sin API key retorna 401
- [ ] Test con API key retorna productos
- [ ] Documentación (/docs) retorna 404
- [ ] Rate limiting funciona (429 después de 30 peticiones)
- [ ] Health check accesible sin API key
- [ ] Service status: active (running)

---

## 🎯 PRÓXIMOS PASOS (FUTURO)

Cuando la seguridad básica esté funcionando, podemos añadir:

1. **Logging de eventos de seguridad** - Guardar intentos fallidos en un log
2. **IP Ban automático** - Banear IPs que intentan acceder sin API key
3. **Detección de scraping avanzado** - Detectar patrones sospechosos
4. **Redis para rate limiting** - Para distribuido y persistente
5. **API Key rotation** - Cambiar API keys periódicamente

---

**Última actualización**: 1 de febrero de 2026
