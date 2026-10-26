import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.config.settings import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds a small set of protective HTTP headers (a Helmet-like analogue)."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.headers.setdefault("X-XSS-Protection", "0")
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-process rate limiter.

    Note: state is per worker. For multi-worker deployments use a shared store
    (Redis) or a reverse proxy.
    """

    def __init__(self, app):
        super().__init__(app)
        self._hits: dict[tuple[str, str], deque[float]] = defaultdict(deque)

    async def dispatch(self, request, call_next):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        client = request.client.host if request.client else "unknown"
        path = request.url.path.rstrip("/")
        is_login = path.endswith("/auth/login") or path.endswith("/auth/google")
        bucket = "login" if is_login else "default"
        limit = settings.RATE_LIMIT_LOGIN if is_login else settings.RATE_LIMIT_DEFAULT

        now = time.monotonic()
        window = settings.RATE_LIMIT_WINDOW_SECONDS
        hits = self._hits[(client, bucket)]
        while hits and now - hits[0] > window:
            hits.popleft()

        if len(hits) >= limit:
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": "Too many requests, please slow down",
                        "details": [],
                    }
                },
            )
        hits.append(now)
        return await call_next(request)
