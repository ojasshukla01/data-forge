# Full validation (same as CI): ruff, mypy, pytest (coverage), frontend tsc + lint + test + build
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

Write-Host "=== Backend: ruff ===" -ForegroundColor Cyan
python -m ruff check src tests
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n=== Backend: mypy ===" -ForegroundColor Cyan
python -m mypy src
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n=== Backend: pytest (with coverage) ===" -ForegroundColor Cyan
python -m pytest tests -v --tb=short --cov=src/data_forge --cov-report=term-missing
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (Test-Path "frontend\package.json") {
    Write-Host "`n=== Frontend: type-check ===" -ForegroundColor Cyan
    Set-Location frontend
    npx tsc --noEmit
    if ($LASTEXITCODE -ne 0) { Set-Location $root; exit $LASTEXITCODE }
    Write-Host "`n=== Frontend: lint ===" -ForegroundColor Cyan
    npm run lint
    if ($LASTEXITCODE -ne 0) { Set-Location $root; exit $LASTEXITCODE }
    Write-Host "`n=== Frontend: unit tests ===" -ForegroundColor Cyan
    npm test
    if ($LASTEXITCODE -ne 0) { Set-Location $root; exit $LASTEXITCODE }
    Write-Host "`n=== Frontend: build ===" -ForegroundColor Cyan
    npm run build
    if ($LASTEXITCODE -ne 0) { Set-Location $root; exit $LASTEXITCODE }
    Set-Location $root
}

Write-Host "`n=== All checks passed ===" -ForegroundColor Green
