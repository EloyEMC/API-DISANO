#!/bin/bash
# =============================================================================
# Script de Configuración Producción - API DISANO
# =============================================================================
#
# Este script genera una API key segura y actualiza la configuración
# en el servidor para producción con seguridad activada.
#
# =============================================================================

set -e

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║       🔐 CONFIGURACIÓN DE SEGURIDAD - API DISANO PRODUCCIÓN            ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

# Generate API Key
API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

echo "🔑 API Key generada: $API_KEY"
echo ""

# Create .env file
cat > /var/www/API-DISANO/.env << EOF
# Production Configuration
ENVIRONMENT=production
API_HOST=127.0.0.1
API_PORT=8000

# API Keys (separadas por comas si hay múltiples)
API_KEYS=$API_KEY

# Rate Limiting
RATE_LIMIT_PER_MINUTE=30

# CORS (solo dominios autorizados)
CORS_ORIGINS=https://eloymartinezcuesta.com,https://disano.eloymartinezcuesta.com

# Database
DATABASE_PATH=database/tarifa_disano.db
EOF

echo "✅ Archivo .env creado"
echo ""

# Save credentials
cat > /root/api-disano-api-key.txt << CREDS_EOF
API DISANO - CREDENCIALES
═════════════════════════

URL: https://api.eloymartinezcuesta.com
Environment: production

API Key: $API_KEY

⚠️  GUARDAR ESTA API KEY - NECESARIA PARA ACCEDER

Ejemplo de uso:
  curl -H "X-API-Key: $API_KEY" \\
       https://api.eloymartinezcuesta.com/api/productos/?limit=10

Para usar desde Python:
  import requests
  headers = {"X-API-Key": "$API_KEY"}
  response = requests.get("https://api.eloymartinezcuesta.com/api/productos/", headers=headers)

Generado: $(date)
CREDS_EOF

chmod 600 /root/api-disano-api-key.txt

echo "✅ Credenciales guardadas en: /root/api-disano-api-key.txt"
echo ""

# Restart service
echo "🔄 Reiniciando servicio..."
systemctl restart api-disano
sleep 3

# Verify
echo "🧪 Verificando servicio..."
systemctl status api-disano --no-pager -n 15

echo ""
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║                  ✅ CONFIGURACIÓN COMPLETADA                            ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📝 Resumen:"
echo "   Environment: production"
echo "   API Key: $API_KEY"
echo "   Rate limiting: 30 req/min"
echo "   CORS: https://eloymartinezcuesta.com"
echo ""
echo "🧪 Prueba la API:"
echo "   curl -H \"X-API-Key: $API_KEY\" \\"
echo "        https://api.eloymartinezcuesta.com/api/productos/?limit=5"
echo ""
