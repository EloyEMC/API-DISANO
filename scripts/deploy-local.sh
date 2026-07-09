#!/bin/bash
# ==============================================================================
# Script de Despliegue Remoto - Desde Mac a Hetzner VPS
# ==============================================================================
#
# Este script se ejecuta desde tu Mac y se conecta al VPS para desplegar.
#
# Uso:
#   bash scripts/deploy-local.sh
#
# ==============================================================================

set -e

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║         🚀 DESPLIEGUE REMOTO - DESDE MAC A HETZNER VPS                  ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

# Pedir datos de conexión
read -p "IP de tu VPS Hetzner: " VPS_IP
read -p "Usuario root [root]: " VPS_USER
VPS_USER=${VPS_USER:-root}
read -p "Dominio (ej: api-disano.com): " DOMAIN
read -p "Email para Let's Encrypt: " EMAIL

echo ""
echo "📋 Configuración:"
echo "   VPS: $VPS_USER@$VPS_IP"
echo "   Dominio: $DOMAIN"
echo "   Email: $EMAIL"
echo ""
read -p "¿Continuar? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelado."
    exit 0
fi

# Verificar que tenemos el script de despliegue
if [ ! -f "scripts/deploy-hetzner.sh" ]; then
    echo "❌ Error: No encuentro scripts/deploy-hetzner.sh"
    echo "   Asegúrate de estar en el directorio raíz del proyecto"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📤 1/3 SUBIENDO SCRIPT AL VPS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

scp scripts/deploy-hetzner.sh $VPS_USER@$VPS_IP:/root/

echo -e "\033[0;32m✅ Script subido\033[0m"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 2/3 EJECUTANDO DESPLIEGUE EN EL VPS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ssh $VPS_USER@$VPS_IP << EOF_REMOTE
export DOMAIN="$DOMAIN"
export EMAIL="$EMAIL"
bash /root/deploy-hetzner.sh
EOF_REMOTE

echo -e "\033[0;32m✅ Despliegue completado\033[0m"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📥 3/3 OBTENIENDO CREDENCIALES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

scp $VPS_USER@$VPS_IP:/root/api-disano-credentials.txt ./api-disano-credentials.txt
cat ./api-disano-credentials.txt

echo -e "\033[0;32m✅ Credenciales guardadas en ./api-disano-credentials.txt\033[0m"

echo ""
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║                  ✅ DESPLIEGUE COMPLETADO CON ÉXITO                      ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Tu API está disponible en:"
echo "   https://$DOMAIN"
echo ""
echo "🧪 Prueba:"
echo "   curl https://$DOMAIN/health"
echo ""
echo "📝 Credenciales guardadas en:"
echo "   ./api-disano-credentials.txt"
echo ""
