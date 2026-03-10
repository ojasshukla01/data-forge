# Data Forge — one-command demo: generates sample outputs (no cloud credentials)
# Run from repo root. Outputs go to demo_output/

$ErrorActionPreference = "Stop"

$out = "demo_output"
if (-not (Test-Path $out)) { New-Item -ItemType Directory -Path $out | Out-Null }

Write-Host "Demo: standard generation (saas_billing, Parquet)..." -ForegroundColor Cyan
uv run data-forge generate --pack saas_billing --scale 500 -o $out -f parquet

Write-Host "Demo: scenario-style run (ecommerce, CSV)..." -ForegroundColor Cyan
uv run data-forge generate --pack ecommerce --scale 300 -o $out -f csv

Write-Host "Demo: benchmark run..." -ForegroundColor Cyan
uv run data-forge benchmark --pack saas_billing --scale 1000 --iterations 1 --output-json "$out/bench_result.json"

Write-Host "Demo outputs in $out/" -ForegroundColor Green
