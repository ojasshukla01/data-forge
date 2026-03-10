# Retention and cleanup

Data Forge keeps run metadata (in `runs/` or SQLite) and artifact files (in `output/<run_id>/`). Retention and cleanup let you control how much to keep.

## Concepts

- **Run record**: Metadata for one execution (id, status, config summary, timestamps, pinned, archived_at).
- **Artifacts**: Files under `output/<run_id>/` (parquet, CSV, dbt seeds, GE, etc.).
- **Pinned run**: Excluded from retention cleanup; never auto-removed.
- **Archived run**: Hidden from the default runs list; still retained until cleanup (unless you also pin it).

## Retention policy

Configured via settings (or API/CLI parameters):

- **Retention count**: Keep the last N run records (default 100). Older runs beyond this are candidates for cleanup.
- **Retention days**: Optionally prune runs older than N days (default: disabled).
- Pinned runs are never removed. Optionally, archived runs can be excluded from cleanup.

Cleanup only removes **run records** by default. Optionally you can also delete artifact directories (`output/<run_id>/`) when running cleanup or when deleting a single run.

## API

- `GET /api/runs/storage/summary` — runs count, artifact count, total size, per-run breakdown.
- `GET /api/runs/cleanup/preview?retention_count=&retention_days=` — dry-run list of runs that would be removed.
- `POST /api/runs/cleanup/execute` — body: `{ "delete_artifacts": false, "retention_count": 100, "retention_days": null }`. Runs retention cleanup; returns `deleted_run_records`, `deleted_artifact_dirs`.
- `POST /api/runs/cleanup` — legacy: runs cleanup without deleting artifact dirs; returns `{ "deleted": n }`.
- `POST /api/runs/{run_id}/archive` — set `archived_at` (hide from default list).
- `POST /api/runs/{run_id}/unarchive` — clear archived.
- `POST /api/runs/{run_id}/pin` — set pinned (exclude from cleanup).
- `POST /api/runs/{run_id}/unpin` — clear pinned.
- `POST /api/runs/{run_id}/delete` — body: `{ "delete_artifacts": false }`. Permanently delete run record (and optionally its output dir).

## CLI

From the project root, use either the installed script or the module:

```bash
# If the package is installed (pip install -e .):
data-forge runs storage
data-forge runs cleanup-preview --count 10

# Without installing, run via Python module:
python -m data_forge.cli runs storage
python -m data_forge.cli runs cleanup-preview --count 10
```

Commands:

- `runs storage` — print storage usage.
- `runs cleanup-preview [--count N] [--days D]` — show cleanup candidates.
- `runs cleanup-execute [--count N] [--days D] [--delete-artifacts]` — run cleanup.
- `runs archive <run_id>`
- `runs unarchive <run_id>`
- `runs delete <run_id> [--delete-artifacts]`
- `runs pin <run_id>`
- `runs unpin <run_id>`

## List runs

- `GET /api/runs?include_archived=false` — default excludes archived runs. Set `include_archived=true` to see them.

## Storage backend

With **file** backend, run records are JSON files in `runs/`; delete run removes the file. With **SQLite** backend, delete run sets `deleted_at` (soft-delete). In both cases, artifact dirs are only removed when you pass `delete_artifacts: true` (or `--delete-artifacts`).

## Artifact metadata

The artifact metadata model (`ArtifactMetadata`) supports artifact_id, run_id, type, file_path, size, checksum, created_at, pinned, tags. Current UI and API still derive artifact lists from scanning `output/<run_id>/` and from run records’ `artifacts` array; a future step can persist artifact metadata in DB for retention by size/age per artifact.
