# Dependency audit

Run periodically to check for vulnerable or outdated packages.

## Backend (Python)

```bash
# List outdated packages
pip list --outdated

# Security audit (requires pip-audit)
pip install pip-audit
pip-audit

# With uv
uv pip list --outdated
uv pip compile pyproject.toml -o requirements.txt
uv pip-audit
```

## Frontend (Node)

```bash
cd frontend
npm outdated
npm audit
```

## CI

GitHub Actions runs optional `pip-audit` (backend) and `npm audit` (frontend) with `continue-on-error: true`. Fix high-severity issues when reported.
