#!/bin/bash
# Get the API key from .env file
API_KEY=$(grep API_KEYS /var/www/API-DISANO/.env | cut -d= -f2)

# Create service file without EnvironmentFile - pass vars directly
rm -f /tmp/api-disano.service

echo "[Unit]" >> /tmp/api-disano.service
echo "Description=API Disano" >> /tmp/api-disano.service
echo "After=network.target" >> /tmp/api-disano.service
echo "" >> /tmp/api-disano.service
echo "[Service]" >> /tmp/api-disano.service
echo "Type=simple" >> /tmp/api-disano.service
echo "User=www-data" >> /tmp/api-disano.service
echo "Group=www-data" >> /tmp/api-disano.service
echo "WorkingDirectory=/var/www/API-DISANO" >> /tmp/api-disano.service
echo "Environment=PATH=/var/www/API-DISANO/venv/bin" >> /tmp/api-disano.service
echo "Environment=ENVIRONMENT=production" >> /tmp/api-disano.service
echo "Environment=API_KEYS=$API_KEY" >> /tmp/api-disano.service
echo "Environment=RATE_LIMIT_PER_MINUTE=30" >> /tmp/api-disano.service
echo "Environment=CORS_ORIGINS=https://eloymartinezcuesta.com,https://disano.eloymartinezcuesta.com" >> /tmp/api-disano.service
echo "ExecStart=/var/www/API-DISANO/venv/bin/python3 /var/www/API-DISANO/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000" >> /tmp/api-disano.service
echo "Restart=always" >> /tmp/api-disano.service
echo "RestartSec=10" >> /tmp/api-disano.service
echo "" >> /tmp/api-disano.service
echo "[Install]" >> /tmp/api-disano.service
echo "WantedBy=multi-user.target" >> /tmp/api-disano.service

# Show content
cat /tmp/api-disano.service

# Copy to systemd
cp /tmp/api-disano.service /etc/systemd/system/api-disano.service

systemctl daemon-reload
systemctl restart api-disano
sleep 3
systemctl status api-disano --no-pager -n 15
