#!/bin/bash
# Final fix for service file - correct all paths with proper O

cat > /etc/systemd/system/api-disano.service << 'ENDSERVICE'
[Unit]
Description=API Disano
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/API-DISANO
Environment=PATH=/var/www/API-DISANO/venv/bin
EnvironmentFile=/var/www/API-DISANO/.env
ExecStart=/var/www/API-DISANO/venv/bin/python3 /var/www/API-DISANO/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
ENDSERVICE

echo "Service file created"
echo ""
cat /etc/systemd/system/api-disano.service
echo ""

systemctl daemon-reload
systemctl restart api-disano
sleep 3
systemctl status api-disano --no-pager -n 15
