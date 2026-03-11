"""SQLite storage backend for runs and scenarios metadata."""

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

from data_forge.storage.base import RunStoreInterface, ScenarioStoreInterface
from data_forge.api.scenario_store import (
    MASKED_PLACEHOLDER,
    _redact_config,
    _extract_summary,
    _derive_badges,
)


def _default_db_path() -> Path:
    root = Path(__file__).resolve().parent.parent.parent.parent
    return root / "data" / "data_forge.db"


def _get_conn(db_path: Path | str | None) -> sqlite3.Connection:
    path = Path(db_path or _default_db_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def init_sqlite_schema(conn: sqlite3.Connection) -> None:
    """Create runs and scenarios tables if not exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            run_type TEXT NOT NULL,
            status TEXT NOT NULL,
            config TEXT NOT NULL,
            config_summary TEXT,
            selected_pack TEXT,
            source_scenario_id TEXT,
            created_at REAL,
            started_at REAL,
            finished_at REAL,
            duration_seconds REAL,
            stage_progress TEXT,
            warnings TEXT,
            error_message TEXT,
            result_summary TEXT,
            artifact_paths TEXT,
            artifacts TEXT,
            output_dir TEXT,
            output_run_id TEXT,
            events TEXT,
            pinned INTEGER DEFAULT 0,
            archived_at REAL,
            deleted_at REAL,
            updated_at REAL
        );
        CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
        CREATE INDEX IF NOT EXISTS idx_runs_created ON runs(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_runs_source_scenario ON runs(source_scenario_id);

        CREATE TABLE IF NOT EXISTS scenarios (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL,
            tags TEXT,
            source_pack TEXT,
            config TEXT NOT NULL,
            config_summary TEXT,
            created_at REAL,
            updated_at REAL,
            created_from_run_id TEXT,
            created_from_scenario_id TEXT,
            key_features TEXT,
            uses_pipeline_simulation INTEGER,
            uses_benchmark INTEGER,
            uses_privacy_mode INTEGER,
            uses_integrations INTEGER
        );
        CREATE INDEX IF NOT EXISTS idx_scenarios_category ON scenarios(category);
        CREATE INDEX IF NOT EXISTS idx_scenarios_updated ON scenarios(updated_at DESC);
    """)
    conn.commit()


def _run_row_to_record(row: sqlite3.Row) -> dict[str, Any]:
    """Convert DB row to run record dict."""
    r = dict(row)
    for key in ("config", "config_summary", "stage_progress", "warnings", "result_summary",
                "artifact_paths", "artifacts", "events"):
        if r.get(key):
            try:
                r[key] = json.loads(r[key])
            except (TypeError, json.JSONDecodeError):
                r[key] = [] if key in ("stage_progress", "warnings", "artifact_paths", "artifacts", "events") else {}
        elif key in ("stage_progress", "warnings", "artifact_paths", "artifacts", "events"):
            r[key] = []
    r["pinned"] = bool(r.get("pinned"))
    return r


def _scenario_row_to_record(row: sqlite3.Row) -> dict[str, Any]:
    """Convert DB row to scenario record dict."""
    r = dict(row)
    for key in ("config", "config_summary", "tags", "key_features"):
        if r.get(key):
            try:
                r[key] = json.loads(r[key])
            except (TypeError, json.JSONDecodeError):
                r[key] = [] if key in ("tags", "key_features") else {}
        elif key in ("tags", "key_features"):
            r[key] = []
    for k in ("uses_pipeline_simulation", "uses_benchmark", "uses_privacy_mode", "uses_integrations"):
        r[k] = bool(r.get(k))
    return r


