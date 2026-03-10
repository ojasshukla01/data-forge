# Service layer

Routers and background tasks use **services** instead of talking to storage or engine directly. This keeps controllers thin and centralizes orchestration.

## Services

- **RunService** (via `data_forge.services.run_service`): `create_run`, `get_run`, `update_run`, `list_runs`, `append_event`, `run_cleanup`. All delegate to the configured run store (file or SQLite) via `get_run_store()`.
- **ScenarioService** (via `data_forge.services.scenario_service`): `create_scenario`, `get_scenario`, `update_scenario`, `delete_scenario`, `list_scenarios`, `get_masked_field_names`. Delegate to `get_scenario_store()`.
- **RetentionService** (via `data_forge.services.retention_service`): `preview_cleanup`, `execute_cleanup`, `archive_run`, `unarchive_run`, `delete_run`, `pin_run`, `unpin_run`, `get_storage_usage`. Uses the run store and scans `output/` for sizes.

## Usage

- **API routers** (`api/routers/runs.py`, `scenarios.py`, `artifacts.py`, `benchmark.py`) import from `data_forge.services` (e.g. `create_run`, `get_run`, `list_runs`, `create_scenario`, …) instead of `api.run_store` / `api.scenario_store`.
- **Background task runner** (`api/task_runner.py`) uses `get_run_store()` for run updates and `RunConfig.from_flat_dict(config)` so legacy and nested configs are normalized before calling the engine.

## Config normalization

- When starting a run (sync or async), config is normalized with `RunConfig.from_flat_dict(config)`; the engine receives `run_config.to_flat_dict()` so old scenario JSONs and flat API payloads keep working.
- When creating or updating a scenario, config is normalized with `_normalize_scenario_config()` so `config_schema_version` is set for export/import round-trip.

## Storage abstraction

Services do not import `run_store` or `scenario_store` directly. They use `get_run_store()` and `get_scenario_store()` from `data_forge.storage`, so the backend (file vs SQLite) is chosen by settings (`DATA_FORGE_STORAGE_BACKEND`).
