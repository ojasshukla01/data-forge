# Run, scenario, and artifact relationships

```mermaid
flowchart TB
  subgraph Scenarios
    S1[Scenario A]
    S2[Scenario B]
  end

  subgraph Runs
    R1[Run 1]
    R2[Run 2]
    R3[Run 3]
  end

  subgraph Artifacts
    A1[Datasets, event streams, dbt, GE, ...]
  end

  S1 -->|run from scenario| R1
  S2 -->|run from scenario| R2
  R1 -->|produces| A1
  R2 -->|produces| A1
  R3 -->|produces| A1
  R3 -.->|optional: created from run| S2
```

- **Scenario** = saved config (name, category, tags, config blob). Can be created from scratch, from Advanced config, or from a run (clone).
- **Run** = one execution (generate or benchmark). May have `source_scenario_id` if started from a scenario.
- **Artifacts** = output files registered per run (path, type). One run can have many artifacts.
