"""BigQuery adapter using google-cloud-bigquery."""

from datetime import date, datetime
from typing import Any

from data_forge.adapters.base import BaseDatabaseAdapter
from data_forge.models.schema import SchemaModel, DataType


def _to_json_safe(obj: Any) -> Any:
    """Convert to JSON-serializable form for BigQuery insert_rows_json."""
    if obj is None:
        return None
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_json_safe(x) for x in obj]
    return obj


def _data_type_to_bigquery(dt: DataType) -> str:
    """Map DataType to BigQuery SQL type. Nested/JSON uses STRING fallback if needed."""
    m = {
        DataType.STRING: "STRING",
        DataType.TEXT: "STRING",
        DataType.INTEGER: "INT64",
        DataType.BIGINT: "INT64",
        DataType.FLOAT: "FLOAT64",
        DataType.DECIMAL: "FLOAT64",
        DataType.BOOLEAN: "BOOL",
        DataType.DATE: "DATE",
        DataType.DATETIME: "TIMESTAMP",
        DataType.TIMESTAMP: "TIMESTAMP",
        DataType.UUID: "STRING",
        DataType.EMAIL: "STRING",
        DataType.PHONE: "STRING",
        DataType.URL: "STRING",
        DataType.JSON: "JSON",  # BigQuery JSON type; fallback to STRING if unsupported
        DataType.ENUM: "STRING",
        DataType.CURRENCY: "FLOAT64",
        DataType.PERCENT: "FLOAT64",
    }
    return m.get(dt, "STRING")


class BigQueryAdapter(BaseDatabaseAdapter):
    """BigQuery adapter using google-cloud-bigquery. Uses project and dataset."""

    def __init__(
        self,
        uri: str = "",
        batch_size: int = BaseDatabaseAdapter.DEFAULT_BATCH_SIZE,
        *,
        project: str | None = None,
        dataset: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(uri or "bigquery", batch_size)
        self.project = project or kwargs.get("bigquery_project") or ""
        self.dataset_id = dataset or kwargs.get("bigquery_dataset") or ""
        self._client: Any = None

    def _check_config(self) -> None:
        if not self.project or not self.dataset_id:
            raise ValueError(
                "BigQuery config missing. Set DATA_FORGE_BIGQUERY_PROJECT, "
                "DATA_FORGE_BIGQUERY_DATASET or pass --bq-project, --bq-dataset."
            )

    def connect(self) -> None:
        self._check_config()
        from google.cloud import bigquery
        self._client = bigquery.Client(project=self.project)

    def create_schema(self, schema_model: SchemaModel) -> None:
        from google.cloud import bigquery
        dataset_ref = bigquery.Dataset(f"{self.project}.{self.dataset_id}")
        try:
            self._client.create_dataset(dataset_ref, exists_ok=True)
        except Exception:
            pass  # Dataset may already exist

    def create_tables(self, schema_model: SchemaModel) -> None:
        from google.cloud import bigquery
        for table in schema_model.tables:
            cols = []
            for c in table.columns:
                bq_type = _data_type_to_bigquery(c.data_type)
                cols.append(bigquery.SchemaField(c.name, bq_type, mode="REQUIRED" if c.primary_key and not c.nullable else "NULLABLE"))
            table_ref = f"{self.project}.{self.dataset_id}.{table.name}"
            table_obj = bigquery.Table(table_ref, schema=cols)
            self._client.delete_table(table_ref, not_found_ok=True)
            self._client.create_table(table_obj)

    def load_table(self, table_name: str, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0
        table_ref = f"{self.project}.{self.dataset_id}.{table_name}"
        safe_rows = [_to_json_safe(dict(r)) for r in rows]
        errors = self._client.insert_rows_json(table_ref, safe_rows)
        if errors:
            raise RuntimeError(f"BigQuery insert errors: {errors[:3]}")  # First few
        self._load_counts[table_name] = len(rows)
        return len(rows)

    def validate_load(self) -> dict[str, Any]:
        result: dict[str, Any] = {"expected": dict(self._load_counts), "actual": {}, "success": True}
        for table_name in self._load_counts:
            table_ref = f"{self.project}.{self.dataset_id}.{table_name}"
            query = f'SELECT COUNT(*) as cnt FROM `{table_ref}`'
            row = next(self._client.query(query).result(), None)
            actual = row.cnt if row else 0
            result["actual"][table_name] = actual
            if actual != self._load_counts[table_name]:
                result["success"] = False
        return result

    def close(self) -> None:
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None
