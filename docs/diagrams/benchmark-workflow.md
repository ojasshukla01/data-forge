# Benchmark workflow

```mermaid
flowchart TB
  A[User: pack, scale, iterations] --> B[Backend: create run]
  B --> C[Loop: generate + export]
  C --> D[Collect timings & row counts]
  D --> E[Compute throughput, duration, memory]
  E --> F[Update run result summary]
  F --> G[UI: run detail shows metrics]
```

Benchmark runs execute N iterations of generation and export (and optionally load). Results include generation seconds, export seconds, total rows, rows/second, and memory estimate. Scale presets (small → xlarge) and workload profiles (wide_table, high_cardinality, etc.) control the effective data volume and shape.
