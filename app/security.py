"""
Security Module for API DISANO
Simple API Key authentication and rate limiting
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import os
from dotenv import load_dotenv
import time
from collections import defaultdict
from typing import Dict

# Load environment variables
load_dotenv()

# Configuration
API_KEYS = os.getenv("API_KEYS", "").split(",") if os.getenv("API_KEYS") else []
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Rate limiting storage (in production, use Redis)
rate_limit_store: Dict[str, list] = defaultdict(list)
RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware to validate API Key on every request"""

    # Paths that don't require API key
    EXEMPT_PATHS = {"/", "/health", "/docs", "/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next):
        # In development, skip API key check
        if ENVIRONMENT == "development":
            return await call_next(request)

        # Check if path is exempt
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Get API key from header
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "API Key is required. Use X-API-Key header."}
            )

        # Validate API key
        if api_key not in API_KEYS:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid API Key"}
            )

        # Continue with the request
        response = await call_next(request)
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware (30 requests per minute per API key)"""

    # Paths that don't require rate limiting
    EXEMPT_PATHS = {"/", "/health"}

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip rate limiting for exempt paths
        if path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Get API key (or use IP if no API key in development)
        client_id = request.headers.get("X-API-Key", request.client.host)

        # Clean old requests (older than 1 minute)
        current_time = time.time()
        minute_ago = current_time - 60

        # Filter out old requests
        rate_limit_store[client_id] = [
            req_time for req_time in rate_limit_store[client_id]
            if req_time > minute_ago
        ]

        # Check rate limit
        if len(rate_limit_store[client_id]) >= RATE_LIMIT:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded. Maximum {RATE_LIMIT} requests per minute.",
                    "limit": RATE_LIMIT,
                    "window": "1 minute"
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(RATE_LIMIT),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(current_time + 60))
                }
            )

        # Add current request
        rate_limit_store[client_id].append(current_time)

        # Continue with request
        response = await call_next(request)

        # Add rate limit headers
        remaining = RATE_LIMIT - len(rate_limit_store[client_id])
        response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + 60))

        return response


class UserAgentMiddleware(BaseHTTPMiddleware):
    """Block suspicious User-Agents"""

    BLOCKED_AGENTS = [
        "python-requests",
        "curl",
        "wget",
        "scraper",
        "crawler",
        "bot",
        "spider",
        "headless",
        "phantom",
        "selenium",
        "scrapy"
    ]

    async def dispatch(self, request: Request, call_next):
        user_agent = request.headers.get("user-agent", "").lower()

        # Check if user agent contains blocked patterns
        for blocked in self.BLOCKED_AGENTS:
            if blocked in user_agent:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Access denied. Suspicious User-Agent detected."}
                )

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Remove server header
        response.headers.pop("server", None)
        response.headers.pop("x-powered-by", None)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "no-referrer"

        # HSTS (only in production with HTTPS)
        if ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
