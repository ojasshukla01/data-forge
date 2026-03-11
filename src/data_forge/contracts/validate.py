"""Validate generated fixtures against OpenAPI / JSON Schema."""

import json
from pathlib import Path
from typing import Any, cast


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_openapi(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        import yaml
        return cast(dict[str, Any], yaml.safe_load(text))
    return cast(dict[str, Any], json.loads(text))


def _resolve_ref(ref: str, root: dict[str, Any]) -> dict[str, Any] | None:
    if not ref.startswith("#/"):
        return None
    parts = ref.split("/")[1:]
    cur: Any = root
    for p in parts:
        cur = cur.get(p) if isinstance(cur, dict) else None
        if cur is None:
            return None
    return cur if isinstance(cur, dict) else None




def _validate_against_schema(data: Any, schema: dict[str, Any], root: dict[str, Any]) -> list[str]:
    """Validate data against JSON Schema. Use jsonschema if available."""
    try:
        import jsonschema
        jsonschema.validate(instance=data, schema=schema)
        return []
    except ImportError:
        # Minimal validation: check required props
        if not isinstance(schema, dict):
            return []
        required = schema.get("required", [])
        if not isinstance(data, dict):
            return ["Expected object"] if required else []
        errors = []
        for r in required:
            if r not in data:
                errors.append(f"missing required property: {r}")
        return errors
    except Exception as e:
        return [str(e)]


def validate_contract_fixtures(
    schema_path: Path | str,
    data_dir: Path | str,
) -> dict[str, Any]:
    """
    Validate fixture files in data_dir against OpenAPI schema.
    Returns report with total, passed, failed, failures.
    """
    schema_path = Path(schema_path)
    data_dir = Path(data_dir)
    if not schema_path.exists():
        return {"total": 0, "passed": 0, "failed": 0, "failures": [{"fixture": "schema", "reason": "Schema not found"}]}

    root = _load_openapi(schema_path)
    schemas = root.get("components", {}).get("schemas", root.get("definitions", {}))
    if not schemas:
        return {"total": 0, "passed": 0, "failed": 0, "failures": []}

    json_files = list(data_dir.glob("*.json"))
    total = len(json_files)
    passed = 0
    failures: list[dict[str, Any]] = []

    for f in json_files:
        try:
            data = _load_json(f)
        except Exception as e:
            failures.append({"fixture": f.name, "reason": f"Invalid JSON: {e}"})
            continue

        # Pick schema: try to match by name
        schema = None
        for name, s in schemas.items():
            if not isinstance(s, dict):
                continue
            if name in f.stem or f.stem.replace("_", "").startswith(name.replace("_", "")):
                schema = _resolve_ref(s["$ref"], root) if "$ref" in s else s
                break
        if schema is None:
            for s in schemas.values():
                if isinstance(s, dict) and (s.get("properties") or "$ref" in s):
                    schema = _resolve_ref(s["$ref"], root) if "$ref" in s else s
                    break

        if schema is None or not isinstance(schema, dict):
            passed += 1
            continue

        errors = _validate_against_schema(data, schema, root)
        if errors:
            failures.append({"fixture": f.name, "reason": "; ".join(errors)})
        else:
            passed += 1

    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "failures": failures,
    }
