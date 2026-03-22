# Deployment

This document covers deployment options for Data Forge: local Docker Compose, production considerations, and cloud deployment guidance.

## Local Docker Compose

The default `docker-compose.yml` provides a reproducible local baseline:

```bash
docker compose up --build
```

- **API:** http://localhost:8000
- **Frontend:** http://localhost:3001
- **Storage:** File backend; data in `./output`, `./runs`, `./scenarios`, `./custom_schemas`

Optional Postgres for adapter workflows:

```bash
docker compose --profile db up --build
```

## Production Considerations

### Environment Variables

For a full list of backend and frontend env vars, see [env.md](env.md).

| Variable | Description | Default |
|----------|-------------|---------|
| `DATA_FORGE_PROJECT_ROOT` | Project root for paths | `.` |
| `DATA_FORGE_OUTPUT_DIR` | Output directory for artifacts | `output` |
| `DATA_FORGE_STORAGE_BACKEND` | `file` or `sqlite` | `file` |
| `DATA_FORGE_CORS_ALLOW_ORIGINS` | Comma-separated allowed origins | `http://localhost:3000,http://127.0.0.1:3000` |
| `NEXT_PUBLIC_API_URL` | API URL used by frontend (browser) | `http://localhost:8000` |
| `DATA_FORGE_STRUCTURED_LOGS` | Emit JSON logs when `1`/`true` | unset |
| `DATA_FORGE_RUNS_RETENTION_COUNT` | Max run records to keep | varies |
| `DATA_FORGE_RUNS_RETENTION_DAYS` | Max age in days for runs | varies |

### CORS and API URL

For production, set:

- **Backend:** `DATA_FORGE_CORS_ALLOW_ORIGINS` to your frontend origin(s), e.g. `https://app.example.com`
- **Frontend:** `NEXT_PUBLIC_API_URL` to your API URL, e.g. `https://api.example.com`

The frontend uses `NEXT_PUBLIC_API_URL` for all API calls. Ensure the API is reachable from the browser (same-origin or CORS).

### Volumes and Persistence

For production, mount persistent volumes for:

- `output/` — Generated artifacts
- `runs/` — Run metadata (file backend)
- `scenarios/` — Scenario configs (file backend)
- `custom_schemas/` — Custom schema definitions

With `DATA_FORGE_STORAGE_BACKEND=sqlite`, run metadata is stored in SQLite; ensure the DB file path is persisted.

### Health Checks

- **API:** `GET /health` and `GET /health/ready`
- **Frontend:** Root URL returns 200 when serving

Use these for load balancer health checks and orchestration readiness probes.

### Metrics (Optional)

Install the metrics extra and expose `/metrics` for Prometheus:

```bash
pip install -e ".[metrics]"
```

Configure Prometheus to scrape `http://<api-host>:8000/metrics`.

## Cloud Deployment

Cloud deployment is not yet a first-class supported path. The following is guidance for self-hosted deployment.

### General Pattern

1. **Build** the API and frontend images (or use pre-built images if available).
2. **Configure** environment variables for your domain and storage.
3. **Deploy** API and frontend behind a reverse proxy (nginx, Traefik, etc.).
4. **Persist** volumes for output, runs, scenarios, and custom schemas.

### Reverse Proxy

Place nginx (or similar) in front of API and frontend:

- `/api/*` — API backend
- `/` — Frontend (Next.js)
- Optional: `/metrics` — API (for Prometheus scrape)

### Example: Single-Host Deployment

```yaml
# docker-compose.prod.yml (conceptual)
services:
  api:
    image: data-forge-api:latest
    environment:
      DATA_FORGE_CORS_ALLOW_ORIGINS: https://your-domain.com
      DATA_FORGE_STRUCTURED_LOGS: "1"
    volumes:
      - data_output:/app/output
      - data_runs:/app/runs
      - data_scenarios:/app/scenarios
      - data_schemas:/app/custom_schemas

  frontend:
    image: data-forge-frontend:latest
    environment:
      NEXT_PUBLIC_API_URL: https://api.your-domain.com

volumes:
  data_output:
  data_runs:
  data_scenarios:
  data_schemas:
```

### Limitations

- **No built-in multi-tenancy** — Single-tenant by design.
- **No managed cloud services** — You manage compute, storage, and networking.
- **Local-first storage** — File or SQLite; no native S3/GCS for run metadata.
- **Scaling** — API is stateless except for in-memory rate limiting; frontend is static/SSR. Horizontal scaling of the API is possible with shared storage (e.g. NFS for file backend).

## See Also

- [ci-cd.md](ci-cd.md) — CI workflow and validation
- [observability-and-metrics.md](observability-and-metrics.md) — Metrics and logging
- [security.md](security.md) — Rate limiting, schema limits, path safety
