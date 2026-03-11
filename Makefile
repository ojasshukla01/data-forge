# Data Forge make targets (optional; scripts/validate_all.* work without make)

.PHONY: validate-all backend-check frontend-check e2e

validate-all:
	@echo "Running full validation (ruff, pytest, frontend tsc + test + build)..."
	@python -m ruff check src tests
	@python -m pytest tests -v --tb=short
	@if [ -f frontend/package.json ]; then \
		(cd frontend && npx tsc --noEmit && npm test -- --run && npm run build); \
	fi
	@echo "All checks passed."

backend-check:
	@python -m ruff check src tests
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
