#!/usr/bin/env python3
"""Debug test admin API key"""

from fastapi.testclient import TestClient
from app.main import app
import os

# Configurar environment
os.environ["ADMIN_API_KEYS"] = "test-admin-key-1,test-admin-key-2"
os.environ["API_KEYS"] = "test-api-key-1,test-api-key-2"
os.environ["SECRET_KEY"] = "test-secret-key-32"

client = TestClient(app)

# Test 1: Sin API key
response = client.post(
    "/api/productos/",
    json={"codigo": "PROD-TEST", "descripcion": "Test", "pvp": 100.00},
)
print(f"Without API key - Status: {response.status_code}")

# Test 2: Con API key válida
response = client.post(
    "/api/productos/",
    json={"codigo": "PROD-TEST2", "descripcion": "Test", "pvp": 100.00},
    headers={"X-API-Key": "test-admin-key-1"},
)
print(f"With valid admin key - Status: {response.status_code}")
print(f"Response: {response.text[:200]}")

# Test 3: Verificar admin_api_keys
from app.config import Settings

settings = Settings(secret_key="test", api_keys=["test-api-key-1"])
print(f"ADMIN_API_KEYS: {settings.admin_api_keys}")
print(f"Contains test-admin-key-1: {'test-admin-key-1' in settings.admin_api_keys}")
