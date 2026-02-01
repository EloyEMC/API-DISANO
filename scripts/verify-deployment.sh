#!/bin/bash
# =============================================================================
# Script de Verificación de Despliegue - API DISANO
# =============================================================================
#
# Este script verifica que el servicio esté correctamente configurado
# para auto-reinicio y inicio automático tras reinicio del servidor.
#
# Uso:
#   bash scripts/verify-deployment.sh
#
# =============================================================================

set -e

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║         🔍 VERIFICACIÓN DE DESPLIEGUE - API DISANO                     ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Contadores
PASS=0
FAIL=0

# Función para verificar
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $1"
        ((PASS++))
    else
        echo -e "${RED}❌ FAIL${NC}: $1"
        ((FAIL++))
    fi
}

# =============================================================================
# 1. VERIFICAR SERVICIO ESTÁ ACTIVO
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 1/8 VERIFICANDO SERVICIO ACTIVO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

systemctl is-active api-disano >/dev/null 2>&1
check "El servicio está activo"

systemctl status api-disano >/dev/null 2>&1
check "El servicio existe y es accesible"

echo ""

# =============================================================================
# 2. VERIFICAR AUTO-INICIO (ENABLED)
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 2/8 VERIFICANDO AUTO-INICIO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ENABLED=$(systemctl is-enabled api-disano 2>/dev/null)
if [ "$ENABLED" = "enabled" ]; then
    echo -e "${GREEN}✅ PASS${NC}: El servicio está habilitado para auto-inicio"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC}: El servicio NO está habilitado (estado: $ENABLED)"
    ((FAIL++))
fi

echo ""

# =============================================================================
# 3. VERIFICAR POLÍTICA DE REINICIO
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 3/8 VERIFICANDO POLÍTICA DE REINICIO AUTOMÁTICO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if grep -q "Restart=always" /etc/systemd/system/api-disano.service; then
    echo -e "${GREEN}✅ PASS${NC}: Restart=always configurado"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC}: Restart=always NO configurado"
    ((FAIL++))
fi

if grep -q "RestartSec=10" /etc/systemd/system/api-disano.service; then
    echo -e "${GREEN}✅ PASS${NC}: RestartSec=10 configurado"
    ((PASS++))
else
    echo -e "${YELLOW}⚠️  WARNING${NC}: RestartSec no configurado (opcional)"
fi

echo ""

# =============================================================================
# 4. VERIFICAR RESPUESTA DE LA API
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 4/8 VERIFICANDO RESPUESTA DE LA API"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(curl -s http://127.0.0.1:8000/health)
if echo "$RESPONSE" | grep -q '"status":"ok"'; then
    echo -e "${GREEN}✅ PASS${NC}: La API responde correctamente"
    echo "   Response: $RESPONSE"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC}: La API NO responde o respuesta incorrecta"
    echo "   Response: $RESPONSE"
    ((FAIL++))
fi

echo ""

# =============================================================================
# 5. VERIFICAR CONFIGURACIÓN NGINX
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 5/8 VERIFICANDO CONFIGURACIÓN NGINX"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

nginx -t 2>/dev/null
check "Configuración de Nginx es válida"

if [ -f /etc/nginx/sites-enabled/api-disano ]; then
    echo -e "${GREEN}✅ PASS${NC}: Site de Nginx está habilitado"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC}: Site de Nginx NO está habilitado"
    ((FAIL++))
fi

echo ""

# =============================================================================
# 6. VERIFICAR CERTIFICADO SSL
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 6/8 VERIFICANDO CERTIFICADO SSL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if certbot certificates 2>/dev/null | grep -q "api.eloymartinezcuesta.com"; then
    echo -e "${GREEN}✅ PASS${NC}: Certificado SSL instalado para api.eloymartinezcuesta.com"
    ((PASS++))

    # Verificar fecha de expiración
    EXPIRY=$(certbot certificates 2>/dev/null | grep -A 5 "api.eloymartinezcuesta.com" | grep "Expiry Date" | cut -d: -f2 | xargs)
    echo "   Expira: $EXPIRY"
else
    echo -e "${RED}❌ FAIL${NC}: Certificado SSL NO encontrado"
    ((FAIL++))
fi

echo ""

# =============================================================================
# 7. PRUEBA DE AUTO-REINICIO
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 7/8 PRUEBA DE AUTO-REINICIO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "ℹ️  Esta prueba matará el proceso y verificará que systemd lo reinicie"
echo ""

# Obtener PID actual
PID=$(pidof uvicorn || echo "")
if [ -n "$PID" ]; then
    echo "ℹ️  Proceso uvicorn encontrado con PID: $PID"

    # Matar proceso
    echo "🔪 Matando proceso..."
    kill -9 $PID 2>/dev/null || true

    # Esperar a que systemd lo reinicie
    echo "⏳ Esperando 15 segundos para que systemd reinicie..."
    sleep 15

    # Verificar que se reinició
    NEW_PID=$(pidof uvicorn || echo "")
    if [ -n "$NEW_PID" ]; then
        if [ "$NEW_PID" != "$PID" ]; then
            echo -e "${GREEN}✅ PASS${NC}: El servicio se reinició automáticamente"
            echo "   Viejo PID: $PID"
            echo "   Nuevo PID: $NEW_PID"
            ((PASS++))
        else
            echo -e "${RED}❌ FAIL${NC}: El proceso sigue siendo el mismo (no se reinició)"
            ((FAIL++))
        fi
    else
        echo -e "${RED}❌ FAIL${NC}: El servicio NO se reinició"
        ((FAIL++))
    fi
else
    echo -e "${RED}❌ FAIL${NC}: No hay proceso uvicorn corriendo"
    ((FAIL++))
fi

echo ""

# =============================================================================
# 8. VERIFICAR ÚLTIMO REINICIO
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 8/8 VERIFICANDO HISTORIAL DE REINICIOS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESTART_COUNT=$(systemctl show api-disano -p NRestarts --value)
echo "ℹ️  Número de reinicios: $RESTART_COUNT"

if [ "$RESTART_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS${NC}: El servicio se ha reiniciado $RESTART_COUNT vez/veces"
    ((PASS++))
else
    echo -e "${YELLOW}⚠️  INFO${NC}: El servicio no se ha reiniciado aún (es normal si acaba de configurarse)"
    ((PASS++))
fi

# Mostrar últimos restarts
echo ""
echo "Últimos reinicios:"
journalctl -u api-disano --no-pager -n 20 | grep -i "started\|restart" | tail -5

echo ""

# =============================================================================
# RESUMEN FINAL
# =============================================================================

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║                      📊 RESUMEN DE VERIFICACIÓN                        ║"
echo "╚════════════════════════════════════════════════━━━━━━━━━━━━━━━━━━━━━━━╝"
echo ""

echo -e "Tests pasados: ${GREEN}$PASS${NC}"
echo -e "Tests fallidos: ${RED}$FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                  ✅ TODAS LAS VERIFICACIONES PASARON                    ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "🎉 El servicio está correctamente configurado para:"
    echo "   ✅ Auto-reinicio en caso de fallo"
    echo "   ✅ Inicio automático al arrancar el servidor"
    echo ""
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                  ⚠️  HAY PROBLEMAS QUE REQUIEREN ATENCIÓN               ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Revisa los tests fallidos arriba y corrige los problemas."
    echo ""
    exit 1
fi
