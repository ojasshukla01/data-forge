# Data Forge — local validation and demo
# Requires: uv (backend), Node.js + npm (frontend)
# Usage: make <target>

.PHONY: backend-test backend-lint backend-typecheck frontend-test frontend-typecheck frontend-build validate-all demo-data help

help:
	@echo "Data Forge targets:"
	@echo "  backend-test        Run backend test suite (pytest)"
	@echo "  backend-lint        Run ruff on src and tests"
	@echo "  backend-typecheck   Run mypy on src"
	@echo "  frontend-test       Run frontend tests (Vitest)"
	@echo "  frontend-typecheck  Run frontend TypeScript check"
	@echo "  frontend-build      Production build of frontend"
	@echo "  validate-all       Run backend tests, frontend tests, type-check, and build (same as CI)"
	@echo "  demo-data           Generate demo outputs (standard + scenario-style + benchmark)"

backend-test:
	uv run python -m pytest -q

backend-lint:
	uv run ruff check src tests

backend-typecheck:
	uv run python -m mypy src

frontend-test:
	cd frontend && npm test

frontend-typecheck:
	cd frontend && npx tsc --noEmit

frontend-build:
	cd frontend && npm run build

validate-all: backend-test frontend-test frontend-typecheck frontend-build
	@echo "All validation steps passed."

demo-data:
	@echo "Running demo: standard generation, scenario-style run, benchmark..."
	uv run data-forge generate --pack saas_billing --scale 500 -o demo_output -f parquet
	uv run data-forge generate --pack ecommerce --scale 300 -o demo_output -f csv
	uv run data-forge benchmark --pack saas_billing --scale 1000 --iterations 1 --output-json demo_output/bench_result.json
	@echo "Demo outputs written to demo_output/"
