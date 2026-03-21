"""Load generated data into a database via adapters."""

import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

from data_forge.adapters.registry import get_adapter, AdapterNotSupportedError
from data_forge.models.schema import SchemaModel
from data_forge.models.generation import GenerationResult

logger = logging.getLogger(__name__)

# Retry config: max attempts, base delay (s), max delay (s)
RETRY_MAX_ATTEMPTS = 3
RETRY_BASE_DELAY = 1.0
RETRY_MAX_DELAY = 10.0
RETRYABLE_EXCEPTIONS = (ConnectionError, OSError, TimeoutError)


T = TypeVar("T")


def _retry_load_operation(operation_name: str, fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Retry a load operation with exponential backoff on transient failures."""
    last_exc: Exception | None = None
    for attempt in range(1, RETRY_MAX_ATTEMPTS + 1):
        try:
            return fn(*args, **kwargs)
        except RETRYABLE_EXCEPTIONS as e:
            last_exc = e
            if attempt == RETRY_MAX_ATTEMPTS:
                raise
            delay = min(RETRY_BASE_DELAY * (2 ** (attempt - 1)), RETRY_MAX_DELAY)
            logger.warning(
                "Retry %s attempt %d/%d after %s: %s. Sleeping %.2fs",
                operation_name,
                attempt,
                RETRY_MAX_ATTEMPTS,
                type(e).__name__,
                e,
                delay,
            )
            time.sleep(delay)
    raise last_exc  # type: ignore[misc]


def load_to_database(
    result: GenerationResult,
    schema: SchemaModel,
    load_target: str,
    db_uri: str,
    batch_size: int = 1000,
    load_params: dict[str, Any] | None = None,
    table_store: Any = None,
) -> dict[str, Any]:
    """
    Load generated tables into the target database.
    Returns warehouse_load report dict.

    When table_store is provided (e.g. from reduced_memory or spill backend), loads full data
    via iter_rows in batches instead of from result.tables (which may be truncated snapshots).
    """
    report: dict[str, Any] = {
        "target": load_target,
        "tables_loaded": 0,
        "row_counts": {},
        "success": False,
    }
    try:
        params = dict(load_params or {})
        adapter = get_adapter(load_target, db_uri or "", batch_size=batch_size, **params)
    except AdapterNotSupportedError as e:
        report["error"] = str(e)
        return report

    try:
        _retry_load_operation("connect", adapter.connect)
        _retry_load_operation("create_schema", adapter.create_schema, schema)
        _retry_load_operation("create_tables", adapter.create_tables, schema)
        t0 = time.perf_counter()
        if table_store is not None and hasattr(table_store, "iter_rows"):
            counts = {}
            for name in table_store.table_names():
                n = _retry_load_operation(
                    "load_table",
                    adapter.load_table_from_iter,
                    name,
                    table_store.iter_rows(name),
                    batch_size,
                )
                counts[name] = n
        else:
            counts = _retry_load_operation("load_tables", adapter.load_tables, result.tables)
        report["load_seconds"] = round(time.perf_counter() - t0, 4)
        validation = adapter.validate_load()
        adapter.close()

        report["tables_loaded"] = len(counts)
        report["row_counts"] = counts
        report["success"] = validation.get("success", True)
        if not validation.get("success"):
            report["validation"] = validation
            report["error"] = "Row count validation failed"
    except Exception as e:
        report["error"] = str(e)
        try:
            adapter.close()
        except Exception:
            pass
    return report
