#!/bin/bash
# Fix .env file with correct API key

cat > /var/www/API-DISANO/.env << 'ENDENV'
# Production Configuration
ENVIRONMENT=production
API_HOST=127.0.0.1
API_PORT=8000

# API Keys (separadas por comas si hay multiples)
API_KEYS=WteK08mCLiY8VY8v17n8YO_HNOfJZ1IhH-gDm6rKmBI

# Rate Limiting
RATE_LIMIT_PER_MINUTE=30

# CORS (solo dominios autorizados)
CORS_ORIGINS=https://eloymartinezcuesta.com,https://disano.eloymartinezcuesta.com

# Database
DATABASE_PATH=database/tarifa_disano.db
ENDENV

echo ".env file updated"
cat /var/www/API-DISANO/.env

# Restart service
systemctl restart api-disano
sleep 3
systemctl status api-disano --no-pager -n 10
