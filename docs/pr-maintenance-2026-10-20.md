# Pull-request maintenance — October 20, 2026

Two existing baseline problems block otherwise independent PRs:

- SQLAlchemy query typing in `filing_schedule.py` fails fresh mypy runs on main.
  Extract the compatibility fix from `5de4b25` (PR #92) without adopting the Q&A
  feature. The query and scheduler behavior are unchanged.
- The production npm audit reports `follow-redirects` 1.16.0 as vulnerable
  (GHSA-q3jh-wrc6-jgq8 and GHSA-8r9p-f939-6h3c). Update only its lockfile resolution
  to 1.16.1. No direct dependency range, CI threshold or workflow is relaxed.

Local verification uses disposable containers, not the running demo database:

- Backend Ruff lint/format and mypy pass; 34 filing/following tests pass.
- Frontend Node 20 clean install, lint, format, types, 82 tests and build pass.
- Production npm audit reports zero vulnerabilities. The full tooling audit still
  reports existing development-only findings; coordinated tooling work remains #85.
- Node 20 emits the existing jest-dom Node >=22 engine warning. PR #88's isolated
  Node 25 type upgrade was closed in favor of #85's coordinated runtime decision.

GitHub review and CI/security checks must pass before integration. No story is
accepted, no live-model evaluation is claimed, and no deployment is performed.
