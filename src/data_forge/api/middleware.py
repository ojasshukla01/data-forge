"""API middleware: request logging, rate limiting placeholder, request size limits."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("data_forge.api")

# Max request body size (bytes) for JSON endpoints
MAX_REQUEST_SIZE = 2 * 1024 * 1024  # 2MB


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log request method, path, and duration."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start) * 1000
        logger.info(
            "%s %s %d %.1fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests with Content-Length exceeding MAX_REQUEST_SIZE."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
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


class RateLimitPlaceholderMiddleware(BaseHTTPMiddleware):
    """
    Placeholder for rate limiting. Does nothing by default.
    Replace with actual rate limiting (e.g. slowapi) when needed.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Placeholder: no rate limiting applied
        return await call_next(request)
