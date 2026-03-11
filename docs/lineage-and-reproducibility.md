# Lineage and reproducibility

Data Forge records **lineage** (run → scenario → pack → artifacts) and writes **reproducibility manifests** for each run so you can reproduce or audit results.

## Lineage

- **What it is**: For a given run, lineage describes where the run came from (scenario, version, pack or custom schema) and where outputs went (artifact run id, output dir).
- **API**: `GET /api/runs/{run_id}/lineage` returns run_id, run_type, scenario_id, scenario (name, version), pack, custom_schema_id, custom_schema_version, schema_source_type (pack | custom_schema), artifact_run_id, output_dir.
- **Use cases**: Auditing, debugging (“which scenario produced this run?”), and linking runs to scenarios and packs.

## Reproducibility manifest

- **What it is**: A snapshot of run inputs and environment written when a run completes successfully.
- **Contents**: run_id, scenario_id, scenario_version, config (seed, pack or custom_schema_id/custom_schema_version, scale, mode, etc.), schema_source_type (pack | custom_schema), config_schema_version, total_rows_generated, duration_seconds, git_commit_sha, platform, python_version, timestamps. See `data_forge.models.run_manifest` for the full schema.
- **Where**: For each run, the task runner writes `manifest.json` and `manifest.md` under the run’s output directory (e.g. `output/<run_id>/manifest.json`).
- **API**: `GET /api/runs/{run_id}/manifest` returns the manifest (loaded from disk when present).
- **Use cases**: Reproducing a run with the same seed and config, compliance, and sharing exact run conditions.

## Manifest version

Manifests include a `manifest_version` field so future schema changes can be handled. Current version is 1.
