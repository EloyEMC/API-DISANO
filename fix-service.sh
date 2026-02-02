#!/bin/bash
# Fix systemd service type

sed -i 's/Type=notify/Type=simple/g' /etc/systemd/system/api-disano.service
systemctl daemon-reload
systemctl start api-disano
sleep 3
systemctl status api-disano --no-pager
