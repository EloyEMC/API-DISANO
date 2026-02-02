#!/bin/bash
# Test API key validation locally

API_KEY="yg22e0mHH8y08vesvL5za1Sg81q3b7NTpuitRtWe2bs"

cd /var/www/API-DISANO
source venv/bin/activate

python3 << PYEOF
import os
os.environ["API_KEYS"] = "$API_KEY"
os.environ["ENVIRONMENT"] = "production"

# Import the security module
from app.security import get_api_keys

keys = get_api_keys()
print(f"API_KEYS from env: {repr(keys)}")
print(f"Type: {type(keys)}")
print(f"Length: {len(keys)}")
if keys:
    print(f"First key: {repr(keys[0])}")
    print(f"First key length: {len(keys[0])}")

test_key = "$API_KEY"
print(f"\nTest key: {repr(test_key)}")
print(f"Test key length: {len(test_key)}")
print(f"Test key in keys: {test_key in keys}")

# Check character by character
if keys:
    for i, (c1, c2) in enumerate(zip(test_key, keys[0])):
        if c1 != c2:
            print(f"Diff at position {i}: {repr(c1)} != {repr(c2)}")
PYEOF
