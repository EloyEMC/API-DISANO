#!/usr/bin/env python3
"""Debug verify_admin_api_key"""

from app.security.api_key import verify_admin_api_key
import os

# Configurar environment
os.environ["ADMIN_API_KEYS"] = "test-admin-key-1,test-admin-key-2"
os.environ["API_KEYS"] = "test-api-key-1,test-api-key-2"
os.environ["SECRET_KEY"] = "test-secret-key-32"

# Crear request mock
from unittest.mock import Mock

request = Mock()
request.headers = {"X-API-Key": "test-admin-key-1"}

# Debug verify_admin_api_key
print(f"Request headers: {request.headers}")
print(f"X-API-Key: {request.headers.get('X-API-Key')}")


# Test
async def test_verify():
    result = await verify_admin_api_key(request)
    print(f"Result: {result}")


import asyncio

asyncio.run(test_verify())

# Debug admin_api_keys
from app.config import Settings

settings = Settings(secret_key="test", api_keys=["test-api-key-1"])
print(f"ADMIN_API_KEYS from Settings: {settings.admin_api_keys}")
