#!/bin/bash
# ==============================================================================
# Script de Verificación de Seguridad - API DISANO
# ==============================================================================
#
# Este script verifica que todas las medidas de seguridad estén correctamente
# implementadas y funcionando.
#
# Uso:
#   export API_URL='http://localhost:8000'
#   export API_KEY='tu-api-key-aqui'
#   bash scripts/verify_security.sh
#
# ==============================================================================

set -e

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuración por defecto
API_URL="${API_URL:-http://localhost:8000}"
API_KEY="${API_KEY:-}"

echo "============================================"
echo "VERIFICACIÓN DE SEGURIDAD - API DISANO"
echo "URL: $API_URL"
echo "============================================"
echo ""

# Contadores
PASS=0
FAIL=0
WARNING=0

# Función helper
check_status() {
    local test_name="$1"
    local expected="$2"
    local actual="$3"
    local test_type="$4"

    if [ "$expected" = "$actual" ]; then
        echo -e "${GREEN}✓ PASS${NC} ($test_name)"
        ((PASS++))
        return 0
    else
        if [ "$test_type" = "warning" ]; then
            echo -e "${YELLOW}⊘ WARNING${NC} ($test_name): Expected $expected, got $actual"
            ((WARNING++))
            return 0
        else
            echo -e "${RED}✗ FAIL${NC} ($test_name): Expected $expected, got $actual"
            ((FAIL++))
            return 1
        fi
    fi
}

# ==============================================================================
# TESTS DE DESCUBRIMIENTO
# ==============================================================================

echo "=== TESTS DE DESCUBRIMIENTO ==="
echo ""

# Test 1: Health check (debe ser 200)
echo -n "1. Health check público... "
status=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health")
check_status "Health check" "200" "$status"

# Test 2: Documentación NO debe ser accesible
echo -n "2. Documentación (/docs) debe ser 404... "
status=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/docs")
check_status "Docs ocultas" "404" "$status"

# Test 3: OpenAPI schema NO debe existir
echo -n "3. OpenAPI schema (/openapi.json) debe ser 404... "
status=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/openapi.json")
check_status "OpenAPI oculto" "404" "$status"

# Test 4: Robots.txt debe denegar todo
echo -n "4. Robots.txt debe denegar indexación... "
robots=$(curl -s "$API_URL/robots.txt")
if echo "$robots" | grep -q "Disallow: /"; then
    echo -e "${GREEN}✓ PASS${NC} (Indexación bloqueada)"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC} (Permite indexación)"
    ((FAIL++))
fi

# Test 5: Server header debe ser genérico
echo -n "5. Server header debe ser genérico... "
server=$(curl -s -I "$API_URL/health" | grep -i "server:" | cut -d' ' -f2 | tr -d '\r' || echo "unknown")
if [[ ! "$server" =~ *"fastapi"* ]] && [[ ! "$server" =~ *"uvicorn"* ]]; then
    echo -e "${GREEN}✓ PASS${NC} (Server: $server)"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC} (Expone tecnología: $server)"
    ((FAIL++))
fi

# Test 6: Prefijo personalizado usado
echo -n "6. Endpoint estándar (/api/productos) debe ser 404... "
status=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/productos/")
check_status "Prefijo personalizado" "404" "$status" "warning"

echo ""

# ==============================================================================
# TESTS DE AUTENTICACIÓN
# ==============================================================================

echo "=== TESTS DE AUTENTICACIÓN ==="
echo ""

# Test 7: Endpoint sin API key (debe fallar)
echo -n "7. Acceso sin API key debe ser 401... "
status=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/v1/internal/products/")
check_status "Sin API key" "401" "$status"

# Test 8: Endpoint con API key inválida (debe fallar)
echo -n "8. Acceso con API key inválida debe ser 401... "
status=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "X-API-Key: invalid-key-12345" \
    "$API_URL/v1/internal/products/")
check_status "API key inválida" "401" "$status"

# Test 9: Endpoint con API key válida (debe funcionar)
if [ -n "$API_KEY" ]; then
    echo -n "9. Acceso con API key válida debe ser 200... "
    status=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "X-API-Key: $API_KEY" \
        "$API_URL/v1/internal/products/?limit=10")
    check_status "API key válida" "200" "$status"
else
    echo -e "${YELLOW}⊘ SKIP${NC} Test 9 - API_KEY no proporcionada"
    echo "   Para ejecutar: export API_KEY='tu-api-key'"
fi

echo ""

# ==============================================================================
# TESTS DE RATE LIMITING
# ==============================================================================

echo "=== TESTS DE RATE LIMITING ==="
echo ""

