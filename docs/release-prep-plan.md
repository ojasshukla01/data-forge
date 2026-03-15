# Data Forge — Release-Prep Plan

This document defines the goals, gaps, docs strategy, and release-readiness checklist for the open-source launch and first tagged release.

---

## 1. Final Polish Goals

- **Open-source readiness**: CHANGELOG, versioning, GitHub release workflow, LICENSE, polished README
- **Trust**: Accurate API, testing, CI docs for contributors
- **Contributor experience**: Clear CONTRIBUTING, issue/PR templates
- **Docs cohesion**: docs/INDEX.md as hub; versioning and release docs linked
- **Website alignment**: In-app copy matches released product

---

## 2. Remaining User-Facing Gaps

| Gap | Action |
|-----|--------|
| No LICENSE file | Add MIT LICENSE at repo root |
| README not release-ready | Polish; badges; docs map; known limitations |
| CHANGELOG not referenced | Link from README; ensure Keep a Changelog style |
| No versioning guidance | Create docs/versioning.md |

---

## 3. Remaining Developer-Facing Gaps

| Gap | Action |
|-----|--------|
| No automated release workflow | Create .github/workflows/release.yml on v* |
| No docs/versioning.md | Create and link |
| Docs hub missing versioning/release | Add to docs/INDEX.md |
| documentation_issue template | Add .github/ISSUE_TEMPLATE/documentation_issue.md |

---

## 4. Docs to Canonicalize

- **Already canonical**: architecture-current-state, api-reference, testing, ci-cd, security, schema-studio, lineage-and-reproducibility, create-and-config, demo-walkthrough, release-checklist, release-process
- **To add**: docs/versioning.md
- **To ensure**: README links to versioning, CHANGELOG

---

## 5. Release-Readiness Checklist (This Pass)

- [ ] CHANGELOG.md Keep a Changelog style; linked from README
- [ ] docs/versioning.md created; linked from README, CONTRIBUTING, INDEX
- [ ] .github/workflows/release.yml on v* tags; validation + release
- [ ] README: badges, docs map, versioning link, known limitations
- [ ] LICENSE (MIT) at repo root
- [ ] Issue templates: bug, feature, documentation
- [ ] PR template verified
- [ ] docs/INDEX.md includes versioning and release
- [ ] Website/in-app content aligned
- [ ] Full validation passes

---

## 6. Intentionally Not Done in This Pass

- New product features
- Schema Studio ERD
- Run cancellation / retention automation
- Production deployment
- Cloud packaging
