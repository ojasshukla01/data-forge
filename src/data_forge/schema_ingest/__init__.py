"""Schema ingestion from SQL DDL, JSON Schema, OpenAPI, Pydantic."""

from pathlib import Path
from typing import Any

from data_forge.models.schema import (
    ColumnDef,
    DataType,
    RelationshipDef,
    SchemaModel,
    TableDef,
)

from data_forge.schema_ingest.sql_ddl import parse_sql_ddl
from data_forge.schema_ingest.json_schema import parse_json_schema

__all__ = [
    "load_schema",
    "parse_sql_ddl",
    "parse_json_schema",
    "SchemaModel",
]


def load_schema(path: Path | str, project_root: Path | None = None) -> SchemaModel:
    """
    Load a schema from a file. Format is inferred from extension.
    - .sql -> SQL DDL
    - .json -> JSON Schema (or OpenAPI if has openapi/swagger key)
    """
    from data_forge.config import Settings, ensure_path_allowed

    path = Path(path)
    root = project_root or Settings().project_root
    path = ensure_path_allowed(path, root)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".sql":
        text = path.read_text(encoding="utf-8")
        return parse_sql_ddl(text, source=str(path))
    if suffix == ".json" or suffix == ".yaml" or suffix == ".yml":
        if suffix == ".json":
            import json

            data = json.loads(path.read_text(encoding="utf-8"))
        else:
            import yaml

            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            if "openapi" in data or "swagger" in data:
                return _parse_openapi(data, source=str(path))
            if "tables" in data or "definitions" in data or "properties" in data:
                return parse_json_schema(data, source=str(path))
        return parse_json_schema(data, source=str(path))
    raise ValueError(f"Unsupported schema file format: {suffix}")


def _parse_openapi(data: dict[str, Any], source: str) -> SchemaModel:
    """Extract request/response schemas from OpenAPI as a single logical schema."""
    # Simplified: treat each schema object as a "table" with properties as columns
    schemas = data.get("components", {}).get("schemas", data.get("definitions", {}))
    tables: list[TableDef] = []
    for name, schema in schemas.items():
        if not isinstance(schema, dict):
            continue
        props = schema.get("properties", {})
        cols = []
        for prop_name, prop_spec in props.items():
            if not isinstance(prop_spec, dict):
                continue
            dtype = _json_type_to_data_type(prop_spec.get("type"), prop_spec.get("format"))
            cols.append(
                ColumnDef(
                    name=prop_name,
                    data_type=dtype,
                    nullable=prop_name not in (schema.get("required") or []),
                )
            )
        if cols:
            tables.append(TableDef(name=name, columns=cols))
    return SchemaModel(
        name="openapi",
        tables=tables,
        source=source,
        source_type="openapi",
    )


def _json_type_to_data_type(js_type: str | None, fmt: str | None) -> DataType:
    """Map JSON Schema type/format to our DataType."""
    if fmt == "date":
        return DataType.DATE
    if fmt == "date-time":
        return DataType.DATETIME
    if fmt == "uuid":
        return DataType.UUID
    if fmt == "email":
        return DataType.EMAIL
    if fmt == "uri":
        return DataType.URL
    m = {
        "string": DataType.STRING,
        "integer": DataType.INTEGER,
        "number": DataType.FLOAT,
        "boolean": DataType.BOOLEAN,
        "array": DataType.JSON,
        "object": DataType.JSON,
    }
    return m.get(js_type or "string", DataType.STRING)
