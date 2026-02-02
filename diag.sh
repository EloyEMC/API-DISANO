#!/bin/bash
cd /var/www/API-DISANO
source venv/bin/activate
python3 -c "print('Testing import...'); from app.main import app; print('SUCCESS')" 2>&1
