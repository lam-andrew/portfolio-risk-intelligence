# Sprint 1 Acceptance Test Specifications

Living test documentation, not a course submission. Evidence snapshot: September 8, 2026, at c065aef. These 18 specifications map all Sprint 1 requirements to acceptance criteria, procedures, expected results, and source tests. They do not represent 18 newly implemented automated tests.

The September 8 regression run passed 183 backend and 53 frontend tests. Backend execution used Python 3.13, SQLite, and FakeProvider; frontend tests use mocked APIs. Six manual/developer acceptance procedures remain specified but not executed. Record date, revision, tester, actual outcomes, sanitized evidence, and defect links for each future execution. See [testing strategy](testing.md) and [Sprint 1 DoD](sprint1-plan.md).

## US-14 | Containerized deployment

**AR-1 | Must | 5 points | Owner: Andrew Lam**
[Authoritative issue #14](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/14)

### Acceptance criteria

AC14.1: Given the repository, running Compose starts frontend, backend, and database and allows them to communicate locally. AC14.2: Given a push to main, CI builds and tests the container images before deployment. The deployment stage itself remains deferred, not claimed complete.

### Story-specific DoD tasks and current evidence

- Container/service design, Dockerfiles, Compose wiring, database configuration, and health probes: present; CI confirms startup and backend/database connectivity.
- CI builds, code quality, tests, and security gates: present and green for the reviewed PR. There is no new UI sketch task for this infrastructure story.
- Setup documentation and ADRs 0003/0007/0008: present. Current probe is /api/health; hosted deployment is not implemented by this story's evidence.
- Browser/frontend-to-API communication and reproducible local developer acceptance: pending TC-14-01. Complete this and retain evidence before final DoD sign-off.

### TC-14-01 | Full-stack developer acceptance

**Maps to AR-1 / AC14.1. Type: manual system/developer acceptance. Status: specified, not executed.**

Setup: fresh test checkout at the recorded revision, Docker/Compose, isolated test volumes, and configured nonproduction environment. No market API key is required for the basic health check. Actions: build/start the stack; inspect the running services; open the frontend on port 5173; request /api/health on port 8000; use a disposable signed-in account to open holdings and inspect its network response. Expected: all three services run; the frontend loads; health reports database connected; the browser receives a successful JSON holdings response from /api/holdings. Retain sanitized service state, health response, and browser/network evidence. Do not remove existing user volumes.

### TC-14-02 | Container CI gate

**Maps to AR-1 / AC14.2. Type: automated build/system smoke. Status: passed in cited CI run.**

Setup: GitHub Actions checkout and Docker runner, no live market dependency. Actions: build backend/frontend images; run their configured lint, format, type, test, and frontend build jobs; start Compose and poll /api/health. Expected: jobs succeed and database reports connected before timeout. Evidence: [ci.yml](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/c065aef/.github/workflows/ci.yml), [run 34183424793](https://github.com/lam-andrew/portfolio-risk-intelligence/actions/runs/34183424793). Limitation: no image promotion or actual production deployment is proved.

### TC-14-03 | Health failure visibility

**Maps to AR-1 / supports AC14.1. Type: automated API contract. Status: passed September 8.**

Setup: TestClient, stub database connectivity as unavailable. Action: GET /api/health. Expected: HTTP 200 with database="unavailable", allowing a diagnostic response rather than a crash. Evidence: [test_health.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/c065aef/backend/tests/test_health.py), `test_health_reports_db_unavailable_without_failing`. This is a stubbed contract test, not a real database-outage exercise.

**Traceability:** implementation/initial tests c2125f6 (PR #19); CI gates 4b54392; current probe/test-path update 24d39ef (PR #79). Specification IDs created/reviewed September 8.


## US-15 | Decoupled analysis API

**AR-2 | Must | 3 points | Owner: Andrew Lam**
[Authoritative issue #15](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/15)

### Acceptance criteria

AC15.1: Frontend analysis requests call the engine through the API contract, not internal code. AC15.2: A new engine can integrate behind the same API layer without modifying the existing risk engine.

### Story-specific DoD tasks and current evidence

- Establish separate API orchestration and pure risk modules: present; imports reviewed September 8 show standard-library/NumPy dependencies, not provider, database, frontend, or API dependencies.
- Route frontend analysis through the shared HTTP client and /api namespace: present. API-path and risk-response tests pass.
- Document boundaries and contracts: ADRs 0004/0017 and generated OpenAPI provide the design record; no dedicated UI or new database schema is needed for this story.
- Verify an added engine can attach without modifying risk code: planned developer acceptance TC-15-03, not claimed demonstrated. Retain its diff and regression result before full sign-off.

### TC-15-01 | API namespace contract

**Maps to AR-2 / supports AC15.1. Type: automated API contract. Status: passed September 8.**

Setup: unauthenticated TestClient; health needs no user data. Actions: request /api/health, /health, and /holdings. Expected: the namespaced health route returns 200; root /health and /holdings return 404 on the backend, keeping the frontend namespace separate. Evidence: [test_health.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/c065aef/backend/tests/test_health.py), `test_the_api_is_namespaced_under_api`. This verifies paths, not by itself the absence of direct engine imports.

### TC-15-02 | Dependency-boundary inspection

**Maps to AR-2 / AC15.1. Type: static architecture review. Status: reviewed September 8; boundary supported.**

Setup: source revision c065aef. Actions: inspect frontend/src/api/client.ts analysis requests and imports in backend/app/engines/risk; trace API orchestration to the pure volatility function. Expected: browser analysis uses HTTP /api/portfolio/risk; engine modules contain no HTTP, database, provider, or frontend imports. Evidence: [client](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/c065aef/frontend/src/api/client.ts), [risk engine](https://github.com/lam-andrew/portfolio-risk-intelligence/tree/c065aef/backend/app/engines/risk), [ADR 0004](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/c065aef/docs/adr/0004-decoupled-engines-api-contract.md). This was source inspection, not a newly installed automated architecture rule.

### TC-15-03 | Add an isolated test engine

**Maps to AR-2 / AC15.2. Type: manual developer acceptance with regression execution. Status: specified, not executed.**

Setup: disposable branch/worktree with baseline tests passing. Actions: add a trivial demonstration engine returning {status: "ok"}; register a test-only route under the existing API router; request the route; inspect the diff and rerun risk regression tests. Expected: the new route returns its expected JSON; no existing risk-engine file changes; risk tests remain passing. Retain the isolated diff and outputs; do not merge this demonstration into application scope. This tests extensibility without prematurely implementing RAG.

**Traceability:** skeleton c2125f6 (PR #19), API contract ADR 0004, namespace and contract regression 24d39ef (PR #79). Specification IDs created/reviewed September 8.


## US-1 | Add a holding manually

**FR-1 | Must | 2 points | Owner: Andrew Lam**
[Authoritative issue #1](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/1)

### Acceptance criteria

AC1.1: On the portfolio page, submitting a valid ticker and quantity adds and displays the holding. AC1.2: Submitting an unrecognized ticker shows a clear error and adds nothing.

### Story-specific DoD tasks and current evidence

- Design and implement the ticker/quantity form, validation feedback, holding model, persistence, and API: present in implementation and UI source.
- Validate positive/fractional quantities, normalize tickers, reject unknown/duplicate input: existing API tests pass.
- Verify successful and rejected form submissions: both AddHoldingForm component tests pass with mocked API responses.
- Link the issue, implementation PRs, and setup documentation: recorded below. Full-stack browser display and reload persistence remain pending TC-1-03; mocked form tests are not final UAT.

### TC-1-01 | Valid holding persistence

**Maps to FR-1 / supports AC1.1. Type: automated API integration. Status: passed September 8.**

Setup: fresh SQLite test database, authenticated fixture, FakeProvider recognizing AAPL. Actions: POST /api/holdings with ticker AAPL and quantity "10"; then GET /api/holdings. Expected: creation returns 201, an identifier, ticker AAPL, and quantity 10; listing returns the new holding. Evidence: [test_holdings.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/c065aef/backend/tests/test_holdings.py), `test_add_valid_holding_then_appears_in_list`. UI counterpart: [AddHoldingForm.test.tsx](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/c065aef/frontend/src/features/holdings/AddHoldingForm.test.tsx), "submits the ticker and quantity and reports the new holding".

### TC-1-02 | Unrecognized ticker rejection

**Maps to FR-1 / AC1.2. Type: automated API integration plus UI component. Status: passed September 8.**

Setup: same fixtures, with ZZZZ unrecognized by FakeProvider. Actions: POST ticker ZZZZ and quantity "5"; list holdings. Expected: 422 with an Unrecognized error, and the portfolio remains empty. Evidence: test_holdings.py, `test_unrecognized_ticker_is_rejected_and_adds_nothing`. UI counterpart: AddHoldingForm.test.tsx, "shows a clear error and adds nothing when the backend rejects the ticker". These are two complementary assertions across separate test environments, not an end-to-end browser run.

### TC-1-03 | Browser entry and rejected input

**Maps to FR-1 / AC1.1 and AC1.2. Type: manual UAT. Status: specified, not executed.**

Setup: isolated running stack, disposable signed-in user, provider configured and reachable, empty portfolio. Actions: enter AAPL and 10 on Holdings; submit and reload; then submit a ticker confirmed unrecognized by the configured provider. Expected: AAPL appears once with 10 shares and survives reload; the invalid submission shows a clear error and does not increase the holdings count. Retain before/after screenshots and sanitized requests; a provider outage is a blocked environment, not proof of unknown-ticker handling.

**Traceability:** backend implementation and tests e7546a2 (PR #50); frontend and form tests 3c550e8 (PR #52); API paths updated in 24d39ef (PR #79). Specification IDs created/reviewed September 8.


## US-3 | Manage holdings

**FR-4 | Must | 2 points | Owner: Andrew Lam**
[Authoritative issue #3](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/3)

### Acceptance criteria

AC3.1: Editing an existing holding's quantity saves the change and reflects it in analysis. AC3.2: Confirming deletion removes the holding and excludes it from further analysis.

### Story-specific DoD tasks and current evidence

- Provide view, inline edit/save/cancel, and delete-confirmation interaction: present in holding components; interaction tests pass.
- Persist changes through PATCH/DELETE and validate quantities/missing identifiers: implemented and covered by passing API tests.
- Document the interaction in the living user guide; retain implementation/test links: management instructions are refined in the September 8 documentation update, with links below.
- Demonstrate changed quantities affect analysis inputs and deleted holdings disappear from fresh analysis: pending TC-3-03. Existing API CRUD tests inspect the holdings list, not the full subsequent risk response. Do not overstate their coverage.

### TC-3-01 | Save an edited quantity

**Maps to FR-4 / supports AC3.1. Type: automated API integration. Status: passed September 8.**

Setup: authenticated fixture with AAPL quantity 10. Actions: PATCH /api/holdings/{id} with quantity "12.5"; GET /api/holdings. Expected: HTTP 200 and quantity 12.5 in both update response and persisted listing. Evidence: [test_holdings.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/c065aef/backend/tests/test_holdings.py), `test_edit_quantity_is_saved`. Companion rejection test preserves the original quantity when submitted values are zero or negative. Limitation: saved analysis inputs are checked, not a recalculated portfolio metric.

### TC-3-02 | Confirmed deletion

**Maps to FR-4 / supports AC3.2. Type: automated API integration plus UI component. Status: passed September 8.**

Setup: AAPL quantity 10 and MSFT quantity 4 in test fixtures. Action: DELETE the MSFT identifier, then list holdings. Expected: 204; only AAPL remains. Evidence: test_holdings.py, `test_delete_removes_holding_from_further_analysis` (despite its name, the assertions inspect the remaining holdings list). UI evidence: [HoldingRow.test.tsx](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/c065aef/frontend/src/features/holdings/HoldingRow.test.tsx), "requires confirmation before deleting" and "can cancel a delete".

### TC-3-03 | Edit, delete, and reanalyze

**Maps to FR-4 / AC3.1 and AC3.2. Type: manual UAT/system. Status: specified, not executed.**

Setup: disposable account with AAPL 10 and MSFT 4, cached prices for a fixed lookback. Actions: record baseline holdings and analysis; change AAPL to 12.5 and reload; reanalyze; request deletion of MSFT and cancel; confirm it remains; delete again and confirm; reload and reanalyze. Expected: the saved quantity and position value reflect 12.5 at the same price; analysis uses the updated portfolio inputs (not necessarily a visibly different rounded volatility); cancel preserves MSFT, while confirmation removes it from both holdings and the new risk response. Retain sanitized responses and UI evidence.

**Traceability:** implementation/API and interaction tests 09cc471 (PR #53); API paths updated 24d39ef (PR #79). [User guide](https://github.com/lam-andrew/portfolio-risk-intelligence/pull/81). Specification IDs created/reviewed September 8.


## US-4 | Retrieve and cache market data

**FR-5, FR-6 | Must | 5 points | Owner: Andrew Lam**
[Authoritative issue #4](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/4)

### Acceptance criteria

AC4.1: Requesting analysis for a valid ticker retrieves its historical prices. AC4.2: Repeating analysis with recently retrieved prices uses the cache rather than refetching.

### Story-specific DoD tasks and current evidence

- Provider interface, Tiingo adapter, server-side configuration, persistent bars/coverage, and cache policy: implemented and recorded in ADR 0011.
- Fresh, stale, wider-window, provider-failure, and concurrent-fetch behavior: covered by passing deterministic tests. Credentials and cached external data are excluded from version control.
- No separate user-input screen is required; retrieval supports analysis. API responses expose source/count for diagnosis.
- Record a real-provider retrieval followed by cache reuse in a controlled environment: pending TC-4-03. Fake-provider success does not establish live credentials, entitlement, or availability.

### TC-4-01 | Retrieve once and reuse cache

**Maps to FR-5, FR-6 / AC4.1 and AC4.2. Type: automated API integration. Status: passed September 8.**

Setup: authenticated fixture, fresh SQLite cache, FakeProvider recognizing AAPL. Actions: request /api/market-data/AAPL/prices?days=30 twice. Expected: first response has source="provider", nonempty bars with dates and adjusted close; second has source="cache", identical bars/count, and provider.price_calls remains 1. Evidence: [test_market_data.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/c065aef/backend/tests/test_market_data.py), `test_prices_are_retrieved_for_a_valid_ticker` and `test_second_request_is_served_from_cache`.

### TC-4-02 | Stale-cache refresh

**Maps to FR-6 / supports AC4.2's freshness boundary. Type: automated service integration. Status: passed September 8.**

Setup: cache service with ttl_hours=24, FakeProvider, AAPL history ending August 30, 2026, beginning ten days earlier. Actions: fetch, confirm immediate reuse, backdate bars and coverage by 48 hours, then fetch again. Expected: first source provider, immediate source cache, expired source provider; provider call count equals 2. Evidence: test_market_data.py, `test_stale_cache_triggers_a_refetch`. Additional existing tests cover stale fallback on failure and a narrow cached window failing to satisfy a wider request.

### TC-4-03 | Live-provider acceptance

**Maps to FR-5, FR-6 / AC4.1 and AC4.2. Type: manual system/UAT. Status: specified, not executed.**

Setup: disposable stack/test database with no cached AAPL prices, valid server-side Tiingo configuration, quota available, signed-in test account. Actions: add AAPL through the API without opening the portfolio UI (which can prefetch prices); request the 365-day history; confirm a provider source; open the dashboard; repeat the same history request and analysis within the cache TTL. Expected: historical prices exist, initial source is provider, repeated history source is cache, analysis succeeds, and sanitized server-side provider-call evidence shows no extra price fetch for the covered request. Do not publish API keys or raw licensed market data. Record an outage/quota failure as blocked and retry when available.

**Traceability:** configuration 84444a6 (PR #54), retrieval/cache and tests 5ae65cb (PR #55), concurrency regression 53c0189 (PR #69), API paths 24d39ef. [ADR 0011](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/c065aef/docs/adr/0011-market-data-provider.md). Specification IDs created/reviewed September 8.


## US-5 | Holding and portfolio volatility

**FR-7 | Must | 3 points | Owner: Andrew Lam**
[Authoritative issue #5](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/5)

### Acceptance criteria

AC5.1: Given portfolio price data, opening the risk dashboard shows volatility for each holding and for the portfolio.

### Story-specific DoD tasks and current evidence

- Implement pure holding volatility and covariance-based portfolio volatility with adjusted-close simple returns, sample statistics, and sqrt(252) annualization: present and tested against independent calculations.
- Integrate the risk API, holding/portfolio presentation, and insufficient-history behavior: implemented; API/unit tests pass. No new independent database schema is needed beyond holdings and cached prices.
- Record methodology and limitations in ADR 0012 and link implementation/tests: available. A new metric-to-methodology navigation requirement belongs to US-19, not a retroactive Sprint 1 scope addition.
- Verify displayed values against the same analysis response and lookback in browser UAT: pending TC-5-03. Final story sign-off follows that evidence.

### TC-5-01 | Independent mathematical oracle

**Maps to FR-7 / supports AC5.1 correctness. Type: automated unit. Status: passed September 8.**

Setup: seeded synthetic returns, no HTTP/database/provider. Actions: seed 42, generate 300 normal returns with daily sigma 0.01, calculate holding volatility; seed 17, generate two 400-return series with sigmas 0.012 and 0.008, combine at weights 0.7/0.3. Expected: outputs match independently computed NumPy sample standard deviation times sqrt(252), and sqrt(w-transpose * sample covariance * w) times sqrt(252), within pytest.approx tolerance. Evidence: [test_volatility.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/c065aef/backend/tests/test_volatility.py), `test_volatility_matches_an_independent_computation` and `test_portfolio_volatility_matches_the_covariance_formula`.

### TC-5-02 | Risk response for each holding and portfolio

**Maps to FR-7 / supports AC5.1. Type: automated API integration. Status: passed September 8.**

Setup: signed-in SQLite/FakeProvider fixture; add AAPL 10 and NVDA 5. Action: GET /api/portfolio/risk. Expected: both holdings have non-null volatility percentages, a valid descriptive band and positive observation count; portfolio volatility/band are also populated. Evidence: [test_risk.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/c065aef/backend/tests/test_risk.py), `test_risk_reports_volatility_for_each_holding_and_the_portfolio`. Additional unit tests return None for fewer than 20 returns; empty-portfolio API tests return no risk instead of failing.

### TC-5-03 | Displayed risk acceptance

**Maps to FR-7 / AC5.1. Type: manual UAT. Status: specified, not executed.**

Setup: isolated signed-in account with AAPL 10 and NVDA 5, sufficient available price history, same recorded lookback. Actions: open the dashboard and capture the corresponding /api/portfolio/risk response; compare the portfolio tile and each holding's displayed volatility with the matching response values. Expected: every priced holding and the portfolio show a labeled percentage consistent with response rounding; missing history is shown as unavailable, not silently reported as zero. Retain sanitized screenshot/response evidence. Do not assume real NVDA is always more volatile than real AAPL; seeded test ordering is not a live-market assertion.

**Traceability:** implementation and initial math/API tests 1b23564 (PR #56); later dashboard integration 23ca50b (PR #59, Sprint 2 baseline, not Sprint 1 throughput); API paths 24d39ef. [ADR 0012](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/c065aef/docs/adr/0012-risk-methodology.md). Specification IDs created/reviewed September 8.
