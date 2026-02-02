#!/bin/bash
# Script para capturar el error de inicio en un archivo log

cd /var/www/API-DISANO
source venv/bin/activate

echo "Iniciando servidor y capturando output..."
echo "========================================" > /tmp/api-error.log
echo "Fecha: $(date)" >> /tmp/api-error.log
echo "========================================" >> /tmp/api-error.log

python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 >> /tmp/api-error.log 2>&1 &
PID=$!

echo "Servicio iniciado con PID: $PID"
echo "Esperando 5 segundos..."
sleep 5

echo "========================================"
echo "CONTENIDO DEL LOG:"
echo "========================================"
cat /tmp/api-error.log

echo ""
echo "========================================"
echo "El log completo está en: /tmp/api-error.log"
echo "========================================"

# Matar el proceso
kill $PID 2>/dev/null || true
