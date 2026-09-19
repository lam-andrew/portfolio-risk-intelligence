# Software Testing Report — Orbit

**Project:** Orbit (repository: `portfolio-risk-intelligence`)
**Course:** SWENG 894 — Penn State MSE Capstone
**Status:** Living document. Created Week 2; updated as test coverage grows.

> Initial version. This document grows with the test suite; the final version is a Week 14
> deliverable, but it is maintained continuously rather than assembled at the end.

---

## 1. Test strategy

Testing is organized as a pyramid, weighted toward fast, deterministic tests at the bottom.

| Level | Tool | What it covers | Speed |
|---|---|---|---|
| **Unit — engine** | pytest | Risk math in isolation: volatility, correlation, concentration, drawdown. Pure functions, no I/O. | Milliseconds |
| **Unit — frontend** | Vitest + React Testing Library | Component rendering, formatting, interaction, empty/error states. | Seconds |
| **Integration — API** | pytest + FastAPI `TestClient` | Full request/response cycle through real routes, real persistence, real caching, with a fake market-data provider. | Seconds |
| **Integration — stack** | Docker Compose in CI | The whole stack boots and services communicate. | Minutes |
| **Manual / exploratory** | Postman, browser | API contract exploration; visual verification against live market data. | Ad hoc |

### Guiding principles

1. **The algorithmic core is tested against independently known answers**, not against its own
   output. Correlation results are cross-checked against NumPy's `corrcoef`; the Herfindahl
   index is checked against a hand-computed value. A test that only asserts the code does what
   the code does would pass even if the mathematics were wrong.
2. **No network in the automated suite.** A fake market-data provider is injected, so tests are
   deterministic, run without an API key, and do not consume the provider's rate-limited quota.
3. **Bugs become regression tests.** Every defect found in manual verification is reproduced as
   a failing test before it is fixed, and the fix is confirmed by that test passing.
4. **A regression test must be shown to fail.** For concurrency and caching defects in
   particular, a test is only trusted once it has been observed failing against the unfixed
   code. A concurrency test that passes for the wrong reason is worse than no test.

---

## 2. What the automated suite covers today

As of 2026-09-08: **236 automated tests** (183 backend, 53 frontend), all passing locally
at source revision `c065aef`. The same suites run in CI on every push and pull request.
The local backend used Python 3.13, SQLite test databases, and FakeProvider; CI uses
the Python 3.12 container image. A Starlette/httpx TestClient deprecation warning was
emitted locally. No coverage percentage or manual UAT result was measured in this run.

[Sprint 1 test specifications](sprint1-tests.md) provide 18 initial specifications,
requirement/acceptance mappings, exact automation references, and pending acceptance
procedures for all six Sprint 1 stories. Specification IDs were created September 8; the
automated tests themselves are existing tests, not newly written for the report.

| Requirement | Covered by |
|---|---|
| FR-1 (add holding) | API tests for valid input, unrecognized ticker, duplicate ticker, invalid quantity |
| FR-2, FR-3 (CSV import + validation) | Parser tests against per-brokerage fixtures (Fidelity, Schwab, Vanguard), plus preamble rows, ranked header aliases, currency formatting, structural total rows, per-row error reporting |
| FR-4 (manage holdings) | API CRUD tests; frontend interaction tests for inline edit and confirm-before-delete |
| FR-5, FR-6 (retrieve + cache) | Cache freshness (TTL), cache coverage (a narrow earlier fetch must not satisfy a wider request), provider-failure degradation, single-flight concurrent fetch |
| FR-7 (volatility) | Engine unit tests against hand-computed values; portfolio volatility via covariance; diversification benefit |
| FR-8 (correlation) | Engine unit tests cross-checked against NumPy; most/least correlated pairs; identical-series and constant-series edge cases |
| FR-9 (concentration) | Hand-computed Herfindahl index and effective holdings; overweight detection; overlapping-exposure grouping |
| FR-10 (drawdown) | Synthetic peak/trough/recovery series; unrecovered episodes reported rather than dropped |
| FR-12 (dashboard) | Frontend component and routing tests; loading, empty, and error states |
| FR-15 (authenticate) | Unauthenticated rejection on every portfolio route; session lifecycle; logout revocation; ownership isolation; uniform response for unknown email vs wrong password |
| AR-1 (containerized) | CI starts Compose and asserts backend/database connectivity via /api/health; browser-to-API UAT remains pending |
| AR-2 (decoupled engines) | Engine imports inspected September 8; API namespace regression passes; new-engine extension demonstration remains pending |

### Not yet covered

FR-14 (grounded Q&A) is a Sprint 3 story whose tests will be
written with those features. Early US-9 / FR-11 stress-test coverage is recorded in
[the stress-test specifications](us9-stress-tests.md); its Sprint 3 assignment is unchanged.
FR-14 in particular needs a **grounding test**:
every claim in an answer must be traceable to retrieved source text, which is a correctness
property, not a style preference.

---

## 3. Quality gates in CI

Every push and pull request runs, and must pass before merge:

| Gate | Tool | Enforces |
|---|---|---|
| Backend lint | Ruff | Style and common defect patterns |
| Backend types | mypy (strict) | Type correctness |
| Backend tests | pytest | Behavior |
| Frontend lint | ESLint | Style and defect patterns |
| Frontend format | Prettier | Consistent formatting |
| Frontend types | tsc | Type correctness |
| Frontend tests | Vitest | Behavior |
| Frontend build | Vite | The app actually builds |
| Stack integration | Docker Compose | The system boots and communicates |
| Static analysis | CodeQL | Security defects in code |
| Secret scanning | gitleaks | Credentials never enter history |
| Dependency audit | pip-audit, npm audit | Known vulnerabilities in dependencies |
| Filesystem scan | Trivy | Vulnerabilities in the image surface |

