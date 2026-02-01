#!/bin/bash
# ==============================================================================
# Script para hacer push a GitHub - API DISANO
# ==============================================================================
#
# Este script prepara y hace push del código a GitHub.
# Asegúrate de haber ejecutado las pruebas primero.
#
# Uso:
#   bash scripts/github_push.sh
#
# ==============================================================================

set -e

echo "============================================"
echo "PREPARANDO PUSH A GITHUB"
echo "============================================"
echo ""

# 1. Verificar que no haya archivos sin commitear
echo "1. Verificando estado de git..."
if [ -n "$(git status --porcelain)" ]; then
    echo "   ℹ️  Hay cambios sin commitear"
    git status
    echo ""
else
    echo "   ℹ️  No hay cambios pendientes"
    exit 0
fi

# 2. Verificar que .env está en .gitignore
echo ""
echo "2. Verificando .gitignore..."
if git check-ignore .env > /dev/null 2>&1; then
    echo "   ✅ .env está en .gitignore"
else
    echo "   ❌ ERROR: .env NO está en .gitignore"
    echo "   Abortando..."
    exit 1
fi

# 3. Limpiar logs
echo ""
echo "3. Limpiando logs..."
rm -rf logs/*.log 2>/dev/null || true
touch logs/.gitkeep
echo "   ✅ Logs limpiados"

# 4. Limpiar cache de Python
echo ""
echo "4. Limpiando cache de Python..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo "   ✅ Cache limpiada"

# 5. Añadir archivos
echo ""
echo "5. Añadiendo archivos a git..."
git add app/config.py
git add app/security/
git add app/main.py
git add scripts/
git add .env.example
git add requirements.txt
git add SECURITY_README.md
git add IMPLEMENTACION_COMPLETA.md
git add ARQUITECTURA.md
git add .gitignore
echo "   ✅ Archivos añadidos"

# 6. Mostrar cambios
echo ""
echo "6. Resumen de cambios:"
git diff --cached --stat

# 7. Confirmar commit
echo ""
read -p "¿Crear commit con estos cambios? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "   Cancelado por usuario"
    exit 0
fi

# 8. Hacer commit
echo ""
echo "7. Creando commit..."
git commit -m "feat: Implementar seguridad completa en API DISANO

🔒 Seguridad implementada:
- API Key authentication (X-API-Key header)
- Rate limiting anti-scraping (30 peticiones/minuto)
- User-Agent filtering (bloquea curl, python-requests, etc.)
- Scraping detection (detección heurística de patrones)
- Logging estructurado (api.log + security.log)
- Documentación deshabilitada (/docs, /redoc, /openapi.json → 404)
- Prefijos personalizados (/v1/internal/products)
- Robots.txt (bloquea indexación)

📁 Módulos creados:
- app/config.py (configuración centralizada)
- app/security/ (módulo de seguridad)
  - api_key.py (validación API Keys)
  - rate_limiter.py (rate limiting)
  - user_agent_filter.py (filtro UA)
  - scraping_detector.py (detección scraping)
  - logging_config.py (sistema de logs)

🛠️ Scripts:
- scripts/setup.sh (configuración inicial)
- scripts/verify_security.sh (verificación de seguridad)

📖 Documentación:
- SECURITY_README.md (guía de uso)
- IMPLEMENTACION_COMPLETA.md (resumen)
- ARQUITECTURA.md (diagramas)

✅ Producción-ready"

echo "   ✅ Commit creado"

# 9. Verificar remote
echo ""
echo "8. Verificando remote de git..."
if git remote get-url origin > /dev/null 2>&1; then
    echo "   ℹ️  Remote origin ya configurado"
    git remote -v | grep origin
else
    echo "   ℹ️  Configurando remote origin..."
    git remote add origin https://github.com/EloyEMC/API-DISANO.git
    echo "   ✅ Remote configurado"
fi

# 10. Push
echo ""
echo "9. Haciendo push a GitHub..."
read -p "Branch principal (main/master) [main]: " branch
branch=${branch:-main}

git branch -M $branch
echo "   Haciendo push a origin/$branch..."
git push -u origin $branch

echo ""
echo "============================================"
echo "✅ PUSH COMPLETADO"
echo "============================================"
echo ""
echo "Repositorio: https://github.com/EloyEMC/API-DISANO"
echo ""
