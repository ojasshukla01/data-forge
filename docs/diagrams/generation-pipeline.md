# Generation pipeline flow

```mermaid
flowchart LR
  subgraph Input
    A[Config: pack / schema + rules]
    B[Scale, mode, layer]
    C[Options: anomalies, privacy, simulation]
  end

  subgraph Engine
    D[Preflight]
    E[Load schema & rules]
    F[Generate tables]
    G[Export]
    H[Optional: load DB, dbt/GE/Airflow]
  end

  A --> D
  B --> D
  C --> D
  D --> E
  E --> F
  F --> G
  G --> H
```

Stages in order: **Preflight** (validate config) → **Load schema & rules** (from pack or files) → **Generate** (tables in dependency order, FK resolution, drift/messiness/anomalies, simulation events) → **Export** (Parquet, CSV, JSON, SQL) → **Optional** (DB load, dbt/GE/Airflow export, manifest).
