"""dbt-friendly export: seeds, sources.yml, schema_tests.yml."""

from pathlib import Path
from typing import Any

import csv


def export_dbt(
    table_data: dict[str, list[dict[str, Any]]],
    schema: "Any",
    output_dir: Path | str,
) -> dict[str, Any]:
    """
    Export tables as dbt seeds and generate sources.yml and schema_tests.yml.
    Returns report with seeds_generated, sources_file, schema_tests_file.
    """
    output_dir = Path(output_dir)
    seeds_dir = output_dir / "seeds"
    models_dir = output_dir / "models"
    seeds_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "enabled": True,
        "output_dir": str(output_dir),
        "seeds_generated": [],
        "sources_file": "",
        "schema_tests_file": "",
    }

    for table_name, rows in table_data.items():
        if not rows:
            continue
        path = seeds_dir / f"{table_name}.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            all_keys: set[str] = set()
            for r in rows:
                all_keys.update(r.keys())
            fieldnames = list(rows[0].keys()) + [k for k in sorted(all_keys) if k not in rows[0]]
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        report["seeds_generated"].append(path.name)

    sources_path = models_dir / "sources.yml"
    tables_list = [{"name": t} for t in table_data.keys() if table_data.get(t)]
    sources_yml = _render_sources_yml(tables_list)
    sources_path.write_text(sources_yml, encoding="utf-8")
    report["sources_file"] = str(sources_path)

    schema_tests_path = models_dir / "schema_tests.yml"
    tests_yml = _render_schema_tests_yml(schema, table_data)
    schema_tests_path.write_text(tests_yml, encoding="utf-8")
    report["schema_tests_file"] = str(schema_tests_path)

    return report


def _render_sources_yml(tables: list[dict[str, str]]) -> str:
    lines = [
        "version: 2",
        "",
        "sources:",
        "  - name: data_forge",
        "    tables:",
    ]
    for t in tables:
        lines.append(f"      - name: {t['name']}")
    return "\n".join(lines) + "\n"


def _render_schema_tests_yml(schema: "Any", table_data: dict[str, list[dict[str, Any]]]) -> str:
    lines = ["version: 2", "", "models:"]
    if not schema or not hasattr(schema, "tables"):
        return "\n".join(lines) + "\n"
    for table in schema.tables:
        if table.name not in table_data or not table_data[table.name]:
            continue
        lines.append(f"  - name: {table.name}")
        lines.append("    columns:")
        for col in table.columns:
            if col.primary_key:
                lines.append(f"      - name: {col.name}")
                lines.append("        tests:")
                lines.append("          - not_null")
                lines.append("          - unique")
    return "\n".join(lines) + "\n"
