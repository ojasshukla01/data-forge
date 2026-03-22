#!/usr/bin/env bash
# Full validation (same as CI): ruff, mypy, pytest (coverage), frontend tsc + lint + test + build
set -e
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"

echo "=== Backend: ruff ==="
python -m ruff check src tests

echo ""
echo "=== Backend: mypy ==="
python -m mypy src

echo ""
echo "=== Backend: pytest (with coverage) ==="
python -m pytest tests -v --tb=short --cov=src/data_forge --cov-report=term-missing

if [ -f frontend/package.json ]; then
  echo ""
  echo "=== Frontend: type-check ==="
  (cd frontend && npx tsc --noEmit)
  echo ""
  echo "=== Frontend: lint ==="
  (cd frontend && npm run lint)
  echo ""
  echo "=== Frontend: unit tests ==="
  (cd frontend && npm test)
  echo ""
  echo "=== Frontend: build ==="
  (cd frontend && npm run build)
fi

echo ""
echo "=== All checks passed ==="
