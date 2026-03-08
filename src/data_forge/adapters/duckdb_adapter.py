"""DuckDB adapter for efficient bulk loading."""

from typing import Any

from data_forge.adapters.base import BaseDatabaseAdapter
from data_forge.models.schema import SchemaModel, DataType


def _data_type_to_duckdb(dt: DataType) -> str:
    m = {
        DataType.STRING: "VARCHAR",
        DataType.TEXT: "VARCHAR",
        DataType.INTEGER: "INTEGER",
        DataType.BIGINT: "BIGINT",
        DataType.FLOAT: "DOUBLE",
        DataType.DECIMAL: "DECIMAL(18,4)",
        DataType.BOOLEAN: "BOOLEAN",
        DataType.DATE: "DATE",
        DataType.DATETIME: "TIMESTAMP",
        DataType.TIMESTAMP: "TIMESTAMP",
        DataType.UUID: "VARCHAR",
        DataType.EMAIL: "VARCHAR",
        DataType.PHONE: "VARCHAR",
        DataType.URL: "VARCHAR",
        DataType.JSON: "VARCHAR",
        DataType.ENUM: "VARCHAR",
        DataType.CURRENCY: "DOUBLE",
        DataType.PERCENT: "DOUBLE",
    }
    return m.get(dt, "VARCHAR")


class DuckDBAdapter(BaseDatabaseAdapter):
    """DuckDB adapter with efficient bulk inserts via PyArrow when available."""

    def __init__(self, uri: str, batch_size: int = BaseDatabaseAdapter.DEFAULT_BATCH_SIZE) -> None:
        super().__init__(uri, batch_size)
        self._conn: Any = None

    def connect(self) -> None:
        import duckdb
        self._conn = duckdb.connect(self.uri)

    def create_schema(self, schema_model: SchemaModel) -> None:
        pass  # DuckDB has no separate schema concept for file mode

    def create_tables(self, schema_model: SchemaModel) -> None:
        for table in schema_model.tables:
            cols = []
            for c in table.columns:
                sql_type = _data_type_to_duckdb(c.data_type)
                pk = " PRIMARY KEY" if c.primary_key and len(table.primary_key) == 1 else ""
                cols.append(f'"{c.name}" {sql_type}{pk}')
            if table.primary_key and len(table.primary_key) > 1:
                cols.append(f"PRIMARY KEY ({', '.join(table.primary_key)})")
            sql = f"CREATE OR REPLACE TABLE \"{table.name}\" (\n  " + ",\n  ".join(cols) + "\n)"
            self._conn.execute(sql)

    def load_table(self, table_name: str, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0
        try:
            import pyarrow as pa
            cols = list(rows[0].keys())
            arrays = []
            for c in cols:
                vals = [r.get(c) for r in rows]
                try:
                    arr = pa.array(vals)
                except (pa.ArrowInvalid, TypeError):
                    arr = pa.array([str(v) if v is not None else None for v in vals])
                arrays.append(arr)
            arrow_tbl = pa.table(dict(zip(cols, arrays)))
            reg_name = "_load_tmp"
            self._conn.register(reg_name, arrow_tbl)
            self._conn.execute(f'INSERT INTO "{table_name}" SELECT * FROM {reg_name}')
            self._conn.unregister(reg_name)
            count = len(rows)
        except Exception:
            cols = list(rows[0].keys())
            placeholders = ",".join("?" for _ in cols)
            col_list = ",".join(f'"{c}"' for c in cols)
            sql = f'INSERT INTO "{table_name}" ({col_list}) VALUES ({placeholders})'
            count = 0
            for i in range(0, len(rows), self.batch_size):
                for row in rows[i : i + self.batch_size]:
                    vals = [row.get(c) for c in cols]
                    self._conn.execute(sql, vals)
                    count += 1
        self._load_counts[table_name] = count
        return count

    def validate_load(self) -> dict[str, Any]:
        result: dict[str, Any] = {"expected": dict(self._load_counts), "actual": {}, "success": True}
        for table_name in self._load_counts:
            r = self._conn.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()
            actual = r[0] if r else 0
            result["actual"][table_name] = actual
            if actual != self._load_counts[table_name]:
                result["success"] = False
        return result

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
