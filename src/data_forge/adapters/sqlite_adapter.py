"""SQLite adapter using sqlite3."""

import sqlite3
from typing import Any

from data_forge.adapters.base import BaseDatabaseAdapter
from data_forge.models.schema import SchemaModel, DataType


def _data_type_to_sqlite(dt: DataType) -> str:
    m = {
        DataType.STRING: "TEXT",
        DataType.TEXT: "TEXT",
        DataType.INTEGER: "INTEGER",
        DataType.BIGINT: "INTEGER",
        DataType.FLOAT: "REAL",
        DataType.DECIMAL: "REAL",
        DataType.BOOLEAN: "INTEGER",
        DataType.DATE: "TEXT",
        DataType.DATETIME: "TEXT",
        DataType.TIMESTAMP: "TEXT",
        DataType.UUID: "TEXT",
        DataType.EMAIL: "TEXT",
        DataType.PHONE: "TEXT",
        DataType.URL: "TEXT",
        DataType.JSON: "TEXT",
        DataType.ENUM: "TEXT",
        DataType.CURRENCY: "REAL",
        DataType.PERCENT: "REAL",
    }
    return m.get(dt, "TEXT")


class SQLiteAdapter(BaseDatabaseAdapter):
    """SQLite adapter using sqlite3 standard library."""

    def connect(self) -> None:
        self._connection = sqlite3.connect(self.uri)

    def create_schema(self, schema_model: SchemaModel) -> None:
        pass  # SQLite has no schema/namespace

    def create_tables(self, schema_model: SchemaModel) -> None:
        cur = self._connection.cursor()
        for table in schema_model.tables:
            cols = []
            for c in table.columns:
                sql_type = _data_type_to_sqlite(c.data_type)
                pk = " PRIMARY KEY" if c.primary_key and len(table.primary_key) == 1 else ""
                nn = " NOT NULL" if not c.nullable and c.primary_key else ""
                cols.append(f'"{c.name}" {sql_type}{pk}{nn}')
            if table.primary_key and len(table.primary_key) > 1:
                cols.append(f"PRIMARY KEY ({', '.join(table.primary_key)})")
            sql = f"CREATE TABLE IF NOT EXISTS \"{table.name}\" (\n  " + ",\n  ".join(cols) + "\n)"
            cur.execute(f"DROP TABLE IF EXISTS \"{table.name}\"")
            cur.execute(sql)
        self._connection.commit()
        cur.close()

    def load_table(self, table_name: str, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0
        cols = list(rows[0].keys())
        placeholders = ",".join("?" for _ in cols)
        col_list = ",".join(f'"{c}"' for c in cols)
        sql = f'INSERT INTO "{table_name}" ({col_list}) VALUES ({placeholders})'
        cur = self._connection.cursor()
        count = 0
        for i in range(0, len(rows), self.batch_size):
            batch = rows[i : i + self.batch_size]
            batch_vals = [[row.get(c) for c in cols] for row in batch]
            cur.executemany(sql, batch_vals)
            count += len(batch)
        self._connection.commit()
        cur.close()
        self._load_counts[table_name] = count
        return count

    def validate_load(self) -> dict[str, Any]:
        cur = self._connection.cursor()
        result: dict[str, Any] = {"expected": dict(self._load_counts), "actual": {}, "success": True}
        for table_name in self._load_counts:
            cur.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            actual = cur.fetchone()[0]
            result["actual"][table_name] = actual
            if actual != self._load_counts[table_name]:
                result["success"] = False
        cur.close()
        return result

    def close(self) -> None:
        if self._connection:
            self._connection.close()
            self._connection = None
