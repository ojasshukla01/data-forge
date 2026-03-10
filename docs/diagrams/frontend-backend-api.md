# Frontend–backend–API interaction

```mermaid
sequenceDiagram
  participant U as User
  participant F as Frontend (Next.js)
  participant A as API (FastAPI)
  participant E as Engine / Task

  U->>F: Create run (wizard or Advanced)
  F->>A: POST /api/runs/generate
  A->>E: Enqueue generation task
  A-->>F: run_id
  F->>F: Redirect to /runs/:id

  loop Poll or fetch
    F->>A: GET /api/runs/:id
    A-->>F: status, timeline, summary
    F->>U: Show progress / result
  end

  U->>F: Compare runs
  F->>A: GET /api/runs/compare?left=&right=
  A-->>F: diff payload
  F->>U: Side-by-side diff + raw JSON

  U->>F: Run from scenario
  F->>A: POST /api/scenarios/:id/run
  A->>E: Enqueue with scenario config
  A-->>F: run_id
```

The frontend is stateless; all run and scenario state lives in the backend. Long-running runs are observed by polling the run endpoint until status is terminal (succeeded/failed/cancelled).
