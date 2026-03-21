Write-Host "Stopping node.exe processes to clear frontend file locks..."
taskkill /F /IM node.exe 2>$null | Out-Null

Write-Host "Removing frontend .next and cache directories if present..."
$paths = @("frontend/.next", "frontend/node_modules/.cache/next")
foreach ($p in $paths) {
  if (Test-Path $p) {
    Remove-Item $p -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  Removed $p"
  }
}

Write-Host "Done. You can now run frontend build commands again."