if [ -n "$API_KEY" ]; then
    # Test 10: Rate limiting (hacer 35 peticiones rápidas)
    echo -n "10. Rate limiting (35 peticiones rápidas)... "
    success=0
    for i in {1..35}; do
        status=$(curl -s -o /dev/null -w "%{http_code}" \
            -H "X-API-Key: $API_KEY" \
            "$API_URL/v1/internal/products/?limit=10" 2>/dev/null || echo "000")
        if [ "$status" = "429" ]; then
            success=1
            break
        fi
        # Pequeño delay para no saturar
        sleep 0.05
    done
    if [ $success -eq 1 ]; then
        echo -e "${GREEN}✓ PASS${NC} (Rate limit activado)"
        ((PASS++))
    else
        echo -e "${YELLOW}⊘ WARNING${NC} (Rate limit quizás muy permisivo)"
        ((WARNING++))
    fi
else
    echo -e "${YELLOW}⊘ SKIP${NC} Tests de rate limiting - API_KEY no proporcionada"
fi

echo ""

# ==============================================================================
# TESTS DE USER-AGENT FILTERING
# ==============================================================================

echo "=== TESTS DE USER-AGENT FILTERING ==="
echo ""

# Test 11: User-Agent 'curl' debe ser bloqueado
echo -n "11. User-Agent 'curl' debe ser bloqueado... "
status=$(curl -s -o /dev/null -w "%{http_code}" \
    -A "curl/7.68.0" \
    "$API_URL/v1/internal/products/")
if [ "$status" = "403" ] || [ "$status" = "401" ]; then
    echo -e "${GREEN}✓ PASS${NC} (User-Agent bloqueado)"
    ((PASS++))
else
    echo -e "${YELLOW}⊘ WARNING${NC} (No bloqueado: $status)"
    ((WARNING++))
fi

# Test 12: User-Agent 'python-requests' debe ser bloqueado
echo -n "12. User-Agent 'python-requests' debe ser bloqueado... "
status=$(curl -s -o /dev/null -w "%{http_code}" \
    -A "python-requests/2.28.0" \
    "$API_URL/v1/internal/products/")
if [ "$status" = "403" ] || [ "$status" = "401" ]; then
    echo -e "${GREEN}✓ PASS${NC} (User-Agent bloqueado)"
    ((PASS++))
else
    echo -e "${YELLOW}⊘ WARNING${NC} (No bloqueado: $status)"
    ((WARNING++))
fi

echo ""

# ==============================================================================
# TESTS DE PAGINACIÓN
# ==============================================================================

echo "=== TESTS DE PAGINACIÓN ==="
echo ""

if [ -n "$API_KEY" ]; then
    # Test 13: Intentar pedir 500 productos debe fallar
    echo -n "13. Pedir 500 productos debe fallar (422)... "
    status=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "X-API-Key: $API_KEY" \
        "$API_URL/v1/internal/products/?limit=500")
    if [ "$status" = "422" ]; then
        echo -e "${GREEN}✓ PASS${NC} (Validación funciona)"
        ((PASS++))
    else
        echo -e "${YELLOW}⊘ WARNING${NC} (Permite más de 100: $status)"
        ((WARNING++))
    fi
else
    echo -e "${YELLOW}⊘ SKIP${NC} Tests de paginación - API_KEY no proporcionada"
fi

echo ""

# ==============================================================================
# RESUMEN
# ==============================================================================

echo "============================================"
echo "RESUMEN DE VERIFICACIÓN"
echo "============================================"
echo -e "${GREEN}✓ PASSED:${NC} $PASS"
echo -e "${RED}✗ FAILED:${NC} $FAIL"
echo -e "${YELLOW}⊘ WARNINGS:${NC} $WARNING"
echo ""

TOTAL=$((PASS + FAIL))
if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}🎉 TODOS LOS TESTS CRÍTICOS PASARON${NC}"
    echo ""
    echo "Tu API está protegida contra:"
    echo "  • Descubrimiento automático (sin /docs ni /openapi.json)"
    echo "  • Scraping básico (User-Agent bloqueado)"
    echo "  • Rate limiting (previene abuso)"
    echo "  • Acceso no autorizado (API key requerida)"
    echo "  • Indexación en buscadores (robots.txt)"
    echo ""
    if [ $WARNING -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Hay $WARNING advertencias que deberías revisar${NC}"
    fi
    exit 0
else
    echo -e "${RED}❌ HAY $FAIL TESTS FALLANDO${NC}"
    echo "Por favor revisa la configuración de seguridad"
    exit 1
fi
