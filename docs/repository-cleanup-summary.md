# Repository Cleanup Summary

This document records what was removed, what was left in place, and why, during release-prep cleanup.

## Release-prep pass (current)

### Removed

- Implementation/audit duplicate docs: moved to archive or deleted in prior passes (see git history).
- No code removed in this pass.

### Left in place

- All source code, tests, frontend, scripts, and canonical docs.
- `scripts/extract_changelog.sh` — used by release workflow to extract CHANGELOG section for GitHub release notes.
- `docs/versioning.md`, `docs/release-prep-plan.md`, `docs/gap-analysis-next-phase.md` — release-prep planning.
- `.github/ISSUE_TEMPLATE/documentation_issue.md` — for reporting doc issues.
- `LICENSE` (MIT) — required for open-source.

### Conservative approach

- No dead-code removal in this pass.
- No unused-import cleanup unless verified safe.
- Focus on additive release-prep (CHANGELOG, versioning, release workflow, docs) rather than removal.
