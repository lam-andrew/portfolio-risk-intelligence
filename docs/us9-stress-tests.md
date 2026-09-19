# US-9 stress-test specifications and evidence

Created September 18, 2026. Requirement **FR-11** → **US-9**, [issue #9](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/9).
Acceptance criterion: given an analyzed portfolio, selecting a stress scenario estimates
and displays its impact. Owner: Andrew Lam. Sprint 3, 8 points, unchanged; implementation
is early work with its actual date, not Sprint 1 velocity. Methodology: [ADR 0018](adr/0018-hypothetical-portfolio-stress-tests.md).

## Automated specifications

All cases below trace to FR-11 / US-9. API checks use the real authentication, routes,
SQLite persistence and cache service with FakeProvider. They do not call a live provider.
Frontend checks use mocked HTTP-client methods. Each fixture starts with isolated data;
no user portfolio is touched. An estimate is read-only; price cache population is allowed.

### ST-01 — Independent scenario arithmetic (engine unit)

- Preconditions: values AAPL $1,000, MSFT $500; Decimal inputs; no I/O.
- Input/steps: apply a −0.20 price shock.
- Expected: losses $200 and $100; portfolio baseline $1,500, loss $300 (20%), after $1,200.
- Postconditions: inputs unchanged; rows reconcile with totals.
- Automation: `backend/tests/test_stress.py::test_hand_computed_loss_and_contributions`.

### ST-02 — Precision and bounds (engine unit)

- Preconditions: two positions worth $10.05 each for rounding; $1,500 for shock boundaries.
- Steps: apply −10%; separately apply zero and −100% shocks. Try empty values, zero/negative/
  nonfinite values, a portfolio rounding below one cent, positive or below −100% shocks.
- Expected: half-up losses $1.01 each, total $2.02, after $18.08. Boundary losses $0/$1,500.
  Invalid inputs raise ValueError; never return NaN, negative post-shock values or zero baselines.
- Automation: `test_rounding_reconciles_with_visible_rows`, `test_boundary_shocks`,
  `test_invalid_shocks`, `test_invalid_or_subcent_portfolio`, `test_empty_engine_input`.

### ST-03 — Catalogue, selection and empty state (API integration)

- Preconditions: authenticated account, initially no holdings.
- Steps: request catalogue; request unknown ID; request default scenario on empty account.
- Expected: unique IDs with −10/−20/−35 percentages, invalid ID 422, empty status with null
  amounts and no rows. Catalogue/validation do not fetch prices.
- Automation: `test_catalog_and_validation`, `test_empty_portfolio_is_not_a_zero_loss`.

### ST-04 — Complete same-date valuation and no mutation (API integration)

- Preconditions: AAPL 1.5 shares and MSFT 2. Both priced yesterday at $100/$50; only AAPL
  also has today's $999 price. One shared price suffices; no 20-observation threshold.
- Steps: snapshot holdings; request decline-20; retrieve holdings again.
- Expected: yesterday's date, $250 baseline, $50 loss, $200 after, contributions $30/$20;
  holdings unchanged. Never mix today's AAPL price with yesterday's MSFT price.
- Automation: `test_latest_common_date_and_fractional_shares`.

### ST-05 — Pricing gaps and cache reuse (API integration)

- Preconditions: AAPL/MSFT holdings; AAPL has usable data. Vary MSFT data: provider error,
  empty series, zero/negative prices, a disjoint date, or only an out-of-window price.
- Steps: request stress result for each case; separately change a complete portfolio's
  scenario from 10% to 35% within the cache window.
- Expected: incomplete cases return unavailable with null totals/no rows, missing ticker
  when appropriate. Complete scenario changes reuse cached data, same baseline, greater
  loss under 35%; one provider fetch for a single holding.
- Automation: `test_incomplete_prices_never_produce_partial_totals`,
  `test_changing_scenarios_reuses_cached_prices`.

### ST-06 — Account protection (API integration)

- Preconditions: anonymous client; separately first account with AAPL and second empty account.
- Steps: call both endpoints anonymously; sign out first user and register second; request stress.
- Expected: both anonymous calls 401; second account sees empty/no positions, never first user's data.
- Automation: `test_anonymous_rejected`, `test_accounts_are_isolated`.

### ST-07 — Screen, selection and asynchronous responses (frontend unit)

- Preconditions: mocked catalogue and known $1,500/20% result with two holding rows.
- Steps: enter through navigation; choose 20%; run; inspect totals, date, rows and methodology link.
  Change selection; resolve an older request after the newer result. Exercise empty holdings,
  missing prices, request failure/retry, catalogue failure/retry and an empty catalogue.
- Expected: selected ID sent, $300/20% loss and dated contributions displayed; no automatic
  calculation on selection. Old results clear, late responses cannot overwrite new results;
  pending Run button disabled. Error/empty states never invent totals; retry works.
- Automation: `frontend/src/pages/StressTestPage.test.tsx` (8 cases), navigation case in
  `frontend/src/App.test.tsx`. Updated methodology test checks the formula and section.

## Execution snapshot

September 18 local regression: **210 backend, 62 frontend passing**. Checks: backend Ruff
lint/format and mypy; frontend ESLint, Prettier, tsc, Vitest and production build. Existing
Starlette/httpx and Fast Refresh warnings are unchanged. No coverage percentage measured.

## Controlled browser check (ST-08)

Preconditions: isolated SQLite database, synthetic account, fixed provider (AAPL $100,
MSFT $50), real backend HTTP API and React development server. This is an integration
check with synthetic market data, not live-provider UAT or production deployment.

Procedure: open empty Stress test; seed AAPL 10/MSFT 10; run all three scenarios. Expect
baseline $1,500 and losses $150/$300/$525, after values $1,350/$1,200/$975. Follow the
methodology link; inspect desktop dark and 390px mobile light layouts. Check for page
errors and document-wide horizontal overflow. Postcondition: only disposable QA data exists.

Result: **passed September 18 PDT**, application revision `2776e38`. Chrome exercised the
real HTTP routes using the isolated SQLite/fixed-provider harness. All three exact losses,
empty state and methodology navigation passed. Desktop dark and mobile light screenshots
were visually inspected; no page errors or document-wide horizontal overflow at 390px.
Changing AAPL from 10 to 20 shares through Holdings, waiting for the refreshed table, and
rerunning 20% produced the expected $500 loss on a $2,500 baseline. Keyboard Tab from the
selector reached Run, and Enter executed it. QA artifacts are local, outside the repository;
this synthetic integration result does not replace ST-09.

## Remaining acceptance (ST-09)

Andrew's review uses the normal PostgreSQL Compose stack and configured market provider.
Sign in, choose an analyzed portfolio, record the shared pricing date/values, run each
scenario and independently calculate expected losses. Edit a quantity through Holdings,
return and rerun; verify changed contributions, preserved holdings, keyboard navigation and
clear behavior when market data is unavailable. Record revision, time, actual versus expected,
sanitized evidence and any defect. Do not mark the story Done solely on automated evidence.

Status: pending user acceptance and normal-stack/live-provider confirmation. No issue closure
or board movement is implied. The CLI token lacks `read:project`; issue scope is verified,
but current Project board status was not refreshed or changed.


## Visual feedback iteration — ST-10

September 18: added a waterfall comparison and ranked holding-loss bars after initial user
feedback. These are presentation-only views of API results, covered by ADR 0013; no scenario
math, API, dependencies or sprint assignment changed.

Preconditions: the ST-01 $1,500 baseline / $300 loss / $1,200 remainder response. Render the
charts and inspect heights, labels and ranking. Expected: zero-based baseline, a 20% loss
step and 80% remaining bar; AAPL's $200 contribution is twice MSFT's $100. Ranking must not
mutate input order. With more than five holdings, show the largest five with an explicit
limit label. Zero-cent losses produce zero-width/height marks without NaN; unavailable data
produces no plot. Every plotted dollar value remains available as text, and the chart states
that it is not a time series.

Automation: `frontend/src/features/risk/StressImpactChart.test.tsx` (5 cases), plus the
existing screen test now asserts graph presence. **67 frontend tests passed**, along with
lint, formatting, type checks and production build. Backend code is unchanged (210 tests
in the preceding run). The isolated browser flow was repeated with the charts: all three
scenarios, empty state, quantity edit, keyboard Run and methodology link passed. Desktop dark
and 390px mobile light screenshots were inspected; no page errors or page-wide overflow.
ST-09 live-provider/user acceptance remains pending.
