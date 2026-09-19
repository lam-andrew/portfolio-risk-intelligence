# Sprint 1 unit and system test specifications

Created and reviewed September 15, 2026. Application revision: `83716a2`. Owner: Andrew Lam.

This living document adds five specifications for each of the six Sprint 1 stories (30 total). It complements, rather than renumbers, the 18 Week 3 acceptance specifications in [sprint1-tests.md](sprint1-tests.md). These are reporting specifications for existing automation and planned system procedures, not 30 newly coded tests.

## Environments and execution rules

- Unit: pure engine functions with seeded synthetic data; no HTTP, database, or provider calls.
- API/service integration: actual routes and persistence on isolated SQLite with FakeProvider. These support system requirements but are not live full-stack tests.
- Frontend component unit: Vitest and React Testing Library with mocked HTTP client methods.
- System: real Compose/browser or published API contract; future procedures use disposable accounts and isolated volumes. Do not remove user volumes.
- Local regression on September 15 at 20:49 PDT: 183 backend and 53 frontend tests passed, zero failed or skipped. Python 3.13.7 locally; CI targets Python 3.12. A Starlette/httpx deprecation warning was emitted.
- Of the 30 specifications, 25 map to tests in this local passing run, one to a prior passing container CI run, and four are specified but unexecuted. A shared source test can support two requirements; specifications are not a count of distinct executable tests.
- For pending procedures, record tester, date/time, source revision, environment, expected versus actual results, sanitized evidence, and defect links. Pass only if all expected results hold; use Blocked for environment failures. Cleanup only disposable test resources.
- Original six acceptance procedures remain pending. This specification work does not close stories or claim UAT.

## US-14 Containerized deployment

