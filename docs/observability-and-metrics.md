# Observability and metrics

Lightweight, local-friendly observability: run timeline, stage durations, aggregate metrics, Prometheus metrics, and structured logging. No distributed tracing or external APM.

## Prometheus metrics

When the optional `prometheus-client` dependency is installed (`pip install -e '.[metrics]'`), the API exposes a Prometheus scrape endpoint:

- **GET /metrics** — Returns Prometheus text format with request counters and latency histograms.

Metrics include:
- `http_requests_total` — Counter by method, path, status
- `http_request_duration_seconds` — Histogram of request latency

The middleware records each request automatically. If `prometheus-client` is not installed, `/metrics` returns a short message instead of metrics.

## Structured logging

Set `DATA_FORGE_STRUCTURED_LOGS=1` (or `true`/`yes`) to emit JSON logs for each request:

```json
{"message": "request_completed", "level": "info", "method": "GET", "path": "/api/runs", "status_code": 200, "duration_ms": 12.5}
```

Useful for log aggregation (e.g. Datadog, ELK) and production debugging.

## Run timeline

Each run has **stage_progress**: a list of stages (preflight, schema_load, generation, export, etc.) with status, started_at, finished_at, and duration_seconds. The API exposes a structured **timeline** for a run.

### GET /api/runs/{run_id}/timeline

Returns:

- **stages**: List of stages that have duration_seconds (completed/failed only), with name, duration_seconds, status, message.
- **stage_progress_full**: Full stage list as stored (including pending/skipped).
- **events**: Log events (level, message, ts).
- **total_duration_seconds**, **started_at**, **finished_at**.
- **slowest_stage**, **slowest_stage_duration_seconds**: Which stage took the longest.
- **why_slow_hint**: Human-readable hint, e.g. "generation took 80% of total time (12s)".
- **error_message**: If the run failed.

Use this for run detail UIs: show a stage timeline and a “Why slow?” hint when one stage dominates.

## Metrics summary

### GET /api/runs/metrics?limit=500

Aggregates from the run store and storage (no background daemon). Returns:

- **total_runs**: Count of runs (up to limit).
- **runs_by_type**: e.g. `{"generate": 90, "benchmark": 10}`.
- **runs_by_status**: e.g. `{"succeeded": 85, "failed": 5, "queued": 2}`.
- **average_duration_seconds**: Mean of run duration_seconds (completed runs).
- **total_rows_generated**: Sum of result_summary.total_rows (or total_rows_generated/rows_generated).
- **artifact_count**, **storage_mb**: From storage summary.
- **cleanup_candidates_count**: Number of runs that would be removed by retention cleanup (dry-run).
- **failure_categories**: Counts by error message prefix (first 80 chars), for failure analysis.

Use this for a dashboard or “Performance summary” card (e.g. on the Runs page).

## Frontend

- **Run detail page**: “Stage Timeline” shows each stage with status and duration; a “Why slow?” hint appears when one stage is ≥50% of total time.
- **Runs page**: “Performance summary” card shows total runs, avg duration, total rows, and failed count from the metrics API.

## Stage list

Stages tracked in generation runs: preflight, schema_load, rule_load, generation, anomaly_injection, etl_transforms, export, contract_generation, warehouse_load, manifest, validation, complete. Benchmark runs may use a different set; timeline still returns whatever is in stage_progress.
