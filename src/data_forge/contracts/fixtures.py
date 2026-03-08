"""Generate API request/response fixtures from OpenAPI schema."""

import json
import re
from pathlib import Path
from typing import Any


def _load_openapi(path: Path | str) -> dict[str, Any]:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        import yaml
        return yaml.safe_load(text)
    return json.loads(text)


def _resolve_ref(ref: str, root: dict[str, Any]) -> dict[str, Any] | None:
    """Resolve $ref to components/schemas/X or definitions/X."""
    if not ref.startswith("#/"):
        return None
    parts = ref.split("/")[1:]
    cur: Any = root
    for p in parts:
        cur = cur.get(p) if isinstance(cur, dict) else None
        if cur is None:
            return None
    return cur if isinstance(cur, dict) else None


def _get_schema(spec: Any, root: dict[str, Any]) -> dict[str, Any] | None:
    """Extract schema from content block or inline."""
    if not isinstance(spec, dict):
        return None
    if "$ref" in spec:
        return _resolve_ref(spec["$ref"], root)
    return spec.get("schema", spec)


def _sample_from_schema(schema: dict[str, Any], root: dict[str, Any], seed: int = 42) -> Any:
    """Generate a sample value from JSON Schema. Best-effort, supports common cases."""
    if "$ref" in schema:
        resolved = _resolve_ref(schema["$ref"], root)
        if resolved:
            return _sample_from_schema(resolved, root, seed)

    js_type = schema.get("type", "string")
    fmt = schema.get("format", "")
    enum_vals = schema.get("enum")
    if enum_vals:
        return enum_vals[seed % len(enum_vals)]

    if js_type == "string":
        if fmt == "uuid":
            return "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        if fmt == "date":
            return "2024-01-15"
        if fmt == "date-time":
            return "2024-01-15T12:00:00Z"
        if fmt == "email":
            return "user@example.com"
        return f"sample_{seed}"

    if js_type == "integer":
        return seed
    if js_type == "number":
        return float(seed)
    if js_type == "boolean":
        return seed % 2 == 0
    if js_type == "null":
        return None

    if js_type == "array":
        items = schema.get("items", {"type": "string"})
        return [_sample_from_schema(items, root, seed + i) for i in range(min(2, seed % 3 + 1))]

    if js_type == "object":
        props = schema.get("properties", {})
        obj: dict[str, Any] = {}
        required = set(schema.get("required", []))
        for i, (k, v) in enumerate(props.items()):
            if isinstance(v, dict):
                obj[k] = _sample_from_schema(v, root, seed + i * 7)
            else:
                obj[k] = None
        return obj

    return None


def _path_to_safe_name(path: str, method: str) -> str:
    """e.g. /users/{id} + get -> get_users_id."""
    parts = re.sub(r"[{}]", "", path.strip("/")).replace("/", "_").replace("-", "_")
    if not parts:
        parts = "root"
    return f"{method.lower()}_{parts}".replace("__", "_")


def generate_contract_fixtures(
    schema_path: Path | str,
    output_dir: Path | str,
    seed: int = 42,
) -> list[Path]:
    """
    Parse OpenAPI schema, extract request/response schemas from paths,
    generate sample fixtures, and write to output_dir.
    Returns list of written file paths.
    """
    root = _load_openapi(schema_path)
    paths = root.get("paths", {})
    if not paths:
        return []

    schemas = root.get("components", {}).get("schemas", root.get("definitions", {}))
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    counter = 0

    for path_str, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        base_name = _path_to_safe_name(path_str, "path")
        for method in ("get", "post", "put", "patch", "delete"):
            op = path_item.get(method)
            if not isinstance(op, dict):
                continue
            op_id = op.get("operationId") or f"{method}_{base_name}"

            # Request body
            req_body = op.get("requestBody", {})
            if isinstance(req_body, dict):
                content = req_body.get("content", {})
                for mt, spec in content.items():
                    if "json" in mt or mt == "application/json":
                        schema = _get_schema(spec, root)
                        if schema:
                            sample = _sample_from_schema(schema, root, seed + counter)
                            fname = f"{method}_{base_name}_request.json"
                            out_path = output_dir / fname
                            out_path.write_text(json.dumps(sample, indent=2, default=str), encoding="utf-8")
                            written.append(out_path)
                            counter += 1
                        break

            # Responses
            responses = op.get("responses", {})
            for status, resp_spec in responses.items():
                if not isinstance(resp_spec, dict):
                    continue
                content = resp_spec.get("content", {})
                for mt, spec in content.items():
                    if "json" in mt or mt == "application/json":
                        schema = _get_schema(spec, root)
                        if schema:
                            sample = _sample_from_schema(schema, root, seed + counter)
                            fname = f"{method}_{base_name}_response_{status}.json"
                            out_path = output_dir / fname
                            out_path.write_text(json.dumps(sample, indent=2, default=str), encoding="utf-8")
                            written.append(out_path)
                            counter += 1
                        break

    # If no path-based fixtures, fallback to components/schemas
    if not written and schemas:
        for name, schema in schemas.items():
            if isinstance(schema, dict) and schema.get("properties"):
                sample = _sample_from_schema(schema, root, seed)
                out_path = output_dir / f"{name}.json"
                out_path.write_text(json.dumps(sample, indent=2, default=str), encoding="utf-8")
                written.append(out_path)

    return written
