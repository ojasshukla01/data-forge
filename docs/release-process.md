# Release process

Lightweight guide for maintainers preparing a tagged release.

## Versioning

- We use **Semantic Versioning** (major.minor.patch) for tagged releases.
- **Major**: Breaking API or config changes.
- **Minor**: New features, new domain packs, significant UX; backward compatible.
- **Patch**: Bug fixes, docs, small improvements; backward compatible.

Pre-1.0, minor versions may include new capabilities; patch for fixes and polish.

## Before tagging

1. **Validation** — Ensure CI is green and local validation passes:
   ```bash
   make validate-all
   ```
2. **CHANGELOG** — Move “Unreleased” items into a new version section (e.g. `[0.2.0] - 2025-03-15`) and add the release date.
3. **Version bump** — Update `version` in `pyproject.toml` (and frontend `package.json` if we expose a UI version) to match the tag.

## Tag and release

1. Commit CHANGELOG and version bumps.
2. Create an annotated tag:
   ```bash
   git tag -a v0.2.0 -m "Release v0.2.0"
   git push origin v0.2.0
   ```
3. On GitHub: create a **Release** from the tag and paste the relevant CHANGELOG section into the release notes.

## After release

- Start a new **Unreleased** section in CHANGELOG for the next cycle.

No automated publish step is required; the repo is source-only. Users install via clone + `uv sync` / `npm install` or future packaging if added.
