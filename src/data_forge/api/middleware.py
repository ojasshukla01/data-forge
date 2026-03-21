"""API middleware: request logging, rate limiting, request size limits."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("data_forge.api")


def _structured_log(level: str, msg: str, **kwargs: object) -> None:
    """Emit structured log as JSON when DATA_FORGE_STRUCTURED_LOGS=1."""
    if _use_structured_logs():
        payload = {"message": msg, "level": level, **{k: v for k, v in kwargs.items() if v is not None}}
        getattr(logger, level)(json.dumps(payload, default=str))
    else:
        parts = [f"{k}={v}" for k, v in kwargs.items() if v is not None]
        getattr(logger, level)("%s %s", msg, " ".join(parts) if parts else "")


def _use_structured_logs() -> bool:
    import os

    return os.getenv("DATA_FORGE_STRUCTURED_LOGS", "").lower() in ("1", "true", "yes")

# Max request body size (bytes) for JSON endpoints
MAX_REQUEST_SIZE = 2 * 1024 * 1024  # 2MB

# Rate limit: requests per minute per IP (in-memory, resets on restart)
RATE_LIMIT_GET = 300  # GET/HEAD: 300/min
RATE_LIMIT_MUTATE = 60  # POST/PUT/PATCH/DELETE: 60/min

RequestResponseHandler = Callable[[Request], Awaitable[Response]]

# In-memory rate limit state: {ip: [(ts, count), ...]} - simplified fixed window per minute
_rate_limit_lock = asyncio.Lock()
_rate_limit_counts: dict[str, tuple[float, int, int]] = {}  # ip -> (window_start, get_count, mutate_count)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log request method, path, duration. Use structured JSON when DATA_FORGE_STRUCTURED_LOGS=1."""

    async def dispatch(self, request: Request, call_next: RequestResponseHandler) -> Response:
        start = time.time()
        response = await call_next(request)
        duration_sec = time.time() - start
        duration_ms = round(duration_sec * 1000, 2)
        _structured_log(
            "info",
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        try:
            from data_forge.api.routers.metrics import record_request
            record_request(request.method, request.url.path, response.status_code, duration_sec)
        except ImportError:
            pass
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests with Content-Length exceeding MAX_REQUEST_SIZE."""

    async def dispatch(self, request: Request, call_next: RequestResponseHandler) -> Response:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > MAX_REQUEST_SIZE:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": "Request body too large",
                            "code": "payload_too_large",
                            "max_size_bytes": MAX_REQUEST_SIZE,
                        },
                    )
            except ValueError:
                pass
        return await call_next(request)


def _get_client_ip(request: Request) -> str:
    """Extract client IP from request headers or fallback to direct connection."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = request.scope.get("client")
    if client:
        host = client[0]
        return str(host)
    return "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    In-memory rate limiting per IP.
    GET/HEAD: 300/min, POST/PUT/PATCH/DELETE: 60/min.
    Returns 429 when exceeded.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseHandler) -> Response:
        ip = _get_client_ip(request)
        method = request.method.upper()
        is_mutate = method in ("POST", "PUT", "PATCH", "DELETE")
        limit = RATE_LIMIT_MUTATE if is_mutate else RATE_LIMIT_GET

        now = time.time()
        window_minute = int(now // 60)

        async with _rate_limit_lock:
            if ip not in _rate_limit_counts:
                _rate_limit_counts[ip] = (window_minute, 0, 0)
            win_start, get_cnt, mut_cnt = _rate_limit_counts[ip]
            if win_start != window_minute:
                win_start = window_minute
                get_cnt = 0
                mut_cnt = 0
            if is_mutate:
                mut_cnt += 1
                count = mut_cnt
            else:
                get_cnt += 1
                count = get_cnt
            _rate_limit_counts[ip] = (win_start, get_cnt, mut_cnt)

        if count > limit:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "code": "rate_limit_exceeded",
                    "retry_after_seconds": 60,
                },
            )
        return await call_next(request)
