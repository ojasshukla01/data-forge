"""CDC / incremental load simulation: metadata columns and change events."""

import random
from datetime import datetime, timedelta
from typing import Any

from data_forge.models.generation import GenerationMode


def apply_mode(
    table_data: dict[str, list[dict[str, Any]]],
    mode: GenerationMode,
    change_ratio: float,
    seed: int,
    batch_id: str | None,
) -> dict[str, list[dict[str, Any]]]:
    """
    Apply generation mode: add metadata columns (created_at, updated_at, batch_id)
    and for CDC add op_type with INSERT/UPDATE/DELETE. Deterministic from seed.
    """
    if mode == GenerationMode.FULL_SNAPSHOT:
        return table_data

    bid = batch_id or f"batch_{seed}"
    base_ts = datetime(2024, 1, 1)
    rng = random.Random(seed)

    for table_name, rows in list(table_data.items()):
        if not rows:
            continue
        n = len(rows)
        change_count = max(0, min(n, int(n * change_ratio))) if change_ratio > 0 else 0
        change_indices = set(rng.sample(range(n), change_count)) if change_count > 0 else set()

        result: list[dict[str, Any]] = []
        for i, row in enumerate(rows):
            r = dict(row)
            ts = base_ts + timedelta(seconds=seed + i * 17)
            r["created_at"] = ts.isoformat()
            r["updated_at"] = ts.isoformat()
            r["batch_id"] = bid

            if mode == GenerationMode.INCREMENTAL:
                if i in change_indices:
                    r["updated_at"] = (ts + timedelta(hours=1)).isoformat()

            elif mode == GenerationMode.CDC:
                # Deterministic op_type: ~70% INSERT, ~20% UPDATE, ~10% DELETE
                op_seed = rng.randint(0, 99) if i in change_indices else (i % 10)
                if op_seed < 70:
                    op = "INSERT"
                elif op_seed < 90:
                    op = "UPDATE"
                    r["updated_at"] = (ts + timedelta(hours=2)).isoformat()
                else:
                    op = "DELETE"
                    r["deleted_at"] = (ts + timedelta(hours=3)).isoformat()
                r["op_type"] = op

            result.append(r)

        table_data[table_name] = result

    return table_data
