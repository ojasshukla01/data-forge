"""Prometheus metrics endpoint. Requires [metrics] extra: pip install -e '.[metrics]'."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter(tags=["metrics"])

# Lazy-init metrics when prometheus_client is available
_request_count: Any = None
_request_duration: Any = None
_metrics_init_failed = False


def _init_metrics() -> bool:
    """Initialize Prometheus metrics. Returns True if available."""
    global _request_count, _request_duration, _metrics_init_failed
    if _metrics_init_failed:
        return False
    if _request_count is not None and _request_duration is not None:
        return True
    try:
        from prometheus_client import Counter, Histogram
        _request_count = Counter(
            "data_forge_http_requests_total",
            "Total HTTP requests",
            ["method", "path", "status"],
        )
        _request_duration = Histogram(
            "data_forge_http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "path"],
        )
        return True
    except ImportError:
        _metrics_init_failed = True
        _request_count = None
        _request_duration = None
        return False


def record_request(method: str, path: str, status: int, duration_seconds: float) -> None:
    """Record a request for Prometheus (no-op if metrics not available)."""
    if _init_metrics() and _request_count and _request_duration:
        _request_count.labels(method=method, path=path, status=str(status)).inc()
        _request_duration.labels(method=method, path=path).observe(duration_seconds)


def _get_metrics_content() -> str | None:
    """Return Prometheus metrics text if prometheus_client is available."""
    try:
        from prometheus_client import generate_latest
        return str(generate_latest().decode("utf-8"))
    except ImportError:
        return None


@router.get("/metrics", response_class=PlainTextResponse)
def metrics() -> PlainTextResponse:
    """
    Prometheus metrics endpoint.
    Install with: pip install -e '.[metrics]' or pip install prometheus-client
    """
    content = _get_metrics_content()
    if content is None:
        return PlainTextResponse(
            "# Prometheus metrics not available. Install: pip install -e '.[metrics]'\n",
            status_code=200,
        )
    return PlainTextResponse(content, media_type="text/plain; charset=utf-8")
