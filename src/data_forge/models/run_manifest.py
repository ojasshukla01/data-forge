"""Run manifest and lineage for reproducibility."""

import platform
import time
from pathlib import Path
from typing import Any


def _git_sha(project_root: Path | None = None) -> str | None:
    """Return current git commit SHA if available."""
    try:
        import subprocess
        root = project_root or Path.cwd()
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=2,
        )
        if out.returncode == 0 and out.stdout:
            return out.stdout.strip()[:40]
    except Exception:
        pass
    return None


def build_run_manifest(
    run_id: str,
    run_type: str,
    config: dict[str, Any],
    *,
    scenario_id: str | None = None,
    scenario_version: int | None = None,
    output_run_id: str | None = None,
    total_rows: int | None = None,
    duration_seconds: float | None = None,
    storage_backend: str = "file",
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Build a reproducibility manifest for a run."""
    now = time.time()
    root = project_root or Path.cwd()
    custom_schema_id = config.get("custom_schema_id")
    schema_source_type = "custom_schema" if custom_schema_id else "pack"
    custom_schema_version = config.get("custom_schema_version")

    return {
        "run_id": run_id,
        "output_run_id": output_run_id or run_id,
        "run_type": run_type,
        "scenario_id": scenario_id,
        "scenario_version": scenario_version,
        "config_schema_version": config.get("config_schema_version"),
        "seed": config.get("seed"),
        "pack": config.get("pack"),
        "custom_schema_id": custom_schema_id,
        "custom_schema_version": custom_schema_version,
        "schema_source_type": schema_source_type,
        "scale": config.get("scale"),
        "mode": config.get("mode"),
        "layer": config.get("layer"),
        "total_rows_generated": total_rows,
        "duration_seconds": duration_seconds,
        "storage_backend": storage_backend,
        "git_commit_sha": _git_sha(root),
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "created_at": now,
        "manifest_version": 1,
    }


def write_manifest_json(manifest: dict[str, Any], output_dir: Path) -> Path:
    """Write manifest as JSON to output_dir/manifest.json."""
    import json
    path = output_dir / "manifest.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def write_manifest_markdown(manifest: dict[str, Any], output_dir: Path) -> Path:
    """Write human-readable manifest as markdown."""
    path = output_dir / "manifest.md"
    schema_source = manifest.get("schema_source_type") or "pack"
    pack_line = f"- **Pack**: {manifest.get('pack') or '—'}"
    if schema_source == "custom_schema":
        pack_line = "- **Schema source**: Custom schema"
    lines = [
        "# Run manifest",
        "",
        f"- **Run ID**: {manifest.get('run_id', '')}",
        f"- **Output run ID**: {manifest.get('output_run_id', '')}",
        f"- **Run type**: {manifest.get('run_type', '')}",
        f"- **Scenario ID**: {manifest.get('scenario_id') or '—'}",
        f"- **Scenario version**: {manifest.get('scenario_version') or '—'}",
        f"- **Config schema version**: {manifest.get('config_schema_version') or '—'}",
        f"- **Seed**: {manifest.get('seed')}",
        pack_line,
    ]
    if manifest.get("custom_schema_id"):
        lines.append(f"- **Custom schema ID**: {manifest.get('custom_schema_id')}")
    if manifest.get("custom_schema_version") is not None:
        lines.append(f"- **Custom schema version**: {manifest.get('custom_schema_version')}")
    lines.extend([
        f"- **Scale**: {manifest.get('scale')}",
    ])
    lines.extend([
        f"- **Total rows**: {manifest.get('total_rows_generated') or '—'}",
        f"- **Duration (s)**: {manifest.get('duration_seconds')}",
        f"- **Storage backend**: {manifest.get('storage_backend', 'file')}",
        f"- **Git SHA**: {manifest.get('git_commit_sha') or '—'}",
        f"- **Created at**: {manifest.get('created_at')}",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
