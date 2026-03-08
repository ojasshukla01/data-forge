"""Bronze / Silver / Gold layer transformations."""

import re
from typing import Any


def bronze_to_silver(
    table_data: dict[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    """
    Clean bronze data: trim whitespace, normalize types, deduplicate by PK-like first col.
    """
    result: dict[str, list[dict[str, Any]]] = {}
    for table_name, rows in table_data.items():
        cleaned = []
        seen_pks: set[Any] = set()
        pk_col = list(rows[0].keys())[0] if rows else None

        for row in rows:
            r = {}
            for k, v in row.items():
                if isinstance(v, str):
                    v = v.strip()
                    if not v and k != pk_col:
                        v = None
                elif v == "":
                    v = None
                r[k] = v

            if pk_col and r.get(pk_col) in seen_pks:
                continue
            if pk_col and r.get(pk_col) is not None:
                seen_pks.add(r[pk_col])
            cleaned.append(r)

        result[table_name] = cleaned
    return result


def silver_to_gold(
    table_data: dict[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    """
    Curate silver for analytics: ensure high quality, fix remaining issues.
    """
    result: dict[str, list[dict[str, Any]]] = {}
    for table_name, rows in table_data.items():
        curated = []
        for row in rows:
            r = {}
            for k, v in row.items():
                if isinstance(v, str):
                    v = _normalize_string(v)
                r[k] = v
            curated.append(r)
        result[table_name] = curated
    return result


def _normalize_string(s: str) -> str:
    """Normalize string: trim, collapse internal whitespace, fix empty."""
    if not isinstance(s, str):
        return str(s) if s is not None else ""
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s


def transform_to_layer(
    table_data: dict[str, list[dict[str, Any]]],
    layer: str,
) -> dict[str, list[dict[str, Any]]]:
    """Transform bronze to requested layer."""
    if layer == "bronze":
        return table_data
    silver = bronze_to_silver(table_data)
    if layer == "silver":
        return silver
    return silver_to_gold(silver)
