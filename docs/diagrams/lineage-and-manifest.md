# Lineage and reproducibility manifest

```mermaid
flowchart LR
  subgraph Run
    R[Run]
  end

  subgraph Scenario
    S[Scenario]
    V[Version history]
  end

  subgraph Pack
    P[Domain pack]
  end

  subgraph Output
    M[manifest.json / manifest.md]
    A[Artifacts]
  end

  R -->|source_scenario_id| S
  S --> V
  S -->|pack| P
  R -->|writes on success| M
  R -->|produces| A
```

- **Lineage**: Run → Scenario (optional) → Version → Pack → Artifacts. Exposed via `GET /api/runs/{id}/lineage` and shown on the run detail page.
- **Manifest**: Reproducibility snapshot (seed, config version, git SHA, platform) written to the run output dir and exposed via `GET /api/runs/{id}/manifest`. Shown on the run detail page under "Reproducibility manifest".
- **Scenario versioning**: Config changes create new versions; diff any two versions via API and the scenario detail "Version history" / "Compare versions" UI.
