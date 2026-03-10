"""Source-system messiness profiles for bronze generation."""

import random
import re
from typing import Any

from data_forge.models.generation import MessinessProfile


def apply_messiness(
    table_data: dict[str, list[dict[str, Any]]],
    profile: MessinessProfile,
    seed: int,
) -> dict[str, list[dict[str, Any]]]:
    """
    Apply messiness profile to bronze data. Deterministic from seed.
    clean: minimal changes
    realistic: common real-world issues
    chaotic: heavy source issues
    """
    if profile == MessinessProfile.CLEAN:
        return table_data

    rng = random.Random(seed)
    intensity = {"realistic": 0.15, "chaotic": 0.4}[profile.value]

    for _table_name, rows in table_data.items():
        n = len(rows)
        if n == 0:
            continue
        k = max(1, int(n * intensity))
        indices = set(rng.sample(range(n), min(k, n)))

        for i in indices:
            row = rows[i]
            r = rng.random()

            if r < 0.25:
                _whitespace_pollute(row, rng)
            elif r < 0.4:
                _inconsistent_casing(row, rng)
            elif r < 0.5 and profile == MessinessProfile.CHAOTIC:
                _numeric_as_string(row, rng)
            elif r < 0.65:
                _date_format_inconsistency(row, rng)
            elif r < 0.8 and profile == MessinessProfile.CHAOTIC:
                _enum_spelling_drift(row, rng)

    return table_data


def _whitespace_pollute(row: dict[str, Any], rng: random.Random) -> None:
    """Add leading/trailing whitespace to string fields."""
    for k, v in list(row.items()):
        if isinstance(v, str) and v and rng.random() < 0.5:
            if rng.random() < 0.5:
                row[k] = "  " + v
            else:
                row[k] = v + "\t "


def _inconsistent_casing(row: dict[str, Any], rng: random.Random) -> None:
    """Randomly change casing in string fields."""
    for k, v in list(row.items()):
        if isinstance(v, str) and len(v) > 2 and rng.random() < 0.4:
            if rng.random() < 0.5:
                row[k] = v.lower()
            else:
                row[k] = v.upper()


def _numeric_as_string(row: dict[str, Any], rng: random.Random) -> None:
    """Serialize some numeric fields as strings."""
    for k, v in list(row.items()):
        if isinstance(v, (int, float)) and rng.random() < 0.5:
            row[k] = str(v)


def _date_format_inconsistency(row: dict[str, Any], rng: random.Random) -> None:
    """Vary date format (ISO vs slashes vs US format)."""
    for k, v in list(row.items()):
        if not isinstance(v, str):
            continue
        if re.match(r"\d{4}-\d{2}-\d{2}", str(v)) and rng.random() < 0.5:
            parts = str(v).split("T")[0].split("-")
            if len(parts) == 3:
                fmt = rng.choice(["slash", "us"])
                if fmt == "slash":
                    row[k] = f"{parts[1]}/{parts[2]}/{parts[0]}"
                else:
                    row[k] = f"{parts[1]}-{parts[2]}-{parts[0]}"


def _enum_spelling_drift(row: dict[str, Any], rng: random.Random) -> None:
    """Introduce minor enum spelling variations."""
    common = {"active": "Active", "pending": "PENDING", "canceled": "cancelled", "paid": "Paid"}
    for k, v in list(row.items()):
        if isinstance(v, str) and v.lower() in common and rng.random() < 0.5:
            row[k] = common[v.lower()]
