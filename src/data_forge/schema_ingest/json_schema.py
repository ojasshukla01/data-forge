"""Parse JSON Schema (or table-like JSON) to SchemaModel."""

from typing import Any

from data_forge.models.schema import (
    ColumnDef,
    DataType,
    SchemaModel,
    TableDef,
)


def _infer_data_type(prop: Any) -> DataType:
    """Infer DataType from JSON Schema property."""
    if not isinstance(prop, dict):
        return DataType.STRING
    t = prop.get("type", "string")
    fmt = prop.get("format", "")
    if fmt == "date-time" or fmt == "date":
        return DataType.DATE if fmt == "date" else DataType.DATETIME
    if fmt == "uuid":
        return DataType.UUID
    if fmt == "email":
        return DataType.EMAIL
    if fmt == "uri":
        return DataType.URL
    type_map = {
        "string": DataType.STRING,
        "integer": DataType.INTEGER,
        "number": DataType.FLOAT,
        "boolean": DataType.BOOLEAN,
        "array": DataType.JSON,
        "object": DataType.JSON,
    }
    return type_map.get(t, DataType.STRING)


def parse_json_schema(data: Any, source: str | None = None) -> SchemaModel:
    """
    Parse JSON Schema or a table-definition JSON into SchemaModel.
    Accepts:
    - { "tables": [ { "name": "...", "columns": [...] } ] }
    - { "definitions": { "EntityName": { "properties": { ... } } } }
    - { "properties": { ... } }  (single table)
    """
    tables: list[TableDef] = []

    if isinstance(data, dict) and "tables" in data:
        for t in data["tables"]:
            if not isinstance(t, dict):
                continue
            name = t.get("name", "unknown")
            cols = []
            for c in t.get("columns", []):
                if isinstance(c, dict):
                    cols.append(
                        ColumnDef(
                            name=c.get("name", "col"),
                            data_type=DataType(c.get("data_type", "string")),
                            nullable=c.get("nullable", True),
                            unique=c.get("unique", False),
                            primary_key=c.get("primary_key", False),
                        )
                    )
                elif isinstance(c, str):
                    cols.append(ColumnDef(name=c, data_type=DataType.STRING))
            tables.append(TableDef(name=name, columns=cols))
        rels = [
            _dict_to_relationship(r)
            for r in data.get("relationships", [])
            if isinstance(r, dict)
        ]
        return SchemaModel(
            name=data.get("name", "json"),
            tables=tables,
            relationships=rels,
            source=source,
            source_type="json_schema",
        )

    if isinstance(data, dict) and "definitions" in data:
        defs = data["definitions"]
        for name, schema in defs.items():
            if not isinstance(schema, dict):
                continue
            props = schema.get("properties", {})
            cols = []
            required = set(schema.get("required", []))
            for prop_name, prop_spec in props.items():
                if not isinstance(prop_spec, dict):
                    continue
                cols.append(
                    ColumnDef(
                        name=prop_name,
                        data_type=_infer_data_type(prop_spec),
                        nullable=prop_name not in required,
                    )
                )
            if cols:
                tables.append(TableDef(name=name, columns=cols))
        return SchemaModel(
            name=data.get("name", "json"),
            tables=tables,
            source=source,
            source_type="json_schema",
        )

    if isinstance(data, dict) and "properties" in data:
        props = data.get("properties", {})
        required = set(data.get("required", []))
        cols = []
        for prop_name, prop_spec in props.items():
            if not isinstance(prop_spec, dict):
                continue
            cols.append(
                ColumnDef(
                    name=prop_name,
                    data_type=_infer_data_type(prop_spec),
                    nullable=prop_name not in required,
                )
            )
        if cols:
            tables.append(TableDef(name="root", columns=cols))
        return SchemaModel(
            name=data.get("title", "root"),
            tables=tables,
            source=source,
            source_type="json_schema",
        )

    return SchemaModel(name="empty", tables=[], source=source, source_type="json_schema")


def _dict_to_relationship(r: dict[str, Any]) -> Any:
    """Build RelationshipDef from dict."""
    from data_forge.models.schema import RelationshipDef

    return RelationshipDef(
        name=r.get("name", "rel"),
        from_table=r.get("from_table", ""),
        from_columns=r.get("from_columns", []),
        to_table=r.get("to_table", ""),
        to_columns=r.get("to_columns", []),
        cardinality=r.get("cardinality", "many-to-one"),
        optional=r.get("optional", False),
    )
