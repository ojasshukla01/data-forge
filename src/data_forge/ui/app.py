"""Streamlit UI for Data Forge."""

import streamlit as st
from pathlib import Path

from data_forge.models.generation import GenerationRequest
from data_forge.engine import run_generation, export_result
from data_forge.domain_packs import list_packs, get_pack
from data_forge.config import OutputFormat

st.set_page_config(
    page_title="Data Forge",
    page_icon="🔨",
    layout="wide",
)

st.title("🔨 Data Forge")
st.caption("Schema-aware synthetic data platform for realistic test data")

tab_pack, tab_custom, tab_about = st.tabs(["Domain pack", "Custom schema", "About"])

with tab_pack:
    st.subheader("Generate from a domain pack")
    packs = list_packs()
    pack_id = st.selectbox(
        "Pack",
        options=[p[0] for p in packs],
        format_func=lambda x: next(d for pid, d in packs if pid == x),
    )
    seed = st.number_input("Seed", value=42, min_value=0, step=1)
    scale = st.slider("Scale (base row count)", min_value=100, max_value=50_000, value=1000, step=100)
    anomalies = st.checkbox("Inject anomalies", value=False)
    anomaly_ratio = st.slider("Anomaly ratio", 0.0, 0.2, 0.02, 0.01) if anomalies else 0.0
    fmt = st.selectbox(
        "Export format",
        options=[f.value for f in OutputFormat],
        index=3,
    )
    if st.button("Generate", type="primary"):
        pack = get_pack(pack_id)
        if not pack:
            st.error(f"Pack not found: {pack_id}")
        else:
            req = GenerationRequest(
                schema_name=pack_id,
                seed=seed,
                scale=scale,
                include_anomalies=anomalies,
                anomaly_ratio=anomaly_ratio,
            )
            with st.spinner("Generating..."):
                result = run_generation(req, schema=pack.schema, rule_set=pack.rule_set)
            if result.success:
                out_dir = Path("output")
                out_dir.mkdir(parents=True, exist_ok=True)
                export_result(result, out_dir, fmt=fmt)
                st.success(f"Generated {sum(t.row_count for t in result.tables)} rows in {result.duration_seconds}s")
                st.json({
                    "tables": [{"name": t.table_name, "rows": t.row_count} for t in result.tables],
                    "quality": result.quality_report.get("summary", {}),
                })
                st.download_button(
                    "Download as ZIP",
                    data="See output/ directory",
                    file_name="data-forge-output.txt",
                    mime="text/plain",
                )
            else:
                st.error(result.errors)

with tab_custom:
    st.subheader("Custom schema + rules")
    schema_file = st.file_uploader("Schema (.sql or .json)", type=["sql", "json"])
    rules_file = st.file_uploader("Rules (.yaml)", type=["yaml", "yml"])
    if schema_file:
        seed_c = st.number_input("Seed (custom)", value=42, min_value=0, key="seed_c")
        scale_c = st.slider("Scale (custom)", 100, 50_000, 1000, key="scale_c")
        if st.button("Generate from upload", key="gen_custom"):
            import tempfile
            with tempfile.TemporaryDirectory() as tmp:
                schema_path = Path(tmp) / schema_file.name
                schema_path.write_bytes(schema_file.getvalue())
                rules_path = None
                if rules_file:
                    rules_path = Path(tmp) / rules_file.name
                    rules_path.write_bytes(rules_file.getvalue())
                req = GenerationRequest(schema_name="custom", seed=seed_c, scale=scale_c)
                result = run_generation(req, schema_path=schema_path, rules_path=rules_path)
            if result.success:
                out_dir = Path("output")
                out_dir.mkdir(parents=True, exist_ok=True)
                export_result(result, out_dir, fmt="parquet")
                st.success("Done. Check output/ directory.")
            else:
                st.error(result.errors)

with tab_about:
    st.markdown("""
    **Data Forge** generates business-valid, cross-table, time-consistent, privacy-safe test data.

    - **Schema-aware**: Import from SQL DDL, JSON Schema, or use domain packs.
    - **Relational**: PK/FK integrity across tables.
    - **Rules**: YAML business rules and distribution hints.
    - **Export**: CSV, JSON, Parquet, SQL.
    - **Quality report**: Referential integrity and basic stats.

    Use the CLI for CI and scripting:
    ```bash
    data-forge generate --pack saas_billing --scale 5000 -o output -f parquet
    data-forge generate -s schemas/custom.sql -r rules/custom.yaml --seed 42
    ```
    """)


def main() -> None:
    pass  # Streamlit runs by script execution


if __name__ == "__main__":
    main()
