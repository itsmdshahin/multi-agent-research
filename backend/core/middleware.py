"""
Rate limiting middleware using Redis sliding-window counters.
Applies per-IP rate limits to all API endpoints.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import settings
from core.logging import get_logger
from memory.redis_memory import get_redis

logger = get_logger(__name__)

# Paths that bypass rate limiting (health checks, static)
EXEMPT_PATHS = {"/health", "/health/detailed", "/docs", "/redoc", "/openapi.json"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window rate limiter: limits requests per IP per time window.
    Stores counters in Redis with automatic expiry.
    """

    def __init__(
        self,
        app,
        max_requests: int = settings.RATE_LIMIT_REQUESTS,
        window_seconds: int = settings.RATE_LIMIT_PERIOD,
    ):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next):
        # Skip exempt paths
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        # Get client IP
        forwarded = request.headers.get("X-Forwarded-For")
        ip = forwarded.split(",")[0].strip() if forwarded else request.client.host if request.client else "unknown"

        try:
            redis = await get_redis()
            key = f"ratelimit:{ip}:{request.url.path.split('/')[1]}"
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, self.window_seconds)

            # Set rate limit headers on every response
            remaining = max(0, self.max_requests - count)
            ttl = await redis.ttl(key)

            if count > self.max_requests:
                logger.warning("Rate limit exceeded", ip=ip, path=request.url.path, count=count)
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds}s.",
                        "retry_after": ttl,
                    },
                    headers={
                        "X-RateLimit-Limit": str(self.max_requests),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(ttl),
                        "Retry-After": str(ttl),
                    },
                )
        except Exception as e:
            # Don't block requests if Redis is down
            logger.warning("Rate limiter Redis error, allowing request", error=str(e))

        response = await call_next(request)

        try:
            response.headers["X-RateLimit-Limit"] = str(self.max_requests)
            response.headers["X-RateLimit-Remaining"] = str(remaining)  # type: ignore[possibly-undefined]
        except Exception:
            pass

        return response
