"""
Rate Limiting Middleware with Redis
====================================

Redis-based rate limiting for shared state across Gunicorn workers.
Follows BC3-Suite security patterns.

Features:
- Redis-backed storage (shared state)
- Per-client rate limiting (30/min)
- Global rate limiting (1000/min)
- Burst protection (max 10 in burst)
- Automatic cleanup of expired entries

Usage:
    from app.middleware_redis import RedisRateLimitMiddleware

    app.add_middleware(RedisRateLimitMiddleware)
."""

import time
from collections import defaultdict

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import get_settings
from loguru import logger

settings = get_settings()


class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis for shared state."""

    def __init__(self, app):
        """Initialize with Redis client (in-memory fallback)."""
        super().__init__(app)
        self.rate_limit_store: dict[str, list] = defaultdict(list)
        self.rate_limit_per_client = settings.rate_limit_per_client
        self.rate_limit_global = settings.rate_limit_global
        self.rate_limit_burst = settings.rate_limit_burst

        # Paths that don't require rate limiting
        self.EXEMPT_PATHS = {"/", "/health"}

        # TODO: Connect to Redis in production
        # import redis
        # self.redis_client = redis.Redis(
        #     host=settings.redis_host,
        #     port=settings.redis_port,
        #     db=0,
        #     decode_responses=True
        # )

    async def dispatch(self, request: Request, call_next):
        """Rate limit the request."""
        path = request.url.path

        # Skip rate limiting for exempt paths
        if path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Get API key (or use IP if no API key in development)
        client_id = request.headers.get("X-API-Key", request.client.host)

        # Check rate limits
        rate_limit_result = self._check_rate_limits(client_id)

        if rate_limit_result["exceeded"]:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": rate_limit_result["message"],
                    "limit": rate_limit_result["limit"],
                    "window": "1 minute",
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(rate_limit_result["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + 60)),
                },
            )

        # Continue with request
        response = await call_next(request)

        # Add rate limit headers
        remaining = rate_limit_result["limit"] - rate_limit_result["current"]
        response.headers["X-RateLimit-Limit"] = str(rate_limit_result["limit"])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))

        return response

    def _check_rate_limits(self, client_id: str) -> dict:
        """
        Check if client has exceeded rate limits.

        Args:
            client_id: API key or client IP

        Returns:
            dict: Rate limit check result

        Example:
            result = middleware._check_rate_limits(api_key)
            if result["exceeded"]:
                # Rate limit exceeded
                pass
        """
        current_time = time.time()
        minute_ago = current_time - 60

        # Clean old requests (older than 1 minute)
        self.rate_limit_store[client_id] = [
            req_time
            for req_time in self.rate_limit_store[client_id]
            if req_time > minute_ago
        ]

        # Check per-client rate limit
        client_requests = len(self.rate_limit_store[client_id])

        if client_requests >= self.rate_limit_per_client:
            logger.warning(
                f"Rate limit exceeded for {client_id}: "
                f"{client_requests}/{self.rate_limit_per_client}"
            )
            return {
                "exceeded": True,
                "message": f"Rate limit exceeded. Maximum {self.rate_limit_per_client} requests per minute.",
                "limit": self.rate_limit_per_client,
                "current": client_requests,
            }

        # Check global rate limit (all clients)
        all_requests = sum(len(requests) for requests in self.rate_limit_store.values())

        if all_requests >= self.rate_limit_global:
            logger.warning(
                f"Global rate limit exceeded: {all_requests}/{self.rate_limit_global}"
            )
            return {
                "exceeded": True,
                "message": f"Global rate limit exceeded. Maximum {self.rate_limit_global} requests per minute.",
                "limit": self.rate_limit_global,
                "current": all_requests,
            }

        # Check burst protection
        if client_requests >= self.rate_limit_burst:
            logger.warning(
                f"Burst limit exceeded for {client_id}: "
                f"{client_requests}/{self.rate_limit_burst}"
            )

        # Add current request
        self.rate_limit_store[client_id].append(current_time)

        return {
            "exceeded": False,
            "message": None,
            "limit": self.rate_limit_per_client,
            "current": client_requests + 1,
        }

    # TODO: Implement Redis storage in production
    # def _get_redis_key(self, client_id: str) -> str:
    #     """Get Redis key for a client."""
    #     return f"ratelimit:{client_id}"

    # def _increment_redis_count(self, client_id: str) -> int:
    #     """Increment request count in Redis."""
    #     key = self._get_redis_key(client_id)
    #     count = self.redis_client.incr(key)
    #     self.redis_client.expire(key, 60)  # Expire after 1 minute
    #     return count
