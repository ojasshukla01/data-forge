# Pre-commit CI checks (run from repo root)
# Usage: .\scripts\pre-commit-ci-checks.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

Write-Host "=== Backend: ruff ===" -ForegroundColor Cyan
python -m ruff check src tests
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n=== Backend: mypy ===" -ForegroundColor Cyan
python -m mypy src
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n=== Backend: pytest ===" -ForegroundColor Cyan
python -m pytest tests -q --tb=line
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n=== Frontend: tsc ===" -ForegroundColor Cyan
Set-Location frontend
npx tsc --noEmit
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n=== Frontend: unit tests ===" -ForegroundColor Cyan
npm test
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n=== Frontend: build ===" -ForegroundColor Cyan
npm run build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Set-Location $root
Write-Host "`n=== All CI checks passed ===" -ForegroundColor Green
