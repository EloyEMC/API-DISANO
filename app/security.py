"""
Security Module for API DISANO
Simple API Key authentication and rate limiting
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import os
import time
from collections import defaultdict
from typing import Dict

# Note: Don't use load_dotenv() - systemd passes env vars directly
# from dotenv import load_dotenv

# Rate limiting storage (in production, use Redis)
rate_limit_store: Dict[str, list] = defaultdict(list)

def get_api_keys():
    """Get API keys from environment"""
    keys = os.getenv("API_KEYS", "")
    if keys:
        return keys.split(",")
    return []

def get_environment():
    """Get environment from settings"""
    return os.getenv("ENVIRONMENT", "development")

def get_rate_limit():
    """Get rate limit from settings"""
    return int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))


def get_admin_keys():
    """Get admin API keys from environment"""
    keys = os.getenv("ADMIN_API_KEYS", "")
    if keys:
        return keys.split(",")
    return []


def verify_admin_api_key(request: Request) -> bool:
    """Verify if request has a valid admin API key"""
    if get_environment() == "development":
        return True

    admin_api_key = request.headers.get("X-Admin-API-Key")
    if not admin_api_key:
        return False

    valid_admin_keys = get_admin_keys()
    return admin_api_key in valid_admin_keys


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware to validate API Key on every request"""

    # Paths that don't require API key
    EXEMPT_PATHS = {"/", "/health", "/docs", "/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next):
        # In development, skip API key check
        if get_environment() == "development":
            return await call_next(request)

        # Check if path is exempt
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Get API keys from headers
        api_key = request.headers.get("X-API-Key")
        admin_api_key = request.headers.get("X-Admin-API-Key")

        # Check if we have at least one API key
        if not api_key and not admin_api_key:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "API Key is required. Use X-API-Key or X-Admin-API-Key header."}
            )

        # Validate regular API key if provided
        if api_key:
            valid_keys = get_api_keys()
            if api_key in valid_keys:
                return await call_next(request)

        # Validate admin API key if provided
        if admin_api_key:
            valid_admin_keys = get_admin_keys()
            if admin_api_key in valid_admin_keys:
                return await call_next(request)

        # If we get here, neither key was valid
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid API Key"}
        )


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
        rate_limit = get_rate_limit()
        if len(rate_limit_store[client_id]) >= rate_limit:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded. Maximum {rate_limit} requests per minute.",
                    "limit": rate_limit,
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
        remaining = rate_limit - len(rate_limit_store[client_id])
        response.headers["X-RateLimit-Limit"] = str(rate_limit)
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
        if "server" in response.headers:
            del response.headers["server"]
        if "x-powered-by" in response.headers:
            del response.headers["x-powered-by"]

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "no-referrer"

        # HSTS (only in production with HTTPS)
        if get_environment() == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