[AR-1 / issue #14](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/14) | 5 points | Sprint 1

AC14.1: Compose starts communicating frontend, backend and database services. AC14.2: CI builds and tests containers before deployment; hosted CD remains deferred.

### W4-14-01 Connected health response

**Maps to:** AR-1 / AC14.1. **Level:** API integration.

**Preconditions and data:** TestClient; stub database check as connected.

**Procedure:** GET /api/health.

**Expected result and pass criterion:** HTTP 200; status ok; database connected; nonempty service and version.

**Evidence:** `backend/tests/test_health.py::test_health_ok_when_db_connected`.

**Actual result and status:** Passed September 15 in the existing automated suite.

### W4-14-02 Unavailable database response

**Maps to:** AR-1 / AC14.1. **Level:** API integration.

**Preconditions and data:** TestClient; stub database check as unavailable.

**Procedure:** GET /api/health.

**Expected result and pass criterion:** HTTP 200 with database unavailable, permitting diagnosis without crashing. This does not simulate a real database outage.

**Evidence:** `backend/tests/test_health.py::test_health_reports_db_unavailable_without_failing`.

**Actual result and status:** Passed September 15 in the existing automated suite.

### W4-14-03 Optional market data configuration

**Maps to:** AR-1 / AC14.1. **Level:** API integration.

**Preconditions and data:** Connected database stub; initially blank market-data key.

**Procedure:** GET /api/health; set a dummy test token and repeat.

**Expected result and pass criterion:** market_data changes from unconfigured to configured; a missing key does not prevent the health response. No external call occurs.

**Evidence:** `backend/tests/test_health.py::test_health_reports_market_data_configuration`.

**Actual result and status:** Passed September 15 in the existing automated suite.

### W4-14-04 Container build and stack startup

**Maps to:** AR-1 / AC14.1 and AC14.2. **Level:** Automated system smoke.

**Preconditions and data:** GitHub Actions Docker runner at the recorded revision; isolated CI volumes.

**Procedure:** Build both images, run configured checks, start Compose and poll /api/health.

**Expected result and pass criterion:** Backend, frontend and integration jobs pass; database reports connected within the polling limit. CI alone does not establish browser connectivity.

**Evidence:** `.github/workflows/ci.yml`.

**Actual result and status:** Passed in main CI run 34317645071 on September 8 PDT; inspected September 15.

### W4-14-05 Browser reaches the running stack

**Maps to:** AR-1 / AC14.1. **Level:** Manual system.

**Preconditions and data:** Disposable Compose stack, isolated volumes, test account; no market key needed for empty holdings.

**Procedure:** Open port 5173; sign in; open Holdings; inspect its /api/holdings network response.

**Expected result and pass criterion:** Frontend loads, three services run, health reports connected and the browser receives HTTP 200 JSON. Retain sanitized network and service evidence.

**Evidence:** `docs/sprint1-tests.md#tc-14-01--full-stack-developer-acceptance`.

**Actual result and status:** Specified September 15; not executed.

## US-15 Decoupled analysis API

[AR-2 / issue #15](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/15) | 3 points | Sprint 1

AC15.1: Frontend analysis uses the API contract. AC15.2: Another engine can be added without modifying the existing risk engine.

### W4-15-01 API namespace contract

**Maps to:** AR-2 / AC15.1. **Level:** API integration.

**Preconditions and data:** Anonymous TestClient; namespaced health route available.

**Procedure:** Request /api/health, /health and /holdings from the backend.

**Expected result and pass criterion:** Namespaced health returns 200; the two legacy root paths return 404. This verifies routing, not the entire dependency boundary.

**Evidence:** `backend/tests/test_health.py::test_the_api_is_namespaced_under_api`.

**Actual result and status:** Passed September 15 in the existing automated suite.

### W4-15-02 Analysis result through the API

**Maps to:** AR-2 / AC15.1. **Level:** API integration.

**Preconditions and data:** Authenticated SQLite/FakeProvider fixture; AAPL 10 and NVDA 5.

**Procedure:** GET /api/portfolio/risk.

**Expected result and pass criterion:** Response exposes both holding results, portfolio volatility, descriptive bands and positive observation counts through JSON.

**Evidence:** `backend/tests/test_risk.py::test_risk_reports_volatility_for_each_holding_and_the_portfolio`.

**Actual result and status:** Passed September 15 in the existing automated suite.

### W4-15-03 Engine calculation without services

**Maps to:** AR-2 / AC15.1. **Level:** Unit.

**Preconditions and data:** NumPy seed 42; 300 normal returns, mean 0, daily sigma 0.01; no app/database/provider fixture.

**Procedure:** Call annualized_volatility directly and calculate the independent sample-standard-deviation result.

**Expected result and pass criterion:** Outputs agree within pytest.approx. The unit invocation needs no HTTP or persistence; import inspection is separate supporting evidence.

**Evidence:** `backend/tests/test_volatility.py::test_volatility_matches_an_independent_computation`.

**Actual result and status:** Passed September 15 in the existing automated suite.

### W4-15-04 Published analysis contract

**Maps to:** AR-2 / AC15.1. **Level:** System contract.

**Preconditions and data:** Running disposable backend at the recorded revision.

**Procedure:** GET /openapi.json; inspect /api/portfolio/risk and /api/holdings operations and referenced schemas.

**Expected result and pass criterion:** Risk GET and holdings GET/POST are documented; response schemas resolve; application routes use /api. Save sanitized schema assertions.

**Evidence:** `backend/app/api/routes.py; backend/app/api/schemas.py`.

**Actual result and status:** Specified September 15; not executed.

### W4-15-05 Register another isolated engine

**Maps to:** AR-2 / AC15.2. **Level:** Developer system.

**Preconditions and data:** Disposable worktree; baseline risk regression passes; hash existing risk files.

**Procedure:** Add a test engine returning status ok and a test-only API route; request it; rerun risk regression and compare hashes.

**Expected result and pass criterion:** New route returns 200 and status ok; all original risk files are unchanged and risk regressions pass. Retain diff and results; do not merge demonstration code.

**Evidence:** `docs/sprint1-tests.md#tc-15-03--add-an-isolated-test-engine`.

**Actual result and status:** Specified September 15; not executed.

## US-1 Add a holding manually

[FR-1 / issue #1](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/1) | 2 points | Sprint 1

AC1.1: A valid ticker and quantity add and display a holding. AC1.2: An unrecognized ticker produces a clear error and adds nothing.

### W4-1-01 Add and retrieve a holding

**Maps to:** FR-1 / AC1.1. **Level:** API integration.

**Preconditions and data:** Fresh authenticated SQLite/FakeProvider fixture recognizing AAPL.

**Procedure:** POST /api/holdings with AAPL and quantity 10; GET /api/holdings.

**Expected result and pass criterion:** Creation returns 201, identifier, ticker AAPL and quantity 10; listing returns the holding.

**Evidence:** `backend/tests/test_holdings.py::test_add_valid_holding_then_appears_in_list`.

**Actual result and status:** Passed September 15 in the existing automated suite.

### W4-1-02 Reject an unknown ticker

**Maps to:** FR-1 / AC1.2. **Level:** API integration.

**Preconditions and data:** Fresh authenticated fixture; FakeProvider does not recognize ZZZZ.

**Procedure:** POST ZZZZ with quantity 5, then list holdings.

**Expected result and pass criterion:** HTTP 422 with an Unrecognized message; holdings remain empty.

**Evidence:** `backend/tests/test_holdings.py::test_unrecognized_ticker_is_rejected_and_adds_nothing`.

**Actual result and status:** Passed September 15 in the existing automated suite.

### W4-1-03 Normalize user input

**Maps to:** FR-1 / AC1.1. **Level:** API integration.

**Preconditions and data:** Fresh authenticated fixture recognizing AAPL.

**Procedure:** POST ticker "  aapl " and quantity 1.5.

**Expected result and pass criterion:** HTTP 201 and normalized ticker AAPL. Fractional quantity support is also covered by the separate fractional-quantity test.

**Evidence:** `backend/tests/test_holdings.py::test_ticker_is_normalized`.

**Actual result and status:** Passed September 15 in the existing automated suite.

### W4-1-04 Reject nonpositive quantities

**Maps to:** FR-1 / AC1.1 validation. **Level:** API integration.

**Preconditions and data:** Fresh authenticated fixture; valid ticker AAPL.

**Procedure:** POST quantity 0, then quantity -3.

**Expected result and pass criterion:** Both requests return HTTP 422. This existing test checks rejection status; it does not independently query the database after each request.

**Evidence:** `backend/tests/test_holdings.py::test_non_positive_quantity_is_rejected`.

**Actual result and status:** Passed September 15 in the existing automated suite.

### W4-1-05 Reject a duplicate position

**Maps to:** FR-1 / AC1.1 validation. **Level:** API integration.

**Preconditions and data:** Authenticated fixture with MSFT quantity 4 successfully created.

**Procedure:** POST a second MSFT holding with quantity 9.

**Expected result and pass criterion:** HTTP 409 with an already-in-your-portfolio message. Editing is the intended path to changing an existing quantity.

**Evidence:** `backend/tests/test_holdings.py::test_duplicate_ticker_is_rejected`.

**Actual result and status:** Passed September 15 in the existing automated suite.

## US-3 Manage holdings

[FR-4 / issue #3](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/3) | 2 points | Sprint 1

AC3.1: Edited quantities persist and feed analysis. AC3.2: Confirmed deletion removes the holding from subsequent analysis.

### W4-3-01 Persist a quantity edit

**Maps to:** FR-4 / AC3.1. **Level:** API integration.

**Preconditions and data:** Authenticated fixture containing AAPL 10.

**Procedure:** PATCH its holding ID to quantity 12.5; GET /api/holdings.

**Expected result and pass criterion:** HTTP 200 and quantity 12.5 in both the update response and stored listing. Recalculated analysis is covered by case 05.

**Evidence:** `backend/tests/test_holdings.py::test_edit_quantity_is_saved`.

**Actual result and status:** Passed September 15 in the existing automated suite.

### W4-3-02 Preserve quantity on rejected edit

**Maps to:** FR-4 / AC3.1 validation. **Level:** API integration.

**Preconditions and data:** Authenticated fixture containing AAPL 10.

**Procedure:** PATCH quantity 0, then -2; list holdings.

**Expected result and pass criterion:** Each update returns 422; the stored quantity remains 10.

**Evidence:** `backend/tests/test_holdings.py::test_edit_rejects_non_positive_quantity`.

**Actual result and status:** Passed September 15 in the existing automated suite.

### W4-3-03 Delete only the selected holding

**Maps to:** FR-4 / AC3.2. **Level:** API integration.

**Preconditions and data:** Authenticated fixture containing AAPL 10 and MSFT 4.

**Procedure:** DELETE the MSFT ID; GET /api/holdings.

**Expected result and pass criterion:** HTTP 204; only the original AAPL ID remains. Despite its source name, this test does not request a fresh analysis response.

**Evidence:** `backend/tests/test_holdings.py::test_delete_removes_holding_from_further_analysis`.

**Actual result and status:** Passed September 15 in the existing automated suite.

### W4-3-04 Require deletion confirmation

**Maps to:** FR-4 / AC3.2. **Level:** Frontend component unit.

**Preconditions and data:** Render HoldingRow for AAPL ID 7 with mocked deleteHolding and onChanged.

**Procedure:** Click Delete; inspect call count; click Confirm.

**Expected result and pass criterion:** No deletion before confirmation; confirmation calls deleteHolding(7) and invokes onChanged. Browser/backend communication is outside this mock-based test.

**Evidence:** `frontend/src/features/holdings/HoldingRow.test.tsx::requires confirmation before deleting`.

**Actual result and status:** Passed September 15 in the existing automated suite.

### W4-3-05 Reanalyze after edit and deletion

**Maps to:** FR-4 / AC3.1 and AC3.2. **Level:** Manual system.

**Preconditions and data:** Disposable signed-in account; AAPL 10, MSFT 4; fixed cached prices and lookback.

**Procedure:** Capture baseline; edit AAPL to 12.5 and reanalyze; cancel MSFT deletion; then confirm deletion and reanalyze.

**Expected result and pass criterion:** Updated quantity feeds valuation; cancel preserves MSFT; confirmation removes MSFT from holdings and risk response. Rounded volatility need not change. Retain response and browser evidence.

**Evidence:** `docs/sprint1-tests.md#tc-3-03--edit-delete-and-reanalyze`.

**Actual result and status:** Specified September 15; not executed.

## US-4 Retrieve and cache market data

[FR-5 and FR-6 / issue #4](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/4) | 5 points | Sprint 1

AC4.1: A valid ticker retrieves historical prices for analysis. AC4.2: Repeated analysis reuses recently retrieved prices.

### W4-4-01 Retrieve historical prices

**Maps to:** FR-5 / AC4.1. **Level:** API integration.

**Preconditions and data:** Authenticated fixture, empty SQLite cache and FakeProvider.

**Procedure:** GET /api/market-data/AAPL/prices?days=30.

**Expected result and pass criterion:** HTTP 200; source provider; positive count matching bars; dates and adjusted closes present; exactly one provider price call.

**Evidence:** `backend/tests/test_market_data.py::test_prices_are_retrieved_for_a_valid_ticker`.

**Actual result and status:** Passed September 15 in the existing automated suite.

### W4-4-02 Reuse fresh cached prices

**Maps to:** FR-6 / AC4.2. **Level:** API integration.

**Preconditions and data:** Fresh authenticated fixture and FakeProvider.

**Procedure:** Request the same AAPL 30-day history twice.

**Expected result and pass criterion:** First source provider, second cache; identical bars/count; provider.price_calls remains 1.

**Evidence:** `backend/tests/test_market_data.py::test_second_request_is_served_from_cache`.

**Actual result and status:** Passed September 15 in the existing automated suite.

### W4-4-03 Refresh expired cache

**Maps to:** FR-6 / AC4.2 freshness. **Level:** Service integration.

**Preconditions and data:** SQLite service; 24-hour TTL; AAPL from August 20 to August 30, 2026.

**Procedure:** Fetch and repeat; age both bars and coverage by 48 hours; fetch again.

**Expected result and pass criterion:** Sources are provider, cache, provider; provider call count is 2.

**Evidence:** `backend/tests/test_market_data.py::test_stale_cache_triggers_a_refetch`.

**Actual result and status:** Passed September 15 in the existing automated suite.

### W4-4-04 Use cached data during provider failure

**Maps to:** FR-5 and FR-6 / AC4.1 and AC4.2 resilience. **Level:** Service integration.

**Preconditions and data:** Populate the same AAPL window; age cache 48 hours; replace provider with one raising MarketDataError.

**Procedure:** Request the previously cached window again.

**Expected result and pass criterion:** Returns source cache and the original number of bars instead of failing. This does not establish a live-provider outage result.

**Evidence:** `backend/tests/test_market_data.py::test_stale_cache_is_served_when_the_provider_fails`.

**Actual result and status:** Passed September 15 in the existing automated suite.

### W4-4-05 Expand a narrow cached window

**Maps to:** FR-5 and FR-6 / AC4.1 and AC4.2 coverage. **Level:** Service integration.

**Preconditions and data:** Fresh SQLite service and FakeProvider; fixed ending date.

**Procedure:** Fetch 10 days, then 365 days, then an inner 30-day window.

**Expected result and pass criterion:** Wider request goes to provider and contains over five times as many bars; the inner window is cached; total price calls equal 2.

**Evidence:** `backend/tests/test_market_data.py::test_a_narrow_cached_window_does_not_answer_a_wider_request`.

**Actual result and status:** Passed September 15 in the existing automated suite.

## US-5 Holding and portfolio volatility

[FR-7 / issue #5](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/5) | 3 points | Sprint 1

AC5.1: With sufficient price data, the risk view displays volatility for each holding and the portfolio.

### W4-5-01 Calculate simple daily returns

**Maps to:** FR-7 / AC5.1 correctness. **Level:** Unit.

**Preconditions and data:** Adjusted closing prices 100, 110 and 99 as Decimals.

**Procedure:** Call daily_returns.

**Expected result and pass criterion:** Returns match 0.10 and -0.10 within pytest.approx; no database, HTTP or provider is involved.

**Evidence:** `backend/tests/test_volatility.py::test_daily_returns_are_simple_returns`.

**Actual result and status:** Passed September 15 in the existing automated suite.

### W4-5-02 Verify holding volatility independently

**Maps to:** FR-7 / AC5.1 correctness. **Level:** Unit.

**Preconditions and data:** Seed 42; 300 normal returns with mean 0 and daily sigma 0.01.

**Procedure:** Calculate annualized_volatility and NumPy sample standard deviation multiplied by the square root of 252.

**Expected result and pass criterion:** Outputs match within pytest.approx; the independent oracle uses ddof=1.

**Evidence:** `backend/tests/test_volatility.py::test_volatility_matches_an_independent_computation`.

**Actual result and status:** Passed September 15 in the existing automated suite.

### W4-5-03 Verify portfolio covariance calculation

**Maps to:** FR-7 / AC5.1 correctness. **Level:** Unit.

**Preconditions and data:** Seed 17; two 400-return series with sigmas 0.012 and 0.008; weights 0.7 and 0.3.

**Procedure:** Calculate portfolio_volatility and an independent NumPy covariance quadratic form.

**Expected result and pass criterion:** Output equals the square root of the weighted covariance result multiplied by the square root of 252, within pytest.approx.

**Evidence:** `backend/tests/test_volatility.py::test_portfolio_volatility_matches_the_covariance_formula`.

**Actual result and status:** Passed September 15 in the existing automated suite.

### W4-5-04 Withhold estimates on thin history

**Maps to:** FR-7 / AC5.1 data sufficiency. **Level:** Unit.

**Preconditions and data:** Nineteen daily returns of 0.01, below the 20-return minimum, and an empty series.

**Procedure:** Call annualized_volatility for each input.

**Expected result and pass criterion:** Both return None; neither produces a misleading zero or a numerical risk estimate.

**Evidence:** `backend/tests/test_volatility.py::test_too_little_history_returns_none_rather_than_a_noisy_number`.

**Actual result and status:** Passed September 15 in the existing automated suite.

### W4-5-05 Expose holding and portfolio percentages

**Maps to:** FR-7 / AC5.1. **Level:** API integration.

**Preconditions and data:** Authenticated SQLite/FakeProvider fixture; AAPL 10 and NVDA 5.

**Procedure:** GET /api/portfolio/risk.

**Expected result and pass criterion:** Both holdings and portfolio have non-null volatility percentages, valid descriptive bands and positive observations. Rendering is separately covered by pending TC-5-03.

**Evidence:** `backend/tests/test_risk.py::test_risk_reports_volatility_for_each_holding_and_the_portfolio`.

**Actual result and status:** Passed September 15 in the existing automated suite.
