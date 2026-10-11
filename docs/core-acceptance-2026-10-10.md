# Core acceptance execution — October 10, 2026

## Scope and release boundary

Executed by Codex at Andrew's request, on October 10 PDT (October 11 UTC).
This records agent-operated browser acceptance, not Andrew's personal sign-off.
Scope and estimates remain unchanged: the seven Sprint 2 stories total 23 points.

- Baseline: `main` at `236d64e`, with a browser smoke check of sign-in, dashboard,
  reload persistence and sign-out. This was **not** the full acceptance suite on main.
- Full run: UI branch `cac2730`, followed by corrective commits beginning with `daf0b3b` on
  `codex/core-acceptance`. The PR is stacked on `codex/ui-chart-refresh` (#94).
- Application: real React, FastAPI routes/authentication, migrated PostgreSQL 16,
  real cache and risk engine. Prices and symbol recognition use the isolated test
  provider except for the explicitly identified live Tiingo check.
- Separate Compose project `orbit-acceptance`, disposable database, synthetic
  accounts and holdings. Browser origin `http://127.0.0.1:5187`, API port 8087.
  Andrew's existing localhost portfolio was not modified.
- SEC and model workers are not running in this fixture stack. No live Q&A quality,
  homelab deployment, or user acceptance of SEC ingestion is implied.

Specifications: [Sprint 2 UAT](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/codex/sprint2-planning/docs/sprint2-tests.md),
[unit/system specifications](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/codex/sprint2-planning/docs/sprint2-unit-system-tests.md),
[Sprint 1 carryover](sprint1-tests.md). Historical weekly snapshots retain their original dates.

## Results and traceability

All 14 Sprint 2 UAT procedures passed after corrective work, with the overlap-fixture
variation disclosed below. Five carryover procedures and W7-19-05 also passed in
this isolated environment. These are procedure counts, separate from automated test counts.
Evidence paths below are relative to [the evidence directory](evidence/acceptance-2026-10-10/).

| Requirement / story | Case | Actual result | Evidence |
|---|---|---|---|
| FR-15 / US-13 #13 | W6-UAT-13-01 | Valid login showed owned holdings; reload preserved session; logout hid protected content and revoked session (401 on replay). | `correlated-overview.png`, `auth-health.json` |
| FR-15 / US-13 #13 | W6-UAT-13-02 | Wrong password and unknown account both showed “Incorrect email or password.” API responses matched, created no cookie, and anonymous holdings returned 401. | `invalid-login.png`, `auth-health.json` |
| FR-2, FR-3 / US-2 #2 | W6-UAT-2-01 | Browser uploaded simple.csv into empty account B. AAPL 10 and MSFT 5.5 imported, two added/no errors, persisted after reload. | `csv-valid.png`, repository `backend/tests/fixtures/simple.csv` |
| FR-2, FR-3 / US-2 #2 | W6-UAT-2-02 | Empty account C imported only AAPL 10. Line 3 rejected abc; line 4 rejected -5. No invalid holding appeared. | `csv-partial.png` |
| FR-8 / US-6 #6 | W6-UAT-6-01 | 25 prices, 24 alternating ±1% returns, MSFT twice AAPL prices: labeled symmetric matrix, diagonals/pair +1.00. | `correlated-api.json`, `correlated-overview.png` |
| FR-8 / US-6 #6 | W6-UAT-6-02 | Constant MSFT price: cross-correlation and MSFT diagonal null; screen showed em dashes, no fabricated measured zero. | `constant-api.json`, `constant-correlation.png` |
| FR-9 / US-7 #7 | W6-UAT-7-01 | Weights 55/25/10/10: HHI .385 → API .39, effective count 2.60, only BIG overweight at 2.2×. Misleading explanation fixed and retested. | `concentration-api.json`, `concentration-fixed.png` |
| FR-9 / US-7 #7 | W6-UAT-7-02 | VOO/VTI/QQQ grouped at 80%; BND excluded. Copy described price co-movement; methodology explicitly excludes constituent look-through. | `overlap-api.json`, `overlap.png`, `overlap.txt` |
| FR-10 / US-8 #8 | W6-UAT-8-01 | Recovered series: worst -40%, currently at peak; peak Oct 8, trough Oct 9, recovery Oct 10; each interval one calendar day. | `recovered-api.json`, `recovered.png` |
| FR-10 / US-8 #8 | W6-UAT-8-02 | Ongoing series: worst/current -25%; Oct 9 peak, Oct 10 trough; “not recovered,” no invented recovery date. | `ongoing-api.json`, `ongoing.png` |
| FR-12 / US-10 #10 | W6-UAT-10-01 | Four-holding dashboard $10,000; volatility 9.3% (API 9.32), average correlation .48, weights 30/25/25/20. Keyboard Home changed chart date; Tab/Enter selected QQQ. Desktop and narrow layout inspected; no document overflow (375px content/client width under requested 390px viewport). Holdings table scrolls within its container. | `restored-api.json`, `restored-dashboard.png`, `mobile-dashboard.png` |
| FR-12 / US-10 #10 | W6-UAT-10-02 | Empty account showed add/import guidance. Controlled 503 showed error without metrics; false “0 positions” fixed and alert semantics added. Restoring provider/reloading returned correct values; holdings identical before/after. | `error-state.png`, `partial-analysis.png`, `overlap-api.json`, `restored-api.json` |
| FR-12 support / US-19 #62 | W6-UAT-19-01 | Reviewed return, volatility, correlation, concentration and drawdown definitions against ADR 0012. Fixed unconditional “far fewer” claim at 3.92/4. Historical/fixed-holding/look-through limits and no-advice explanation present. | `methodology.txt`, corrective tests |
| FR-12 support / US-19 #62 | W6-UAT-19-02; W7-19-05 | Followed all four dashboard metric explanation links and all nine contents links to correct anchors. Examples matched API (3.92 effective holdings, VOO/VTI 1.00, ongoing decline -25%). Empty account showed formulas without another account's examples. | `metric-links.json`, `methodology-links.json`, `methodology.txt`, `empty-methodology.txt`, relevant API captures |
| AR-1 / US-14 #14 | TC-14-01 | All three disposable containers built/started, migrations applied, API database health connected. Authenticated real browser rendered persisted API holdings. Ports deliberately differ from normal stack. | `auth-health.json`, Compose harness and screenshots |
| FR-1 / US-1 #1 | TC-1-03 | Empty account D: entered AAPL 10 in UI, reloaded successfully; ZZZZ rejected, count unchanged. Symbol validation used controlled provider. | `manual-invalid.png` |
| FR-4 / US-3 #3 | TC-3-03 | Added MSFT 4, changed AAPL 10→12.5; value became $1,250 at $100. Cancel retained MSFT; confirmation removed it after reload and from fresh risk response. | `manual-edited-deleted.png`, `managed-api.json` |
| FR-5, FR-6 / US-4 #4 | TC-4-03 | Real Tiingo AAPL request returned 250 daily records, source provider; repeat source cache. Analysis and subsequent browser dashboard succeeded; repeat after browser made zero provider calls. | `live-first.json`, `live-after-browser.json` |
| FR-7 / US-5 #5 | TC-5-03 | AAPL 10/NVDA 5, 365-day requested window/24 fixture returns: both holdings and portfolio 11.5% on screen, 11.47 in API. | `volatility-api.json`, `volatility.png` |

### Fixture variations and evidence limits

- Inputs are generated by [acceptance_app.py](../backend/tests/acceptance_app.py).
  Fixture dates are consecutive calendar dates, ending on the previous UTC day;
  these are synthetic observations, not an actual trading calendar.
- Overlap UAT originally supplies correlations 1.00/.93/.92 directly to a unit
  fixture. Exact perfect correlation of one pair requires equal correlations with
  a third series. For the full-stack run, valid generated returns therefore use
  1.00/.93/.93, with BND correlations zero. The expected group and 80% weight are
  unchanged; the original matrix remains covered by existing unit tests.
- HHI is independently .55²+.25²+.10²+.10²=.385; the API intentionally rounds it
  to two decimal places. Effective holdings are computed before that rounding.
- Independently computed sample annualized volatility for ±1% returns is
  `100 × sqrt(252) × sqrt(24 × .01² / 23) = 16.2159%`, matching API 16.22/UI 16.2.
- The live market check used the real Tiingo adapter and HTTP route through
  FastAPI TestClient, PostgreSQL, and a counting provider wrapper. Browser then
  read those same cached prices through the fixture app. This is a disclosed
  semi-automated integration check, not a deployed-provider soak test.
  Persisted evidence contains counts/dates/source/call counts only, no token or
  licensed raw price bars. Cached live data remains only in the disposable DB.
- No manual screen-reader audit, broad browser compatibility study, new coverage
  percentage, instructor review, or Andrew sign-off is claimed.

## Defects and regression proof

1. **US-7:** “spread fairly evenly” contradicted a flagged 55% overweight position.
   Removed the arbitrary half-count presentation threshold; explanation now states
   the weight-based effective count and that correlation is excluded.
2. **US-19:** “far fewer positions” appeared unconditionally, including 3.92/4.
   Replaced it with the definition of equivalent equally weighted holdings.
3. **US-10:** Failed loads fabricated “0 positions” and lacked an alert role.
   Unknown count stays omitted; load failure is announced as an alert.

4. **US-19:** Dashboard volatility had no direct explanation link. Metric labels
   now link directly to volatility, correlation and drawdown methodology sections;
   concentration retains its existing explanation link. All four were followed in
   the running browser and personalized figures checked against `final-api.json`.
5. **US-10:** A partial analytics failure left priced holdings visible but called
   an unavailable drawdown “recovered to peak.” It now explicitly says “Drawdown
   unavailable.” Controlled browser retest retained the holding/value and displayed
   unavailable risk figures, without the false recovery claim.

Commit `daf0b3b` contains the first three fixes and regression assertions. With original production
files restored temporarily, the three targeted tests failed (34 other tests passed).
Restoring fixes yielded **37/37 passing** targeted tests. The final two gaps were also
proved by **two failing tests / 28 passing** before correction and included in the
final passing frontend suite. No risk formulas, API
contracts, dependencies, story estimates or sprint assignments changed; ADR 0012
and ADR 0013 still apply, so no new architectural decision is needed.

## Automated checks and security

- Backend container: Ruff lint/format, strict mypy: passed. **316 passed, seven
  skipped** in normal pytest; the seven PostgreSQL cases **passed separately**
  against the disposable database (`APP_TEST_POSTGRES=1`).
- Frontend container: ESLint, Prettier, TypeScript (build), Vite production build:
  passed. **101 tests passed across 13 files** after fixes.
- `pip-audit`: no known vulnerabilities in audited dependencies; local Orbit
  package is not on PyPI and was not audited as a published distribution.
- Required `npm audit --omit=dev --audit-level=high`: **zero vulnerabilities**.
- Broader development-tool audit: **15 existing advisories** (five moderate,
  eight high, two critical). Includes Vite/Vitest/Tailwind transitive packages;
  wholesale major-version upgrades are not bundled into this acceptance fix.
  They remain release/tooling follow-up, not silently treated as a clean full audit.
- Existing Starlette/httpx deprecation and non-blocking Fast Refresh warning remain.
- CI/security status must be read from the acceptance PR at its current head.
  Local checks do not stand in for required GitHub checks.

## Board and completion status

US-2, US-6, US-7, US-8, US-10, US-13 and US-19 are **In Progress**, awaiting
review/integration and final acceptance gates; all retain Sprint 2 and existing
point estimates. Board changes were made through Andrew's signed-in Chrome session
and verified after reload. No issue was closed or newly marked Done.
Previously Done Sprint 1 cards remain there; this record supplies missing acceptance
evidence without rewriting their earlier completion history.

Remaining project gates include the stacked PR review/merge chain, Andrew's final
product review, ST-09 live stress/user acceptance, FI-08 manual SEC-source comparison
and interrupted live-worker recovery, the real-provider grounded-Q&A evaluation,
and homelab deployment/operational verification. This core sweep does not claim those
separate procedures passed. The Q&A evaluation must respect existing budgets and
cannot be replaced with fake-provider tests.

## Reproduce the isolated browser environment

From the acceptance branch/worktree:

```sh
mkdir -p .acceptance
printf '%s\n' '{"profile":"correlated"}' > .acceptance/current.json
docker compose -f docker-compose.acceptance.yml up -d --build
```

Open `http://127.0.0.1:5187`, create disposable accounts and enter/import only test
holdings. Keep credentials in ignored local files. Available price profiles:
`correlated`, `constant`, `concentration`, `overlap`, `recovered`, `ongoing`, `error`,
`analytics_error` (summary succeeds; analytic endpoints fail).
For a profile change, update `.acceptance/current.json`, then clear **only this
fixture database's** price cache before reloading:

```sh
docker compose -f docker-compose.acceptance.yml exec -T db \
  psql -U orbit -d orbit_acceptance -c 'TRUNCATE price_bars, price_coverage;'
```

Use 55/25/10/10 shares for BIG/MID/A/B in concentration; 30/25/25/20 for
VOO/VTI/QQQ/BND in overlap (all end at $100). Other scenarios are proportional
across holdings. Partial CSV: `Symbol,Quantity` with AAPL/10, MSFT/abc, TSLA/-5.
No secret or live service is needed for deterministic browser checks. The test
entry point refuses databases not named `orbit_acceptance`; production startup
continues to use `app.main:app`. The database is ephemeral and disappears when the
acceptance DB container is removed. Cleanup only this Compose project:

```sh
docker compose -f docker-compose.acceptance.yml down
```
