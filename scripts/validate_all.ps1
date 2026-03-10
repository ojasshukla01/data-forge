# Data Forge — full validation (backend tests, frontend tests, type-check, build)
# Run from repo root. Requires: uv, Node.js, npm

$ErrorActionPreference = "Stop"

Write-Host "=== Backend tests ===" -ForegroundColor Cyan
uv run python -m pytest -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n=== Frontend tests ===" -ForegroundColor Cyan
Set-Location frontend
npm test
if ($LASTEXITCODE -ne 0) { Set-Location ..; exit $LASTEXITCODE }

Write-Host "`n=== Frontend type-check ===" -ForegroundColor Cyan
npx tsc --noEmit
if ($LASTEXITCODE -ne 0) { Set-Location ..; exit $LASTEXITCODE }

Write-Host "`n=== Frontend build ===" -ForegroundColor Cyan
npm run build
$buildExit = $LASTEXITCODE
Set-Location ..
if ($buildExit -ne 0) { exit $buildExit }

Write-Host "`nAll validation steps passed." -ForegroundColor Green
