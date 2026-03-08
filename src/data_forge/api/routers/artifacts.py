"""Artifacts API router."""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from data_forge.api.run_store import list_runs

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent


def _registry_artifacts_for_output(output_folder_id: str) -> list[dict[str, Any]]:
    """Get artifacts from run registry for output folder (artifact_run_id)."""
    runs = list_runs(limit=500)
    for r in runs:
        summary = r.get("result_summary") or {}
        aid = summary.get("artifact_run_id") or summary.get("output_run_id")
        if aid == output_folder_id:
            arts = r.get("artifacts") or []
            return [{"run_id": output_folder_id, **a} for a in arts]
    return []


def _scan_artifacts(output_dir: Path) -> list[dict[str, Any]]:
    """Scan output directory for artifact files."""
    artifacts: list[dict[str, Any]] = []
    if not output_dir.is_dir():
        return artifacts
    for f in sorted(output_dir.rglob("*")):
        if not f.is_file():
            continue
        try:
            stat = f.stat()
            rel = str(f.relative_to(output_dir)).replace("\\", "/")
            suffix = f.suffix.lower()
            cat = "dataset"
            if suffix in (".json", ".yaml", ".yml") and ("manifest" in rel or "ge" in rel.lower()):
                cat = "manifest" if "manifest" in rel else "ge"
            elif "great_expectations" in rel or "expectations" in rel:
                cat = "ge"
            elif "airflow" in rel or "dags" in rel:
                cat = "airflow"
            elif "dbt" in rel or "seeds" in rel:
                cat = "dbt"
            elif "contracts" in rel:
                cat = "contracts"
            elif "event_stream" in rel or ("events" in rel and suffix == ".jsonl"):
                cat = "event_stream"
            elif "pipeline_snapshot" in rel or ("snapshot" in rel and suffix == ".json"):
                cat = "pipeline_snapshot"
            elif "benchmark_profile" in rel:
                cat = "benchmark_profile"
            elif suffix in (".csv", ".json", ".jsonl", ".parquet", ".sql"):
                cat = "dataset"
            artifacts.append({
                "path": rel,
                "name": f.name,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "category": cat,
                "type": cat,
            })
        except (OSError, ValueError):
            continue
    return artifacts


@router.get("")
def list_artifacts(run_id: str | None = None, type_filter: str | None = None) -> dict:
    """
    List artifacts. If run_id given, prefer registry from run records; else scan output dir.
    type_filter: dataset|dbt|ge|airflow|contracts|manifest
    """
    root = _project_root()
    output_base = root / "output"
    if not output_base.exists():
        return {"artifacts": [], "runs": []}

    if run_id:
        run_dir = output_base / run_id
        if not run_dir.is_dir():
            return {"artifacts": [], "runs": [{"id": run_id, "exists": False}], "run_id": run_id}
        # Prefer registry when available
        reg = _registry_artifacts_for_output(run_id)
        if reg:
            artifacts = reg
        else:
            artifacts = _scan_artifacts(run_dir)
            for a in artifacts:
                a["run_id"] = run_id
        if type_filter and type_filter != "all":
            artifacts = [a for a in artifacts if (a.get("type") or a.get("category") or "dataset") == type_filter]
        return {"artifacts": artifacts, "runs": [{"id": run_id}], "run_id": run_id}

    runs: list[dict[str, Any]] = []
    all_artifacts: list[dict[str, Any]] = []
    for d in sorted(output_base.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if d.is_dir() and (d.name.startswith("run_") or d.name.isdigit()):
            arts = _scan_artifacts(d)
            runs.append({"id": d.name, "artifact_count": len(arts)})
            for a in arts:
                a["run_id"] = d.name
                all_artifacts.append(a)
    return {"artifacts": all_artifacts[:200], "runs": runs[:50]}


@router.get("/file")
def get_artifact(run_id: str, path: str) -> FileResponse:
    """Download or serve an artifact file. path is relative to run output dir."""
    root = _project_root()
    full = (root / "output" / run_id / path).resolve()
    base = (root / "output" / run_id).resolve()
    if not full.exists() or not str(full).startswith(str(base)):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(full, filename=full.name)
