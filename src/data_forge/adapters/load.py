"""Load generated data into a database via adapters."""

import time
from typing import Any

from data_forge.adapters.registry import get_adapter, AdapterNotSupportedError
from data_forge.models.schema import SchemaModel
from data_forge.models.generation import GenerationResult, TableSnapshot


def load_to_database(
    result: GenerationResult,
    schema: SchemaModel,
    load_target: str,
    db_uri: str,
    batch_size: int = 1000,
    load_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Load generated tables into the target database.
    Returns warehouse_load report dict.
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
        adapter.connect()
        adapter.create_schema(schema)
        adapter.create_tables(schema)
        t0 = time.perf_counter()
        counts = adapter.load_tables(result.tables)
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
