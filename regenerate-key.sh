#!/bin/bash
# Regenerate API key using Python to avoid keyboard issues

cd /var/www/API-DISANO
source venv/bin/activate

# Generate new API key
NEW_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

echo "New API Key: $NEW_KEY"

# Update .env
cat > /var/www/API-DISANO/.env << ENDENV
ENVIRONMENT=production
API_HOST=127.0.0.1
API_PORT=8000
API_KEYS=$NEW_KEY
RATE_LIMIT_PER_MINUTE=30
CORS_ORIGINS=https://eloymartinezcuesta.com,https://disano.eloymartinezcuesta.com
DATABASE_PATH=database/tarifa_disano.db
ENDENV

echo ""
echo "API Key saved to .env"
echo ""
echo "Save this key:"
echo "$NEW_KEY"
echo ""

# Save to file
cat > /root/api-disano-key.txt << KEYEOF
API DISANO KEY
=============
Key: $NEW_KEY
Date: $(date)
KEYEOF

chmod 600 /root/api-disano-key.txt

# Restart service
systemctl restart api-disano
sleep 3
systemctl status api-disano --no-pager -n 10
