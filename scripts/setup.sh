#!/bin/bash
# ==============================================================================
# Script de Configuración Inicial - API DISANO
# ==============================================================================
#
# Este script configura el entorno para ejecutar la API por primera vez.
#
# Uso:
#   bash scripts/setup.sh
#
# ==============================================================================

set -e

echo "============================================"
echo "CONFIGURACIÓN INICIAL - API DISANO"
echo "============================================"
echo ""

# 1. Crear virtual environment
echo "1. Creando virtual environment..."
if [ ! -d "venv" ]; then
	python3 -m venv venv
	echo "   ✅ Virtual environment creado"
else
	echo "   ℹ️  Virtual environment ya existe"
fi

# 2. Activar virtual environment
echo ""
echo "2. Activando virtual environment..."
source venv/bin/activate
echo "   ✅ Virtual environment activado"

# 3. Instalar dependencias
echo ""
echo "3. Instalando dependencias..."
pip install --upgrade pip -q
pip install -r requirements.txt
echo "   ✅ Dependencias instaladas"

# 4. Crear directorio de logs
echo ""
echo "4. Creando directorio de logs..."
mkdir -p logs
echo "   ✅ Directorio logs/ creado"

# 5. Verificar .env
echo ""
echo "5. Verificando configuración..."
if [ ! -f ".env" ]; then
	echo "   ⚠️  Archivo .env no encontrado"
	echo "   Creando .env con valores por defecto..."

	# Generar API key
	API_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

	cat >.env <<EOF
# Configuración generada automáticamente
ENVIRONMENT=development
API_HOST=127.0.0.1
API_PORT=8000
API_KEYS=$API_KEY
CORS_ORIGINS=*
LOG_LEVEL=INFO
DATABASE_PATH=database/tarifa_disano.db
EOF

	echo "   ✅ Archivo .env creado"
	echo "   🔐 API Key generada y guardada en el archivo .env protegido"
else
	echo "   ✅ Archivo .env ya existe"
fi

# 6. Verificar sintaxis
echo ""
echo "6. Verificando sintaxis de Python..."
python -m py_compile app/main.py app/config.py app/security/*.py
if [ $? -eq 0 ]; then
	echo "   ✅ Sintaxis correcta"
else
	echo "   ❌ Error de sintaxis"
	exit 1
fi

# 7. Resumen
echo ""
echo "============================================"
echo "✅ CONFIGURACIÓN COMPLETADA"
echo "============================================"
echo ""
echo "Para iniciar la API:"
echo ""
echo "  source venv/bin/activate"
echo "  python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
echo ""
echo "En otra terminal, para verificar seguridad:"
echo ""
echo "  export API_URL='http://127.0.0.1:8000'"
echo "  export API_KEY='tu-api-key'"
echo "  bash scripts/verify_security.sh"
echo ""
