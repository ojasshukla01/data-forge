"""Airflow DAG template generation for Data Forge workflows."""

from pathlib import Path
from typing import Any, Literal

TemplateKind = Literal["generate_only", "generate_and_load", "generate_validate_and_load", "benchmark_pipeline"]

DAG_TEMPLATES: dict[TemplateKind, str] = {
    "generate_only": '''"""
Data Forge: generate-only DAG.
Requires: DATA_FORGE_PACK or DATA_FORGE_SCHEMA, DATA_FORGE_OUTPUT
"""
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id="data_forge_generate",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    tags=["data-forge", "synthetic"],
) as dag:
    gen = BashOperator(
        task_id="generate",
        bash_command="data-forge generate --pack {{ params.get('pack', 'saas_billing') }} "
                    "--scale {{ params.get('scale', 1000) }} "
                    "-o {{ params.get('output_dir', '/tmp/data_forge_output') }} "
                    "-f {{ params.get('format', 'parquet') }}",
    )
''',
    "generate_and_load": '''"""
Data Forge: generate and load to database.
Requires: DATA_FORGE_PACK, DATA_FORGE_OUTPUT, DATA_FORGE_DB_URI, DATA_FORGE_LOAD_TARGET
Env: DATA_FORGE_DB_URI, DATA_FORGE_LOAD_TARGET (sqlite|duckdb|postgres)
"""
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id="data_forge_generate_load",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    tags=["data-forge", "synthetic", "load"],
) as dag:
    gen = BashOperator(
        task_id="generate",
        bash_command="data-forge generate --pack {{ params.get('pack', 'saas_billing') }} "
                    "--scale {{ params.get('scale', 1000) }} "
                    "-o {{ params.get('output_dir', '/tmp/data_forge_output') }} "
                    "--load {{ var.value.get('data_forge_load_target', 'sqlite') }} "
                    "--db-uri {{ var.value.get('data_forge_db_uri', 'sqlite:///data.db') }}",
    )
''',
    "generate_validate_and_load": '''"""
Data Forge: generate, validate with GE, then load.
Requires: DATA_FORGE_OUTPUT, DATA_FORGE_GE_DIR, DATA_FORGE_DB_URI
Env: DATA_FORGE_GE_DIR (path to expectations), DATA_FORGE_DB_URI
"""
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id="data_forge_generate_validate_load",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    tags=["data-forge", "synthetic", "validation", "load"],
) as dag:
    gen = BashOperator(
        task_id="generate",
        bash_command="data-forge generate --pack {{ params.get('pack', 'saas_billing') }} "
                    "--scale {{ params.get('scale', 1000) }} -o {{ params.get('output_dir', '/tmp/data_forge_output') }} "
                    "--export-ge --ge-dir {{ params.get('ge_dir', './great_expectations') }}",
    )
    validate = BashOperator(
        task_id="validate_ge",
        bash_command="data-forge validate-ge --expectations {{ params.get('ge_dir', './great_expectations') }} "
                    "--data {{ params.get('output_dir', '/tmp/data_forge_output') }}",
    )
    load = BashOperator(
        task_id="load",
        bash_command="data-forge generate --pack {{ params.get('pack', 'saas_billing') }} "
                    "--scale {{ params.get('scale', 1000) }} -o {{ params.get('output_dir') }} "
                    "--load {{ var.value.get('data_forge_load_target', 'sqlite') }} "
                    "--db-uri {{ var.value.get('data_forge_db_uri', 'sqlite:///data.db') }}",
    )
    gen >> validate >> load
''',
    "benchmark_pipeline": '''"""
Data Forge: benchmark pipeline.
Requires: DATA_FORGE_PACK
"""
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id="data_forge_benchmark",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    tags=["data-forge", "benchmark"],
) as dag:
    benchmark = BashOperator(
        task_id="benchmark",
        bash_command="data-forge benchmark --pack {{ params.get('pack', 'saas_billing') }} "
                    "--scale {{ params.get('scale', 1000) }} "
                    "--iterations {{ params.get('iterations', 1) }} "
                    "--output-json {{ params.get('output_json', '/tmp/benchmark_results.json') }}",
    )
''',
}


def export_airflow(
    template: TemplateKind,
    output_dir: Path | str,
) -> dict[str, Any]:
    """
    Export Airflow DAG template to output_dir/dags/.
    Returns report: {enabled, template, output_dir, files_generated, paths}
    """
    output_dir = Path(output_dir)
    dags_dir = output_dir / "dags"
    dags_dir.mkdir(parents=True, exist_ok=True)

    content = DAG_TEMPLATES.get(template, DAG_TEMPLATES["generate_only"])
    file_map = {
        "generate_only": "data_forge_generate.py",
        "generate_and_load": "data_forge_generate_load.py",
        "generate_validate_and_load": "data_forge_generate_validate_load.py",
        "benchmark_pipeline": "data_forge_benchmark.py",
    }
    filename = file_map.get(template, "data_forge_generate.py")
    path = dags_dir / filename
    path.write_text(content, encoding="utf-8")

    return {
        "enabled": True,
        "template": template,
        "output_dir": str(output_dir),
        "files_generated": 1,
        "paths": [str(path)],
    }


def export_all_airflow_templates(output_dir: Path | str) -> dict[str, Any]:
    """Export all four DAG templates."""
    output_dir = Path(output_dir)
    dags_dir = output_dir / "dags"
    dags_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    for template in ("generate_only", "generate_and_load", "generate_validate_and_load", "benchmark_pipeline"):
        tpl: TemplateKind = template
        content = DAG_TEMPLATES[tpl]
        file_map = {
            "generate_only": "data_forge_generate.py",
            "generate_and_load": "data_forge_generate_load.py",
            "generate_validate_and_load": "data_forge_generate_validate_load.py",
            "benchmark_pipeline": "data_forge_benchmark.py",
        }
        path = dags_dir / file_map[tpl]
        path.write_text(content, encoding="utf-8")
        paths.append(str(path))
    return {
        "enabled": True,
        "template": "all",
        "output_dir": str(output_dir),
        "files_generated": len(paths),
        "paths": paths,
    }
