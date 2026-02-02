#!/bin/bash
# Check what environment variables the running process sees

PID=$(pgrep -f "uvicorn app.main" | head -1)

if [ -z "$PID" ]; then
    echo "ERROR: No uvicorn process found"
    exit 1
fi

echo "Process PID: $PID"
echo ""
echo "Environment variables:"
echo "======================"

# Tricky: use cat /proc/PID/environ to see env vars
cat /proc/$PID/environ | tr '\0' '\n' | grep -E "API_KEYS|ENVIRONMENT|RATE_LIMIT" | sort

echo ""
echo "======================"
echo "If API_KEYS is empty or missing, that's the problem"
