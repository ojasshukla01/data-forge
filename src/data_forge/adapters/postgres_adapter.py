"""PostgreSQL adapter using psycopg."""

from typing import Any

from data_forge.adapters.base import BaseDatabaseAdapter
from data_forge.models.schema import SchemaModel, DataType


def _data_type_to_postgres(dt: DataType) -> str:
    m = {
        DataType.STRING: "TEXT",
        DataType.TEXT: "TEXT",
        DataType.INTEGER: "INTEGER",
        DataType.BIGINT: "BIGINT",
        DataType.FLOAT: "DOUBLE PRECISION",
        DataType.DECIMAL: "DECIMAL(18,4)",
        DataType.BOOLEAN: "BOOLEAN",
        DataType.DATE: "DATE",
        DataType.DATETIME: "TIMESTAMP",
        DataType.TIMESTAMP: "TIMESTAMP",
        DataType.UUID: "UUID",
        DataType.EMAIL: "TEXT",
        DataType.PHONE: "TEXT",
        DataType.URL: "TEXT",
        DataType.JSON: "JSONB",
        DataType.ENUM: "TEXT",
        DataType.CURRENCY: "DOUBLE PRECISION",
        DataType.PERCENT: "DOUBLE PRECISION",
    }
    return m.get(dt, "TEXT")


class PostgresAdapter(BaseDatabaseAdapter):
    """PostgreSQL adapter using psycopg."""

    def __init__(self, uri: str, batch_size: int = BaseDatabaseAdapter.DEFAULT_BATCH_SIZE) -> None:
        super().__init__(uri, batch_size)
        self._conn: Any = None

    def connect(self) -> None:
        import psycopg
        self._conn = psycopg.connect(self.uri)

    def create_schema(self, schema_model: SchemaModel) -> None:
        schema_name = schema_model.name.replace("-", "_").replace(" ", "_") or "public"
        if schema_name != "public":
            with self._conn.cursor() as cur:
                cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
            self._conn.commit()

    def create_tables(self, schema_model: SchemaModel) -> None:
        with self._conn.cursor() as cur:
            for table in schema_model.tables:
                cols = []
                for c in table.columns:
                    sql_type = _data_type_to_postgres(c.data_type)
                    pk = " PRIMARY KEY" if c.primary_key and len(table.primary_key) == 1 else ""
                    nn = " NOT NULL" if not c.nullable and c.primary_key else ""
                    cols.append(f'"{c.name}" {sql_type}{pk}{nn}')
                if table.primary_key and len(table.primary_key) > 1:
                    cols.append(f"PRIMARY KEY ({', '.join(table.primary_key)})")
                sql = f'CREATE TABLE IF NOT EXISTS "{table.name}" (\n  ' + ",\n  ".join(cols) + "\n)"
                cur.execute(f'DROP TABLE IF EXISTS "{table.name}" CASCADE')
                cur.execute(sql)
        self._conn.commit()

    def load_table(self, table_name: str, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0
        cols = list(rows[0].keys())
        col_list = ",".join(f'"{c}"' for c in cols)
        placeholders = ",".join("%s" for _ in cols)
        sql = f'INSERT INTO "{table_name}" ({col_list}) VALUES ({placeholders})'
        count = 0
        with self._conn.cursor() as cur:
            for i in range(0, len(rows), self.batch_size):
                batch = rows[i : i + self.batch_size]
                batch_vals = [[row.get(c) for c in cols] for row in batch]
                cur.executemany(sql, batch_vals)
                count += len(batch)
        self._conn.commit()
        self._load_counts[table_name] = count
        return count

    def validate_load(self) -> dict[str, Any]:
        result: dict[str, Any] = {"expected": dict(self._load_counts), "actual": {}, "success": True}
        with self._conn.cursor() as cur:
            for table_name in self._load_counts:
                cur.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                r = cur.fetchone()
                actual = r[0] if r else 0
                result["actual"][table_name] = actual
                if actual != self._load_counts[table_name]:
                    result["success"] = False
        return result

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
