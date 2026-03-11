# Use cases

Why Data Forge exists and who it’s for.

---

## Data pipeline testing

- **Need:** Realistic data that matches your schema and relationships for integration tests, staging, and UAT.
- **Data Forge:** Use your SQL DDL, JSON Schema, or OpenAPI (or a domain pack), set scale and options, and generate FK-consistent data. Export to Parquet, CSV, SQL inserts, or load directly into SQLite, DuckDB, Postgres, Snowflake, or BigQuery. Optional anomaly injection and messiness profiles for edge-case testing.

---

## Warehouse benchmarking

- **Need:** Load tests and throughput metrics for your warehouse or database.
- **Data Forge:** Benchmark mode with scale presets (small → xlarge) and workload profiles (wide_table, high_cardinality, event_stream, fact_table). Run N iterations, get rows/second, generation/export duration, and memory estimates. Compare runs side-by-side to see impact of config changes.

---

## Synthetic analytics datasets

- **Need:** Demo or training datasets that look like production: consistent dates, sensible distributions, referential integrity.
- **Data Forge:** Domain packs (SaaS, e-commerce, fintech, healthcare, IoT, etc.) with business rules and time-aware generation. Control scale, seed for reproducibility, and export in the format your analytics stack expects.

---

## Pipeline replay and simulation

- **Need:** Event streams and pipeline snapshots for streaming, CDC, or event-driven pipelines.
- **Data Forge:** Pipeline simulation with event streams (order lifecycle, payments, logistics, IoT). Time patterns (steady, burst, seasonal, growth) and replay modes (ordered, shuffled, windowed). Full snapshot, incremental, and CDC modes with bronze/silver/gold layers and optional schema drift.

---

## Scenario-based reusable workflows

- **Need:** Reuse the same config across runs, teams, or environments without copying JSON by hand.
- **Data Forge:** Save configs as scenarios (name, category, tags). Run from the wizard or Advanced config; update in place or save as new. Import/export JSON. Link runs to scenarios (`source_scenario_id`) and create scenarios from runs. Example scenarios in `examples/scenarios/` for quick start, benchmark, and simulation.

---

## Validation and quality

- **Need:** Validate generated (or existing) data against schema and rules, or against golden manifests.
- **Data Forge:** Schema + rules validation, Great Expectations export and validation, manifest reconciliation (expected vs actual row counts). Privacy detection and redaction (warn/strict). Contract fixtures from OpenAPI for API testing.

---

## Summary

| Use case | Data Forge feature |
|----------|--------------------|
| Pipeline testing | Schema-driven generation, export/load, anomalies |
| Warehouse benchmarking | Benchmark mode, scale presets, workload profiles |
| Synthetic analytics | Domain packs, rules, time-aware, reproducible seed |
| Pipeline replay/simulation | Event streams, time patterns, replay modes, ETL modes |
| Reusable workflows | Scenarios, save/update/save-as-new, import/export |
| Validation & quality | Schema/GE/manifest validation, privacy, contracts |

For a step-by-step demo, see [demo-walkthrough.md](demo-walkthrough.md). For architecture, see [architecture-overview.md](architecture-overview.md).
