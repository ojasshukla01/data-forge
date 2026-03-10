# Scenario versioning and diff

Scenarios track version history. Each update creates a new version; you can compare any two versions.

## Version history

- On **create**, a scenario gets `version: 1` and a single entry in `versions`.
- On **update** (when config changes), the current config is appended to `versions` and `version` is incremented.
- Up to the last 20 versions are kept (configurable via `MAX_VERSION_HISTORY` in scenario_store).

## API

- `GET /api/scenarios/{id}/versions` — List versions (version number, updated_at). Returns `current_version`.
- `GET /api/scenarios/{id}/versions/{version}` — Config snapshot for that version.
- `GET /api/scenarios/{id}/diff?left=1&right=2` — Compare two versions. Returns `changed`: list of `{ key, left, right }` for differing config paths.

## Export

`GET /api/scenarios/{id}/export` includes `version` and `updated_at` when present, so exported JSON can be re-imported with version info.

## Backend

- **File store**: `version` and `versions` (array of `{ version, config, updated_at }`) are stored in the scenario JSON.
- **SQLite**: Scenario record can be extended with version/versions columns; until then, versioning is effectively “current only” when using SQLite (service returns version 1 for existing records).