Gates also run locally through pre-commit hooks, so failures are usually caught before a push.
Rationale and the decision to adopt these gates are in
[ADR 0007](adr/0007-quality-gates-and-security-scanning.md).

---

## 4. Verifying the risk mathematics

The risk engine is the graded algorithmic component. Verification combines the following
approaches; planned acceptance evidence is distinguished from executed automated tests:

1. **Mathematical properties.** A series correlated with itself is exactly 1.0; a correlation
   matrix is symmetric with a unit diagonal; portfolio volatility computed from the covariance
   matrix never exceeds the weighted average of individual volatilities unless every pair is
   perfectly correlated.
2. **Independent implementations.** Results are compared against NumPy's own routines and
   against values computed by hand, not against previously recorded output of the same code.
3. **Financial plausibility (planned acceptance evidence).** Compare results with independently
   calculated values for the same dates and adjusted-price inputs. Relative real-market
   volatility depends on the selected assets and window; a fixed bond/equity ordering is
   not a universal correctness assertion. The September 8 automated run used synthetic
   prices and does not establish live-market plausibility or manual acceptance.

Methodological conventions being tested against are fixed in
[ADR 0012](adr/0012-risk-methodology.md).

---

## 5. Change log

| Date | Change |
|---|---|
| 2026-09-02 | Initial testing report created as a living document. |
| 2026-09-07 | Updated test count after the current backend and frontend suites passed: 183 backend and 53 frontend tests. |
| 2026-09-08 | Reran both suites at c065aef; added Week 3 specification traceability and explicit environment, CI-probe, architecture-review, and UAT limitations. Corrected unsupported live-market ordering claim. |

## Week 4 regression evidence

On September 15, 2026, at 20:49 PDT, the unchanged application revision `83716a2`
passed 183 backend tests and 53 frontend tests (236 total; zero failures or skips).
Backend: Python 3.13.7, SQLite, FakeProvider; frontend: Vitest 2.1.9 with mocked APIs.
The backend emitted a Starlette/httpx TestClient deprecation warning. No coverage
percentage, live-provider acceptance, or browser UAT was measured.

Commands: `cd backend && .venv/bin/pytest -q --junitxml=<evidence-dir>/backend-results.xml`;
from frontend, Node invoked `node_modules/vitest/vitest.mjs run --reporter=default
--reporter=junit --outputFile=<evidence-dir>/frontend-results.xml`.

[Thirty unit/system specifications](sprint1-unit-system-tests.md) and
[four wireframe plates](design/sprint1-wireframes.md) now map the six Sprint 1
stories and seven requirement IDs. Twenty-five specifications are supported by
this local run; one uses prior passing CI evidence and four remain unexecuted.
The original six Week 3 acceptance procedures remain pending. No story was
reassigned or newly accepted by creating these documents.

## US-9 early implementation — September 18, 2026

The stress-test change adds 27 backend cases and 9 frontend cases (8 screen cases plus
application navigation), bringing the local suites to **210 backend + 62 frontend = 272**.
Backend Ruff lint/format and strict mypy passed; frontend lint, formatting, type checks,
Vitest and production build passed. Existing warnings: Starlette/httpx deprecation and
one non-blocking Fast Refresh warning in button.tsx. The stress tests emit no new warnings.

Local environment: Python 3.13 with SQLite/FakeProvider; Node 24.19.0. CI independently
checks the configured Python 3.12 and Node 20 containers. Traceability, expected results,
controlled browser evidence and remaining acceptance procedures are in
[US-9 test specifications](us9-stress-tests.md). No live-provider or instructor acceptance,
production deployment, coverage percentage or Sprint 1 throughput is claimed.


### Stress-test visualization follow-up

Initial user feedback added a waterfall value comparison and up to five ranked loss bars.
Five new chart tests bring the frontend suite to **67 passing** (277 combined with the
unchanged 210 backend cases). Lint, formatting, type check and build passed. Controlled
browser checks were repeated, including desktop dark and mobile light visual inspection.
See ST-10 in [the stress specifications](us9-stress-tests.md). No new financial calculation
or dependency was introduced; the existing SVG-chart decision (ADR 0013) applies.

## US-11 filing ingestion — early implementation September 19, 2026

[US-11 specifications and evidence](us11-filing-tests.md) map FR-13 to parser, API,
network-boundary, restart, native PostgreSQL and screen tests. The PostgreSQL-specific
suite runs separately in CI against its disposable Compose database; regular pytest skips
those PostgreSQL cases. No real SEC downloads occur in automated tests. Live SEC integration passed against a separate PostgreSQL database and the actual worker;
manual acceptance steps remain in FI-08. Keyword retrieval is not evidence of grounded
generation under FR-14.

## US-21 automatic filing following — September 19, 2026

[AF-01–AF-06 specifications and evidence](us21-following-tests.md) link FR-16 / US-21 to
holdings backfill, ticker-only watchlists, membership isolation/removal, due intervals,
scheduling concurrency and user acceptance. The local suites now pass **244 backend + 82
frontend tests**, plus **four native PostgreSQL tests** run separately. Ruff, mypy, ESLint,
Prettier, TypeScript and production build pass; existing warnings are unchanged. Desktop
and 390px mobile controlled browser checks passed with synthetic data. User acceptance
remains pending; the story has no new sprint assignment or estimate.