class SQLiteRunStore(RunStoreInterface):
    """SQLite-backed run store."""

    def __init__(self, db_path: Path | str | None = None):
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        conn = _get_conn(self.db_path)
        init_sqlite_schema(conn)
        return conn

    def create_run(
        self,
        run_id: str,
        run_type: str,
        config: dict[str, Any],
        *,
        selected_pack: str | None = None,
        source_scenario_id: str | None = None,
    ) -> dict[str, Any]:
        now = time.time()
        config_summary = _redact_config(config)
        record = {
            "id": run_id,
            "status": "queued",
            "created_at": now,
            "started_at": None,
            "finished_at": None,
            "duration_seconds": None,
            "run_type": run_type,
            "config": config,
            "config_summary": config_summary,
            "selected_pack": selected_pack or config.get("pack"),
            "stage_progress": [],
            "warnings": [],
            "error_message": None,
            "result_summary": None,
            "artifact_paths": [],
            "artifacts": [],
            "output_dir": None,
            "events": [],
            "pinned": False,
            "archived_at": None,
            "deleted_at": None,
        }
        if source_scenario_id:
            record["source_scenario_id"] = source_scenario_id
        conn = self._conn()
        try:
            conn.execute(
                """INSERT INTO runs (id, run_type, status, config, config_summary, selected_pack,
                   source_scenario_id, created_at, stage_progress, warnings, artifact_paths, artifacts, events, pinned, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    run_id, run_type, "queued",
                    json.dumps(config), json.dumps(config_summary),
                    selected_pack or config.get("pack"), source_scenario_id or "",
                    now, json.dumps([]), json.dumps([]), json.dumps([]), json.dumps([]), 0, now,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return record

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        conn = self._conn()
        try:
            row = conn.execute("SELECT * FROM runs WHERE id = ? AND deleted_at IS NULL", (run_id,)).fetchone()
            return _run_row_to_record(row) if row else None
        finally:
            conn.close()

    def update_run(self, run_id: str, **kwargs: Any) -> dict[str, Any] | None:
        record = self.get_run(run_id)
        if not record:
            return None
        for k, v in kwargs.items():
            if v is not None:
                record[k] = v
        conn = self._conn()
        try:
            json_cols = ("config", "config_summary", "stage_progress", "warnings", "result_summary",
                        "artifact_paths", "artifacts", "events")
            set_parts = ["updated_at = ?"]
            vals: list[Any] = [time.time()]
            for k, v in kwargs.items():
                if v is None:
                    continue
                if k in json_cols and isinstance(v, (list, dict)):
                    set_parts.append(f"{k} = ?")
                    vals.append(json.dumps(v))
                elif k in ("created_at", "started_at", "finished_at", "duration_seconds", "archived_at", "deleted_at"):
                    set_parts.append(f"{k} = ?")
                    vals.append(v)
                elif k == "pinned":
                    set_parts.append("pinned = ?")
                    vals.append(1 if v else 0)
                elif k in ("id", "run_type", "status", "selected_pack", "source_scenario_id", "error_message", "output_dir", "output_run_id"):
                    set_parts.append(f"{k} = ?")
                    vals.append(v)
            vals.append(run_id)
            conn.execute(f"UPDATE runs SET {', '.join(set_parts)} WHERE id = ?", vals)
            conn.commit()
        finally:
            conn.close()
        return self.get_run(run_id)

    def append_event(self, run_id: str, level: str, message: str) -> None:
        record = self.get_run(run_id)
        if not record:
            return
        events = record.get("events") or []
        events.append({"level": level, "message": message, "ts": time.time()})
        events = events[-200:]
        conn = self._conn()
        try:
            conn.execute("UPDATE runs SET events = ?, updated_at = ? WHERE id = ?",
                         (json.dumps(events), time.time(), run_id))
            conn.commit()
        finally:
            conn.close()

    def list_runs(
        self,
        *,
        status: str | None = None,
        run_type: str | None = None,
        pack: str | None = None,
        mode: str | None = None,
        layer: str | None = None,
        source_scenario_id: str | None = None,
        limit: int = 100,
        include_archived: bool = True,
    ) -> list[dict[str, Any]]:
        conn = self._conn()
        try:
            q = "SELECT * FROM runs WHERE deleted_at IS NULL"
            params: list[Any] = []
            if not include_archived:
                q += " AND archived_at IS NULL"
            if status:
                q += " AND status = ?"
                params.append(status)
            if run_type:
                q += " AND run_type = ?"
                params.append(run_type)
            if pack:
                q += " AND selected_pack = ?"
                params.append(pack)
            if source_scenario_id:
                q += " AND source_scenario_id = ?"
                params.append(source_scenario_id)
            q += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(q, params).fetchall()
            out = [_run_row_to_record(r) for r in rows]
            if mode or layer:
                cfg_key = "config"
                out = [r for r in out if (
                    (not mode or (r.get(cfg_key) or r.get("config_summary") or {}).get("mode") == mode)
                    and (not layer or (r.get(cfg_key) or r.get("config_summary") or {}).get("layer") == layer)
                )]
            return out
        finally:
            conn.close()

    def run_cleanup(
        self,
        retention_count: int | None = None,
        retention_days: float | None = None,
    ) -> int:
        from data_forge.config import Settings
        settings = Settings()
        count = retention_count if retention_count is not None else settings.runs_retention_count
        days = retention_days if retention_days is not None else settings.runs_retention_days
        conn = self._conn()
        try:
            # Only soft-delete or delete non-pinned runs; keep pinned
            rows = conn.execute(
                "SELECT id FROM runs WHERE deleted_at IS NULL AND pinned = 0 ORDER BY created_at DESC"
            ).fetchall()
            to_delete: list[str] = []
            now = time.time()
            for i, row in enumerate(rows):
                if i >= count:
                    to_delete.append(row["id"])
                    continue
                if days and days > 0:
                    r = conn.execute("SELECT created_at FROM runs WHERE id = ?", (row["id"],)).fetchone()
                    if r and (now - (r["created_at"] or 0)) / 86400 > days:
                        to_delete.append(row["id"])
            for run_id in to_delete:
                conn.execute("UPDATE runs SET deleted_at = ?, updated_at = ? WHERE id = ?", (now, now, run_id))
            conn.commit()
            return len(to_delete)
        finally:
            conn.close()

    def delete_run(self, run_id: str) -> bool:
        """Soft-delete run (set deleted_at)."""
        conn = self._conn()
        try:
            cur = conn.execute(
                "UPDATE runs SET deleted_at = ?, updated_at = ? WHERE id = ?",
                (time.time(), time.time(), run_id),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()


class SQLiteScenarioStore(ScenarioStoreInterface):
    """SQLite-backed scenario store."""

    def __init__(self, db_path: Path | str | None = None):
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        conn = _get_conn(self.db_path)
        init_sqlite_schema(conn)
        return conn

    def create_scenario(
        self,
        name: str,
        config: dict[str, Any],
        *,
        description: str = "",
        category: str = "custom",
        tags: list[str] | None = None,
        created_from_run_id: str | None = None,
        created_from_scenario_id: str | None = None,
    ) -> dict[str, Any]:
        scenario_id = f"scenario_{uuid.uuid4().hex[:12]}"
        now = time.time()
        config_summary = _redact_config(config)
        summary = _extract_summary(config)
        badges = _derive_badges(config)
        record = {
            "id": scenario_id,
            "name": name,
            "description": description or "",
            "category": category,
            "tags": tags or [],
            "source_pack": config.get("pack"),
            "config": config,
            "config_summary": config_summary,
            "created_at": now,
            "updated_at": now,
            "created_from_run_id": created_from_run_id,
            "created_from_scenario_id": created_from_scenario_id,
            "key_features": badges,
            "uses_pipeline_simulation": summary.get("uses_pipeline_simulation", False),
            "uses_benchmark": summary.get("uses_benchmark", False),
            "uses_privacy_mode": bool(summary.get("privacy_mode") and summary.get("privacy_mode") != "off"),
            "uses_integrations": bool(
                config.get("export_dbt") or config.get("export_ge") or config.get("export_airflow")
            ),
        }
        conn = self._conn()
        try:
            conn.execute(
                """INSERT INTO scenarios (id, name, description, category, tags, source_pack, config, config_summary,
                   created_at, updated_at, created_from_run_id, created_from_scenario_id, key_features,
                   uses_pipeline_simulation, uses_benchmark, uses_privacy_mode, uses_integrations)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    scenario_id, name, description or "", category, json.dumps(tags or []), config.get("pack"),
                    json.dumps(config), json.dumps(config_summary), now, now,
                    created_from_run_id or "", created_from_scenario_id or "", json.dumps(badges),
                    1 if record["uses_pipeline_simulation"] else 0, 1 if record["uses_benchmark"] else 0,
                    1 if record["uses_privacy_mode"] else 0, 1 if record["uses_integrations"] else 0,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return record

    def get_scenario(self, scenario_id: str) -> dict[str, Any] | None:
        conn = self._conn()
        try:
            row = conn.execute("SELECT * FROM scenarios WHERE id = ?", (scenario_id,)).fetchone()
            return _scenario_row_to_record(row) if row else None
        finally:
            conn.close()

    def update_scenario(self, scenario_id: str, **kwargs: Any) -> dict[str, Any] | None:
        record = self.get_scenario(scenario_id)
        if not record:
            return None
        if "config" in kwargs:
            record["config_summary"] = _redact_config(kwargs["config"])
            summary = _extract_summary(kwargs["config"])
            record["key_features"] = _derive_badges(kwargs["config"])
            record["uses_pipeline_simulation"] = summary.get("uses_pipeline_simulation", False)
            record["uses_benchmark"] = summary.get("uses_benchmark", False)
            record["uses_privacy_mode"] = bool(summary.get("privacy_mode") and summary.get("privacy_mode") != "off")
            record["uses_integrations"] = bool(
                kwargs["config"].get("export_dbt") or kwargs["config"].get("export_ge")
                or kwargs["config"].get("export_airflow")
            )
        record["updated_at"] = time.time()
        for k, v in kwargs.items():
            if v is not None:
                record[k] = v
        conn = self._conn()
        try:
            conn.execute(
                """UPDATE scenarios SET name=?, description=?, category=?, tags=?, config=?, config_summary=?,
                   source_pack=?, key_features=?, uses_pipeline_simulation=?, uses_benchmark=?, uses_privacy_mode=?,
                   uses_integrations=?, updated_at=? WHERE id=?""",
                (
                    record.get("name"), record.get("description"), record.get("category"), json.dumps(record.get("tags") or []),
                    json.dumps(record.get("config") or {}), json.dumps(record.get("config_summary") or {}),
                    record.get("source_pack"), json.dumps(record.get("key_features") or []),
                    1 if record.get("uses_pipeline_simulation") else 0, 1 if record.get("uses_benchmark") else 0,
                    1 if record.get("uses_privacy_mode") else 0, 1 if record.get("uses_integrations") else 0,
                    record["updated_at"], scenario_id,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return self.get_scenario(scenario_id)

    def delete_scenario(self, scenario_id: str) -> bool:
        conn = self._conn()
        try:
            cur = conn.execute("DELETE FROM scenarios WHERE id = ?", (scenario_id,))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def list_scenarios(
        self,
        *,
        category: str | None = None,
        source_pack: str | None = None,
        tag: str | None = None,
        search: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        conn = self._conn()
        try:
            q = "SELECT * FROM scenarios WHERE 1=1"
            params: list[Any] = []
            if category:
                q += " AND category = ?"
                params.append(category)
            if source_pack:
                q += " AND source_pack = ?"
                params.append(source_pack)
            q += " ORDER BY updated_at DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(q, params).fetchall()
            out = [_scenario_row_to_record(r) for r in rows]
            if tag:
                out = [s for s in out if tag in (s.get("tags") or [])]
            if search:
                ql = search.lower()
                out = [s for s in out if ql in (s.get("name") or "").lower() or ql in (s.get("description") or "").lower()]
            return out
        finally:
            conn.close()

    def get_masked_field_names(self, config: dict[str, Any] | None, prefix: str = "") -> list[str]:
        if not config or not isinstance(config, dict):
            return []
        names: list[str] = []
        for k, v in config.items():
            if isinstance(v, str) and v == MASKED_PLACEHOLDER:
                names.append(prefix + k if prefix else k)
            elif isinstance(v, dict):
                names.extend(self.get_masked_field_names(v, prefix=f"{prefix}{k}."))
        return names
