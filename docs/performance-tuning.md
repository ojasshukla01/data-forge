# Performance tuning and scaling

Guidance for scaling Data Forge generation and reducing latency.

## Generation performance

### Scale presets

| Preset | Approx rows | Use case |
|--------|-------------|----------|
| small | ~10k | Quick demos, unit tests |
| medium | ~100k | Integration tests |
| large | ~1M | UAT, pipeline testing |
| xlarge | ~10M | Load testing, benchmarks |

### Tips

1. **Use DuckDB** for local load when possible — faster than SQLite for bulk inserts.
2. **Reduce columns** — fewer columns per table speeds generation.
3. **Simplify relationships** — deep FK chains increase planning time.
4. **Disable optional features** — turn off anomaly injection, ETL layers, or simulation when not needed.
5. **Export format** — Parquet and DuckDB are typically faster than CSV for large datasets.

### Lower-memory execution

For large-scale runs that may hit memory limits:

- **`reduced_memory_mode`** — When enabled, uses spill-backed table storage (writes intermediate rows to temp files) instead of in-memory. Set via Advanced Config or API: `reduced_memory_mode: true`.
- **`table_store_backend`** — Force `spill` to always use disk-backed storage; `auto` selects spill when planned rows ≥ 200k or when `reduced_memory_mode` is true.
- **Limitation:** The pipeline is not fully streaming end-to-end. Tables are still generated and materialized per-table; spill reduces peak memory but does not provide true row-by-row streaming. For very large schemas (e.g. 50+ tables, millions of rows), consider splitting into smaller runs.
- **Warehouse load:** When `load_target` is set, the engine passes the table store to `load_to_database`. Load streams from `iter_rows` in batches instead of truncated snapshots, so full data is loaded even in reduced_memory mode. See [adapter-maturity.md](adapter-maturity.md) for adapter capabilities.

## API and frontend

- **Run status** — Run detail page uses SSE (`/api/runs/{id}/stream`) when available for real-time updates; falls back to polling otherwise.
- **List limits and cursor** — `GET /api/runs?limit=50` and `GET /api/scenarios?limit=50` reduce payload size. Use `cursor` and `next_cursor` for efficient pagination of large lists.
- **Structured logs** — `DATA_FORGE_STRUCTURED_LOGS=1` adds minimal overhead; useful for production debugging.

## Benchmark mode

Use `POST /api/runs/benchmark` or `data-forge benchmark` to measure throughput (rows/s) and duration for a given pack and scale. Compare before/after changes.

## Known limits

- **Schema body**: 512KB (see [security.md](security.md)).
- **Request body**: 2MB global.
- **Rate limits**: 300 GET/min, 60 mutate/min per IP.
- **File backend**: Large run counts (1000+) may slow list operations; consider SQLite backend for high volume.
