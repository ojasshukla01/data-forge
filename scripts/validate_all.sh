#!/usr/bin/env bash
# Data Forge — full validation (backend tests, frontend tests, type-check, build)
# Run from repo root. Requires: uv, Node.js, npm

set -e

echo "=== Backend tests ==="
uv run python -m pytest -q

echo ""
echo "=== Frontend tests ==="
cd frontend && npm test

echo ""
echo "=== Frontend type-check ==="
npx tsc --noEmit

echo ""
echo "=== Frontend build ==="
npm run build
cd ..

echo ""
echo "All validation steps passed."
