# Dependency audit

Run periodically to check for vulnerable or outdated packages.

## Reproducible installs

- **Backend:** Commit `uv.lock` (from `uv lock` or `python -m uv lock`) for reproducible Python installs. CI uses `uv sync --extra dev`.
- **Frontend:** Commit `package-lock.json` for reproducible npm installs. Run `npm install` to update.

## Backend (Python)

```bash
# List outdated packages
pip list --outdated

# Security audit (requires pip-audit)
pip install pip-audit
pip-audit

# With uv
python -m uv pip list --outdated
python -m uv pip-audit
```

## Frontend (Node)

```bash
cd frontend
npm outdated
npm audit
```

## CI

GitHub Actions runs optional `pip-audit` (backend) and `npm audit` (frontend) with `continue-on-error: true`. Fix high-severity issues when reported.
