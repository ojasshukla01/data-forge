#!/usr/bin/env bash
# Data Forge — one-command demo: generates sample outputs (no cloud credentials)
# Run from repo root. Outputs go to demo_output/

set -e

OUT="demo_output"
mkdir -p "$OUT"

echo "Demo: standard generation (saas_billing, Parquet)..."
uv run data-forge generate --pack saas_billing --scale 500 -o "$OUT" -f parquet

echo "Demo: scenario-style run (ecommerce, CSV)..."
uv run data-forge generate --pack ecommerce --scale 300 -o "$OUT" -f csv

echo "Demo: benchmark run..."
uv run data-forge benchmark --pack saas_billing --scale 1000 --iterations 1 --output-json "$OUT/bench_result.json"

echo "Demo outputs in $OUT/"
