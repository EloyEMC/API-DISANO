#!/bin/bash
# Create service file line by line to avoid heredoc issues

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
echo "EnvironmentFile=/var/www/API-DISANO/.env" >> /tmp/api-disano.service
echo "ExecStart=/var/www/API-DISANO/venv/bin/python3 /var/www/API-DISANO/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000" >> /tmp/api-disano.service
echo "Restart=always" >> /tmp/api-disano.service
echo "RestartSec=10" >> /tmp/api-disano.service
echo "" >> /tmp/api-disano.service
echo "[Install]" >> /tmp/api-disano.service
echo "WantedBy=multi-user.target" >> /tmp/api-disano.service

# Show content
cat /tmp/api-disano.service

# Copy to systemd location
cp /tmp/api-disano.service /etc/systemd/system/api-disano.service

systemctl daemon-reload
systemctl restart api-disano
sleep 3
systemctl status api-disano --no-pager -n 15
