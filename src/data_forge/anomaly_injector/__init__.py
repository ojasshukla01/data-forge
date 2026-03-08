"""Inject anomalies and edge cases: nulls, duplicates, bad encodings, invalid enums."""

import random
from typing import Any

__all__ = ["inject_anomalies", "AnomalyType"]


class AnomalyType:
    """Types of anomalies to inject."""

    NULL_FIELD = "null_field"
    DUPLICATE_ROW = "duplicate_row"
    INVALID_ENUM = "invalid_enum"
    MALFORMED_STRING = "malformed_string"
    OUT_OF_RANGE = "out_of_range"
    NEGATIVE_VALUE = "negative_value"
    EMPTY_STRING = "empty_string"
    WRONG_TYPE = "wrong_type"


def inject_anomalies(
    rows: list[dict[str, Any]],
    ratio: float = 0.02,
    seed: int = 42,
    anomaly_types: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Mutate a fraction of rows to introduce anomalies. ratio in (0, 1].
    Returns new list with anomalies applied (some rows may be duplicated for duplicate_row).
    """
    if ratio <= 0 or not rows:
        return list(rows)
    rng = random.Random(seed)
    types = anomaly_types or [
        AnomalyType.NULL_FIELD,
        AnomalyType.EMPTY_STRING,
        AnomalyType.INVALID_ENUM,
        AnomalyType.MALFORMED_STRING,
    ]
    result = [dict(r) for r in rows]
    n = len(result)
    k = max(1, int(n * ratio))
    indices = rng.sample(range(n), min(k, n))
    for i in indices:
        row = result[i]
        atype = rng.choice(types)
        if atype == AnomalyType.NULL_FIELD and row:
            key = rng.choice(list(row.keys()))
            row[key] = None
        elif atype == AnomalyType.EMPTY_STRING and row:
            string_columns = [k for k, v in row.items() if isinstance(v, str)]
            if string_columns:
                key = rng.choice(string_columns)
                row[key] = ""
        elif atype == AnomalyType.INVALID_ENUM and row:
            key = rng.choice(list(row.keys()))
            row[key] = "__INVALID__"
        elif atype == AnomalyType.MALFORMED_STRING and row:
            string_columns = [k for k, v in row.items() if isinstance(v, str)]
            if string_columns:
                key = rng.choice(string_columns)
                row[key] = "\x00\xff\xfe broken \u0000"
        elif atype == AnomalyType.DUPLICATE_ROW and result:
            result.append(dict(result[rng.randint(0, len(result) - 1)]))
    return result
