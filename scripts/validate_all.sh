#!/usr/bin/env bash
# Full validation (same as CI): ruff, mypy, pytest, frontend tsc + test + build
set -e
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"

echo "=== Backend: ruff ==="
python -m ruff check src tests

echo ""
echo "=== Backend: mypy ==="
python -m mypy src

echo ""
echo "=== Backend: pytest ==="
python -m pytest tests -v --tb=short

if [ -f frontend/package.json ]; then
  echo ""
  echo "=== Frontend: type-check ==="
  (cd frontend && npx tsc --noEmit)
  echo ""
  echo "=== Frontend: unit tests ==="
  (cd frontend && npm test)
  echo ""
  echo "=== Frontend: build ==="
  (cd frontend && npm run build)
fi

echo ""
echo "=== All checks passed ==="
