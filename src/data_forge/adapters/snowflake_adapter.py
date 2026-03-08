"""Snowflake adapter using snowflake-connector-python."""

from typing import Any

from data_forge.adapters.base import BaseDatabaseAdapter
from data_forge.models.schema import SchemaModel, DataType


def _data_type_to_snowflake(dt: DataType) -> str:
    m = {
        DataType.STRING: "VARCHAR",
        DataType.TEXT: "VARCHAR",
        DataType.INTEGER: "NUMBER",
        DataType.BIGINT: "NUMBER",
        DataType.FLOAT: "FLOAT",
        DataType.DECIMAL: "DECIMAL(18,4)",
        DataType.BOOLEAN: "BOOLEAN",
        DataType.DATE: "DATE",
        DataType.DATETIME: "TIMESTAMP_NTZ",
        DataType.TIMESTAMP: "TIMESTAMP_NTZ",
        DataType.UUID: "VARCHAR",
        DataType.EMAIL: "VARCHAR",
        DataType.PHONE: "VARCHAR",
        DataType.URL: "VARCHAR",
        DataType.JSON: "VARIANT",
        DataType.ENUM: "VARCHAR",
        DataType.CURRENCY: "FLOAT",
        DataType.PERCENT: "FLOAT",
    }
    return m.get(dt, "VARCHAR")


class SnowflakeAdapter(BaseDatabaseAdapter):
    """Snowflake adapter using snowflake-connector-python. Uses structured connection params."""

    def __init__(
        self,
        uri: str = "",
        batch_size: int = BaseDatabaseAdapter.DEFAULT_BATCH_SIZE,
        *,
        account: str | None = None,
        user: str | None = None,
        password: str | None = None,
        warehouse: str | None = None,
        database: str | None = None,
        schema: str | None = None,
        role: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(uri or "snowflake", batch_size)
        self.account = account or kwargs.get("snowflake_account") or ""
        self.user = user or kwargs.get("snowflake_user") or ""
        self.password = password or kwargs.get("snowflake_password") or ""
        self.warehouse = warehouse or kwargs.get("snowflake_warehouse") or ""
        self.database = database or kwargs.get("snowflake_database") or ""
        self.schema_name = schema or kwargs.get("snowflake_schema") or "PUBLIC"
        self.role = role or kwargs.get("snowflake_role") or ""
        self._conn: Any = None

    def _check_credentials(self) -> None:
        if not self.account or not self.user or not self.password:
            raise ValueError(
                "Snowflake credentials missing. Set DATA_FORGE_SNOWFLAKE_ACCOUNT, "
                "DATA_FORGE_SNOWFLAKE_USER, DATA_FORGE_SNOWFLAKE_PASSWORD "
                "or pass --sf-account, --sf-user, --sf-password."
            )

    def connect(self) -> None:
        self._check_credentials()
        import snowflake.connector
        self._conn = snowflake.connector.connect(
            account=self.account,
            user=self.user,
            password=self.password,
            warehouse=self.warehouse or None,
            database=self.database or None,
            schema=self.schema_name,
            role=self.role or None,
        )

    def create_schema(self, schema_model: SchemaModel) -> None:
        if self.database:
            with self._conn.cursor() as cur:
                cur.execute(f'USE DATABASE "{self.database}"')
                cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{self.schema_name}"')
                cur.execute(f'USE SCHEMA "{self.schema_name}"')

    def create_tables(self, schema_model: SchemaModel) -> None:
        with self._conn.cursor() as cur:
            if self.database:
                cur.execute(f'USE DATABASE "{self.database}"')
            cur.execute(f'USE SCHEMA "{self.schema_name}"')
            for table in schema_model.tables:
                cols = []
                for c in table.columns:
                    sql_type = _data_type_to_snowflake(c.data_type)
                    nn = " NOT NULL" if not c.nullable and c.primary_key else ""
                    cols.append(f'"{c.name}" {sql_type}{nn}')
                if table.primary_key:
                    cols.append(f"PRIMARY KEY ({', '.join(table.primary_key)})")
                cur.execute(f'DROP TABLE IF EXISTS "{table.name}"')
                cur.execute(
                    f'CREATE TABLE "{table.name}" (\n  ' + ",\n  ".join(cols) + "\n)"
                )
        self._conn.commit()

    def _qualified(self, table_name: str) -> str:
        if self.database and self.schema_name:
            return f'"{self.database}"."{self.schema_name}"."{table_name}"'
        return f'"{table_name}"'

    def load_table(self, table_name: str, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0
        cols = list(rows[0].keys())
        col_list = ",".join(f'"{c}"' for c in cols)
        placeholders = ",".join("%s" for _ in cols)
        qualified = self._qualified(table_name)
        sql = f'INSERT INTO {qualified} ({col_list}) VALUES ({placeholders})'
        count = 0
        with self._conn.cursor() as cur:
            for i in range(0, len(rows), self.batch_size):
                batch = rows[i : i + self.batch_size]
                for row in batch:
                    vals = [row.get(c) for c in cols]
                    cur.execute(sql, vals)
                    count += 1
        self._conn.commit()
        self._load_counts[table_name] = count
        return count

    def validate_load(self) -> dict[str, Any]:
        result: dict[str, Any] = {"expected": dict(self._load_counts), "actual": {}, "success": True}
        with self._conn.cursor() as cur:
            for table_name in self._load_counts:
                qualified = self._qualified(table_name)
                cur.execute(f"SELECT COUNT(*) FROM {qualified}")
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
