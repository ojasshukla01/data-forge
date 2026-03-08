"""Parse SQL DDL to SchemaModel (CREATE TABLE, primary/foreign keys)."""

import re
from typing import Any

from data_forge.models.schema import (
    ColumnDef,
    DataType,
    RelationshipDef,
    SchemaModel,
    TableDef,
)

# Map SQL type names (lower) to our DataType
_SQL_TYPE_MAP: dict[str, DataType] = {
    "varchar": DataType.STRING,
    "char": DataType.STRING,
    "text": DataType.TEXT,
    "int": DataType.INTEGER,
    "integer": DataType.INTEGER,
    "smallint": DataType.INTEGER,
    "bigint": DataType.BIGINT,
    "serial": DataType.INTEGER,
    "bigserial": DataType.BIGINT,
    "real": DataType.FLOAT,
    "float": DataType.FLOAT,
    "double precision": DataType.FLOAT,
    "numeric": DataType.DECIMAL,
    "decimal": DataType.DECIMAL,
    "boolean": DataType.BOOLEAN,
    "bool": DataType.BOOLEAN,
    "date": DataType.DATE,
    "time": DataType.DATETIME,
    "timestamp": DataType.TIMESTAMP,
    "timestamptz": DataType.TIMESTAMP,
    "uuid": DataType.UUID,
    "json": DataType.JSON,
    "jsonb": DataType.JSON,
}


def _normalize_sql_type(raw: str) -> tuple[DataType, int | None]:
    """Parse SQL type string to DataType and optional length."""
    raw = raw.strip().lower()
    # Strip constraint keywords that may have been captured (e.g. "bigint primary key" -> "bigint")
    for kw in ("primary", "key", "not", "null", "unique", "references", "default", "check"):
        raw = re.sub(r"\b" + kw + r"\b.*", "", raw).strip()
    # Strip parentheses for varchar(255) etc.
    match = re.match(r"(\w+(?:\s+\w+)?)\s*\(\s*(\d+)\s*\)", raw)
    if match:
        base, length = match.group(1).strip(), int(match.group(2))
        return _SQL_TYPE_MAP.get(base, DataType.STRING), length
    base = re.sub(r"\s*\(.*\)", "", raw).strip()
    return _SQL_TYPE_MAP.get(base, DataType.STRING), None


def parse_sql_ddl(ddl: str, source: str | None = None) -> SchemaModel:
    """
    Parse SQL DDL string into SchemaModel.
    Supports CREATE TABLE, PRIMARY KEY, REFERENCES (foreign keys).
    """
    tables: list[TableDef] = []
    relationships: list[RelationshipDef] = []
    # Normalize: single line per statement, strip comments
    ddl_clean = re.sub(r"--[^\n]*", "\n", ddl)
    ddl_clean = re.sub(r"/\*.*?\*/", "", ddl_clean, flags=re.DOTALL)
    ddl_clean = " ".join(ddl_clean.split())
    # Split by CREATE TABLE
    create_pattern = re.compile(
        r"create\s+table\s+(?:if\s+not\s+exists\s+)?[\"]?(\w+)[\"]?\s*\((.*?)\)\s*;",
        re.IGNORECASE | re.DOTALL,
    )
    for m in create_pattern.finditer(ddl_clean):
        table_name = m.group(1).lower()
        body = m.group(2)
        columns, pk_cols, fk_refs = _parse_table_body(body, table_name)
        tables.append(
            TableDef(
                name=table_name,
                columns=columns,
                primary_key=pk_cols,
            )
        )
        for (fk_col, ref_table, ref_col) in fk_refs:
            relationships.append(
                RelationshipDef(
                    name=f"{table_name}_{fk_col}_fkey",
                    from_table=table_name,
                    from_columns=[fk_col],
                    to_table=ref_table,
                    to_columns=[ref_col],
                    cardinality="many-to-one",
                )
            )
    return SchemaModel(
        name="sql_ddl",
        tables=tables,
        relationships=relationships,
        source=source,
        source_type="sql_ddl",
    )


def _parse_table_body(body: str, table_name: str) -> tuple[list[ColumnDef], list[str], list[tuple[str, str, str]]]:
    """Parse table body: column list, primary key columns, and FK references."""
    columns: list[ColumnDef] = []
    pk_cols: list[str] = []
    fk_refs: list[tuple[str, str, str]] = []
    # Split by comma, but respect parentheses
    tokens = _split_top_level(body, ",")
    for part in tokens:
        part = part.strip()
        if not part:
            continue
        upper = part.upper()
        if upper.startswith("PRIMARY KEY"):
            # PRIMARY KEY (col1, col2) or PRIMARY KEY (col1)
            pk_match = re.search(r"primary\s+key\s*\(\s*([^)]+)\s*\)", part, re.IGNORECASE)
            if pk_match:
                pk_cols = [c.strip().strip('"').lower() for c in pk_match.group(1).split(",")]
            continue
        if upper.startswith("FOREIGN KEY"):
            # FOREIGN KEY (col) REFERENCES other_table(ref_col)
            fk_match = re.search(
                r"foreign\s+key\s*\(\s*([^)]+)\s*\)\s+references\s+[\"]?(\w+)[\"]?\s*\(\s*([^)]+)\s*\)",
                part,
                re.IGNORECASE,
            )
            if fk_match:
                fk_col = fk_match.group(1).strip().strip('"').lower()
                ref_table = fk_match.group(2).strip().lower()
                ref_col = fk_match.group(3).strip().strip('"').lower()
                fk_refs.append((fk_col, ref_table, ref_col))
            continue
        if upper.startswith("UNIQUE") or upper.startswith("CONSTRAINT") or upper.startswith("CHECK"):
            continue
        # Column definition: name type [constraints] [REFERENCES other(col)]
        col_match = re.match(r"[\"]?(\w+)[\"]?\s+(\w+(?:\s+\w+)?(?:\s*\(\s*\d+\s*\))?)", part, re.IGNORECASE)
        if col_match:
            col_name = col_match.group(1).strip('"').lower()
            sql_type = col_match.group(2).strip()
            dtype, max_len = _normalize_sql_type(sql_type)
            nullable = "NOT NULL" not in part.upper()
            unique = "UNIQUE" in part.upper()
            is_pk = "PRIMARY KEY" in part.upper()
            if is_pk and col_name not in pk_cols:
                pk_cols.append(col_name)
            columns.append(
                ColumnDef(
                    name=col_name,
                    data_type=dtype,
                    nullable=nullable,
                    unique=unique,
                    primary_key=is_pk,
                    max_length=max_len,
                )
            )
            # Inline REFERENCES other_table(ref_col)
            ref_match = re.search(
                r"references\s+[\"]?(\w+)[\"]?\s*\(\s*([^)]+)\s*\)",
                part,
                re.IGNORECASE,
            )
            if ref_match:
                ref_table = ref_match.group(1).strip().lower()
                ref_col = ref_match.group(2).strip().strip('"').lower()
                fk_refs.append((col_name, ref_table, ref_col))
    return columns, pk_cols, fk_refs


def _split_top_level(s: str, sep: str) -> list[str]:
    """Split by sep at top level (ignore inside parentheses)."""
    result: list[str] = []
    depth = 0
    start = 0
    for i, c in enumerate(s):
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        elif c == sep and depth == 0:
            result.append(s[start:i])
            start = i + 1
    result.append(s[start:])
    return result
