# Data Forge make targets (optional; scripts/validate_all.* work without make)
# On Windows use scripts/run_demo.ps1 for demo; make demo-data uses run_demo.sh (Unix).

.PHONY: validate-all backend-check frontend-check e2e demo-data

validate-all:
	@echo "Running full validation (ruff, mypy, pytest, frontend tsc + test + build)..."
	@python -m ruff check src tests
	@python -m mypy src
	@python -m pytest tests -v --tb=short
	@if [ -f frontend/package.json ]; then \
		(cd frontend && npx tsc --noEmit && npm test -- --run && npm run build); \
	fi
	@echo "All checks passed."

backend-check:
	@python -m ruff check src tests
	@python -m mypy src
	@python -m pytest tests -v --tb=short

frontend-check:
	@if [ -f frontend/package.json ]; then \
		(cd frontend && npx tsc --noEmit && npm test && npm run build); \
	else \
		echo "No frontend/package.json, skipping frontend."; \
	fi

e2e:
	@echo "Running E2E (Playwright)..."
	@cd frontend && npm run e2e

demo-data:
	@echo "Running demo (generation + scenario + benchmark)..."
	@./scripts/run_demo.sh
