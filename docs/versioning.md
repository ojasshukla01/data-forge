# Versioning

Data Forge uses **Semantic Versioning** (major.minor.patch) for tagged releases.

## When to bump

| Bump | When |
|------|------|
| **Major** | Breaking API or config changes; incompatible changes |
| **Minor** | New features, new domain packs, significant UX; backward compatible |
| **Patch** | Bug fixes, docs, small improvements; backward compatible |

Pre-1.0, minor versions may include new capabilities; patch for fixes and polish.

## Tag format

- Format: `v0.1.0`, `v1.0.0`, etc.
- Always prefix with `v`
- Use three numbers: major.minor.patch

## Before tagging

1. Run full validation: `make validate-all` (and `make e2e` with API + frontend running)
2. Update **CHANGELOG.md**: move "Unreleased" items into `[X.Y.Z] - YYYY-MM-DD`
3. Bump `version` in `pyproject.toml` and `src/data_forge/__init__.py` (and frontend `package.json` if UI version is exposed)

## Release notes

- Use the matching section from **CHANGELOG.md** for GitHub release notes
- The release workflow extracts it automatically when creating a release from a tag

## See also

- [Release process](release-process.md) — tagging steps, CHANGELOG workflow
- [Release checklist](release-checklist.md) — validation and sanity checks
