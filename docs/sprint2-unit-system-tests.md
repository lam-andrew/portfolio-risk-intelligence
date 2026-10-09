# Sprint 2 unit and system specifications and Week 7 results


**Specification and execution date:** October 9, 2026

**Owner:** Andrew Lam

**Tested preview:** [cac2730](https://github.com/lam-andrew/portfolio-risk-intelligence/tree/cac2730b322345b2b386a5990b46878e225a9d2c) on `codex/ui-chart-refresh`, PR #94. This is not main.


## Execution boundary

35 cases: 21 unit/component and 13 API/UI integration cases have matching passing automated tests; one full-system case is Not executed. The backend suite passed 316 with 7 PostgreSQL-specific skips; frontend passed 99. No failures. No fresh coverage, lint, build or security result is asserted. No product code changed for this report.

Backend ran inside the existing backend container with isolated SQLite test fixtures and fake providers, `APP_QA_ENABLED=false`, empty Gemini/market keys and `APP_DATABASE_URL=sqlite:///:memory:`. Command: `pytest -q --junitxml=/tmp/orbit-week7-results.xml`. Frontend: `npm test -- --reporter=default --reporter=junit --outputFile=/tmp/orbit-week7-results.xml`. Local JUnit records are retained with Week 7 report supporting files.

API integration means real routes/services with isolated SQLite and a fake provider. UI integration means route/component rendering with mocked API responses. Neither establishes full deployed browser-to-PostgreSQL acceptance. Unit inputs have no side effects; API fixtures are discarded at teardown; UI DOM and mocks are reset between cases. Use the linked source fixtures for exact data and runner setup.

[Retained 14 UAT specifications](sprint2-tests.md) remain Not executed, as do the five Sprint 1 carryover procedures in the [plan](sprint2-plan.md). Numerical expectations follow the linked assertions and `pytest.approx` where applicable.


## Traceability

| Story / requirement | Unit/system specifications | UAT | Outcome |
|---|---|---|---|

| [US-13](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/13) / FR-15 | W7-13-01–05 | W6-UAT-13-01–02 | 5 passed |

| [US-2](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/2) / FR-2 and FR-3 | W7-2-01–05 | W6-UAT-2-01–02 | 5 passed |

| [US-6](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/6) / FR-8 | W7-6-01–05 | W6-UAT-6-01–02 | 5 passed |

| [US-7](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/7) / FR-9 | W7-7-01–05 | W6-UAT-7-01–02 | 5 passed |

| [US-8](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/8) / FR-10 | W7-8-01–05 | W6-UAT-8-01–02 | 5 passed |

| [US-10](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/10) / FR-12 | W7-10-01–05 | W6-UAT-10-01–02 | 5 passed |

| [US-19](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/62) / FR-12 support | W7-19-01–05 | W6-UAT-19-01–02 | 4 passed; 1 not executed |



## US-13 Authentication

AC1: Given an existing account, valid credentials grant access to that user’s portfolio.
AC2: Invalid credentials deny access and produce a clear message.


[Original implementation 734419e](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/734419e); [PR #67](https://github.com/lam-andrew/portfolio-risk-intelligence/pull/67). Actual implementation date: Aug 31, 2026. [Wireframe WF-13](design/sprint2-wireframes.md).


### W7-13-01 Password storage

**Trace:** FR-15 / US-13 / AC1

**Level:** Unit

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** Password correct-horse-battery.

**Steps:** 1. Hash the password. 2. Inspect the returned string.

**Expected:** Argon2id prefix is present; plaintext password is absent.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [backend/tests/test_auth.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/backend/tests/test_auth.py#L23) — `test_passwords_are_hashed_not_stored`


### W7-13-02 Correct and wrong passwords

**Trace:** FR-15 / US-13 / AC1/AC2

**Level:** Unit

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** Hash of correct-horse-battery; correct password and wrong.

**Steps:** 1. Verify the correct password. 2. Verify wrong against the same hash.

**Expected:** Verification returns true, then false.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [backend/tests/test_auth.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/backend/tests/test_auth.py#L34) — `test_verification_accepts_the_right_password_and_rejects_others`


### W7-13-03 Corrupt hash

**Trace:** FR-15 / US-13 / AC2

**Level:** Unit

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** Password correct-horse-battery; stored string not-a-hash.

**Steps:** 1. Call password verification with the malformed hash.

**Expected:** Returns false without an exception or authenticated session.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [backend/tests/test_auth.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/backend/tests/test_auth.py#L40) — `test_verification_returns_false_for_a_corrupt_hash`


### W7-13-04 Login across HTTP and session storage

**Trace:** FR-15 / US-13 / AC1

**Level:** API integration

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** Disposable user@example.com account with the test password.

**Steps:** 1. Register the account. 2. Log out. 3. POST correct credentials to /api/auth/login. 4. GET /api/auth/me.

**Expected:** Login and the authenticated identity request both return HTTP 200.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [backend/tests/test_auth.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/backend/tests/test_auth.py#L99) — `test_login_succeeds_with_correct_credentials`


### W7-13-05 Rejected login response

**Trace:** FR-15 / US-13 / AC2

**Level:** API integration

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** Disposable registered account; incorrect password.

**Steps:** 1. Register and log out. 2. POST incorrect credentials to /api/auth/login. 3. Inspect the response.

**Expected:** HTTP 401 and a clear invalid email/password message; no successful login.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [backend/tests/test_auth.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/backend/tests/test_auth.py#L112) — `test_wrong_password_is_denied_with_a_clear_message`



## US-2 CSV portfolio import

AC1: A correctly formatted CSV imports all valid holdings.
AC2: Unparseable rows are reported while valid rows still import.


[Original implementation e4baa80](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/e4baa80); [PR #57](https://github.com/lam-andrew/portfolio-risk-intelligence/pull/57). Actual implementation date: Aug 30, 2026. [Wireframe WF-2](design/sprint2-wireframes.md).


### W7-2-01 Combine repeated symbols

**Trace:** FR-2 and FR-3 / US-2 / AC1

**Level:** Unit

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** CSV Symbol,Quantity with AAPL,10 and AAPL,15.

**Steps:** 1. Encode the CSV as UTF-8. 2. Parse it. 3. Inspect holdings.

**Expected:** One AAPL holding with exact decimal quantity 25.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [backend/tests/test_csv_import.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/backend/tests/test_csv_import.py#L103) — `test_duplicate_symbols_are_combined`


### W7-2-02 Missing required columns

**Trace:** FR-2 and FR-3 / US-2 / AC2

**Level:** Unit

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** CSV Name,Address with Bob,123 Main St.

**Steps:** 1. Parse the file. 2. Inspect holdings and reported problems.

**Expected:** No holdings; a problem explains that a ticker column could not be found.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [backend/tests/test_csv_import.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/backend/tests/test_csv_import.py#L109) — `test_file_without_recognizable_columns_is_reported`


### W7-2-03 Mixed row validation

**Trace:** FR-2 and FR-3 / US-2 / AC1/AC2

**Level:** Unit

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** Repository fixture backend/tests/fixtures/messy.csv.

**Steps:** 1. Parse the fixture. 2. Compare holdings. 3. Inspect row numbers and reasons.

**Expected:** AAPL 125 and TSLA 1000.5 survive; invalid ticker, unreadable and nonpositive quantities have reasons and file-line numbers greater than 1.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [backend/tests/test_csv_import.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/backend/tests/test_csv_import.py#L122) — `test_bad_rows_are_reported_with_reasons_and_row_numbers`


### W7-2-04 Upload and persisted listing

**Trace:** FR-2 and FR-3 / US-2 / AC1

**Level:** API integration

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** Authenticated empty account; vanguard_positions.csv fixture.

**Steps:** 1. POST multipart CSV to /api/holdings/import. 2. GET /api/holdings.

**Expected:** HTTP 200; added list contains BND and VTI, no problems, and both tickers appear in persisted holdings.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [backend/tests/test_csv_import.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/backend/tests/test_csv_import.py#L139) — `test_import_adds_holdings_and_they_appear_in_the_portfolio`


### W7-2-05 Partial import through API

**Trace:** FR-2 and FR-3 / US-2 / AC1/AC2

**Level:** API integration

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** Authenticated empty account; messy.csv fixture.

**Steps:** 1. Upload the CSV. 2. Inspect added items and problems. 3. GET holdings.

**Expected:** AAPL is added and persisted. At least three problems contain row, reason and content fields; good rows are retained.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [backend/tests/test_csv_import.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/backend/tests/test_csv_import.py#L152) — `test_import_reports_bad_rows_while_importing_good_ones`



## US-6 Correlation among holdings

AC1: For two or more holdings with price data, the correlation view displays their correlation structure.


[Original implementation c003351](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/c003351); [PR #58](https://github.com/lam-andrew/portfolio-risk-intelligence/pull/58). Actual implementation date: Aug 30, 2026. [Wireframe WF-6](design/sprint2-wireframes.md).


### W7-6-01 Matrix mathematical structure

**Trace:** FR-8 / US-6 / AC1

**Level:** Unit

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** 300 returns each from seeded series 1, 2 and 3 in the test module.

**Steps:** 1. Calculate the matrix. 2. Compare diagonal and mirrored cells.

**Expected:** Diagonal is 1 and the matrix is symmetric within pytest numerical tolerance.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [backend/tests/test_correlation.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/backend/tests/test_correlation.py#L28) — `test_diagonal_is_one_and_matrix_is_symmetric`


### W7-6-02 Independent Pearson oracle

**Trace:** FR-8 / US-6 / AC1

**Level:** Unit

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** Three seeded return series 8, 9 and 10.

**Steps:** 1. Calculate Orbit correlation. 2. Calculate numpy.corrcoef independently. 3. Compare every cell.

**Expected:** All cells agree with the independent calculation within pytest.approx tolerance.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [backend/tests/test_correlation.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/backend/tests/test_correlation.py#L58) — `test_matches_numpy_corrcoef`


### W7-6-03 Zero variance is undefined

**Trace:** FR-8 / US-6 / AC1 boundary

**Level:** Unit

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** Variable returns from seed 22 and 300 zero returns.

**Steps:** 1. Calculate the two-series correlation matrix. 2. Inspect the pair.

**Expected:** The undefined pair is None, not a measured correlation of zero.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [backend/tests/test_correlation.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/backend/tests/test_correlation.py#L105) — `test_constant_series_yields_none_not_zero`


### W7-6-04 Correlation API contract

**Trace:** FR-8 / US-6 / AC1

**Level:** API integration

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** Fake provider; AAPL 10, MSFT 5, VTI 8 in the authenticated account.

**Steps:** 1. Add holdings. 2. GET /api/portfolio/correlation. 3. Check labels, dimensions and cells.

**Expected:** Three labels; a symmetric 3×3 matrix, unit diagonal, every value within −1…1, positive observations and a non-null average.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [backend/tests/test_risk.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/backend/tests/test_risk.py#L113) — `test_correlation_returns_a_symmetric_matrix_for_the_holdings`


### W7-6-05 One holding boundary

**Trace:** FR-8 / US-6 / AC1 boundary

**Level:** API integration

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** Fake provider; only AAPL 10.

**Steps:** 1. Add the holding. 2. GET /api/portfolio/correlation.

**Expected:** Empty tickers/matrix and null average; the API does not fabricate a pair.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [backend/tests/test_risk.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/backend/tests/test_risk.py#L154) — `test_correlation_needs_two_holdings`



## US-7 Concentration and overlapping exposure

AC1: The exposure view highlights overweight positions and overlapping exposure across analyzed holdings.


[Original implementation bd0bcf9](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/bd0bcf9); [PR #60](https://github.com/lam-andrew/portfolio-risk-intelligence/pull/60). Actual implementation date: Aug 30, 2026. [Wireframe WF-7](design/sprint2-wireframes.md).


### W7-7-01 Equal weight concentration

**Trace:** FR-9 / US-7 / AC1

**Level:** Unit

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** Four weights of 0.25; then ten weights of 0.10.

**Steps:** 1. Calculate the Herfindahl index for each list.

**Expected:** HHI is 0.25 and 0.10 respectively (sum of squared weights).

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [backend/tests/test_concentration.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/backend/tests/test_concentration.py#L19) — `test_equal_weights_give_hhi_of_one_over_n`


### W7-7-02 Overweight threshold

**Trace:** FR-9 / US-7 / AC1

**Level:** Unit

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** BIG .55, MID .25, A .10 and B .10.

**Steps:** 1. Construct four Position values. 2. Identify overweight positions.

**Expected:** Only BIG exceeds twice the equal-weight baseline, 2/4=0.50.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [backend/tests/test_concentration.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/backend/tests/test_concentration.py#L75) — `test_overweight_uses_an_equal_weight_baseline`


### W7-7-03 Overlapping group

**Trace:** FR-9 / US-7 / AC1

**Level:** Unit

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** VOO/VTI/QQQ/BND weights .30/.25/.25/.20 and the module MATRIX fixture.

**Steps:** 1. Group positions using the fixture correlations. 2. Inspect membership and weight.

**Expected:** One group contains QQQ, VOO, VTI; combined weight .80 and minimum within-group correlation .92.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [backend/tests/test_concentration.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/backend/tests/test_concentration.py#L116) — `test_overlapping_holdings_are_grouped_with_a_combined_weight`


### W7-7-04 Concentration API summary

**Trace:** FR-9 / US-7 / AC1

**Level:** API integration

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** Fake provider; AAPL, MSFT and VTI, 10 shares each.

**Steps:** 1. Add holdings. 2. GET /api/portfolio/concentration. 3. Inspect computed summary.

**Expected:** Three holdings; positive HHI, effective count 1…3, top-1 no greater than top-3, and top-3 equals 100%.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [backend/tests/test_exposure.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/backend/tests/test_exposure.py#L22) — `test_concentration_reports_hhi_and_effective_holdings`


### W7-7-05 Dominant position across API

**Trace:** FR-9 / US-7 / AC1

**Level:** API integration

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** Fake provider; AAPL 10000, MSFT 1 and VTI 1.

**Steps:** 1. Add holdings. 2. Request concentration. 3. Inspect effective count and overweight list.

**Expected:** Effective count below 1.5; top holding above 90%; only AAPL overweight, at more than twice equal weight.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [backend/tests/test_exposure.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/backend/tests/test_exposure.py#L38) — `test_a_dominant_position_drives_effective_holdings_toward_one`



## US-8 Historical drawdown

AC1: With sufficient price history, the drawdown view shows the largest peak-to-trough declines over the period.


[Original implementation bd0bcf9](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/bd0bcf9); [PR #60](https://github.com/lam-andrew/portfolio-risk-intelligence/pull/60). Actual implementation date: Aug 30, 2026. [Wireframe WF-8](design/sprint2-wireframes.md).


### W7-8-01 Running peak calculation

**Trace:** FR-10 / US-8 / AC1

**Level:** Unit

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** Values 100, 90, 95, 100, 120, 60.

**Steps:** 1. Calculate the drawdown series. 2. Compare each value with its prior running peak.

**Expected:** Declines are 0, −.10, −.05, 0, 0, −.50. Future peaks do not change earlier declines.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [backend/tests/test_drawdown.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/backend/tests/test_drawdown.py#L32) — `test_decline_is_measured_from_the_running_peak`


### W7-8-02 Recovered episode

**Trace:** FR-10 / US-8 / AC1

**Level:** Unit

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** Values 100,90,80,90,100,105 on consecutive dates from Jan 1, 2026.

**Steps:** 1. Extract drawdown episodes. 2. Inspect dates, depth and durations.

**Expected:** One episode: Jan 1 peak, Jan 3 trough, Jan 5 recovery, depth −20%, two decline days and two recovery days.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [backend/tests/test_drawdown.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/backend/tests/test_drawdown.py#L71) — `test_a_recovered_episode_records_peak_trough_and_recovery`


### W7-8-03 Ongoing episode

**Trace:** FR-10 / US-8 / AC1

**Level:** Unit

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** Values 100,120,90 on Jan 1–3, 2026.

**Steps:** 1. Extract episodes. 2. Inspect the final decline and recovery fields.

**Expected:** Peak Jan 2, trough Jan 3, depth −25%; unrecovered with no recovery date or duration.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [backend/tests/test_drawdown.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/backend/tests/test_drawdown.py#L86) — `test_an_ongoing_decline_is_reported_as_unrecovered`


### W7-8-04 Drawdown API response

**Trace:** FR-10 / US-8 / AC1

**Level:** API integration

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** Fake provider; AAPL 10 and NVDA 5.

**Steps:** 1. Add holdings. 2. GET /api/portfolio/drawdown. 3. Inspect summary and dated series.

**Expected:** Negative maximum, nonpositive current decline, more than 100 dated points in order, and no positive drawdown values.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [backend/tests/test_exposure.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/backend/tests/test_exposure.py#L99) — `test_drawdown_reports_max_current_and_a_series`


### W7-8-05 Summary agrees with series

**Trace:** FR-10 / US-8 / AC1

**Level:** API integration

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** Authenticated fixture portfolio and fake historical prices from the linked test.

**Steps:** 1. Request drawdown. 2. Compute the minimum returned series percentage. 3. Compare with maximum drawdown.

**Expected:** Reported maximum drawdown equals the worst point in its own series.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [backend/tests/test_exposure.py](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/backend/tests/test_exposure.py#L152) — `test_max_drawdown_matches_the_worst_point_of_the_series`



## US-10 Risk dashboard

AC1: Opening an analyzed portfolio’s dashboard presents risk metrics with supporting visualizations.


[Original implementation 23ca50b](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/23ca50b); [PR #59](https://github.com/lam-andrew/portfolio-risk-intelligence/pull/59). Actual implementation date: Aug 30, 2026. [Wireframe WF-10](design/sprint2-wireframes.md).


### W7-10-01 Allocation grouping preserves meaning

**Trace:** FR-12 / US-10 / AC1

**Level:** Component unit

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** Position weights 30,20,15,10,10,5,5,5 percent.

**Steps:** 1. Render AllocationChart. 2. Select Other holdings.

**Expected:** Accessible chart label reports Other holdings 15.0%; selected control has aria-pressed=true.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [frontend/src/components/charts/charts.test.tsx](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/frontend/src/components/charts/charts.test.tsx#L18) — `groups a long allocation without losing weight and supports selection`


### W7-10-02 Inspectable line chart

**Trace:** FR-12 / US-10 / AC1

**Level:** Component unit

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** Sept 1 value 100; Sept 2 value 80; unit USD.

**Steps:** 1. Render LineChart. 2. Move its slider to index 0.

**Expected:** Status text reports 2026-09-01 · $100; a keyboard-accessible control exposes exact values.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [frontend/src/components/charts/charts.test.tsx](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/frontend/src/components/charts/charts.test.tsx#L40) — `exposes exact date and value through keyboard-friendly inspection`


### W7-10-03 Dashboard integration summary

**Trace:** FR-12 / US-10 / AC1

**Level:** UI integration

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** Authenticated App fixture with portfolio value $5,366.30 and volatility 17.9%.

**Steps:** 1. Render the root route. 2. Wait for analysis. 3. Inspect summary labels and values.

**Expected:** Value, volatility, Moderate band, average correlation, effective holdings 2.9 and Worst decline are visible.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [frontend/src/App.test.tsx](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/frontend/src/App.test.tsx#L188) — `presents summary tiles before the detail`


### W7-10-04 Value history accessibility

**Trace:** FR-12 / US-10 / AC1

**Level:** UI integration

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** Authenticated App fixture with history response.

**Steps:** 1. Render the dashboard route. 2. Wait for the history visualization.

**Expected:** An image role is exposed with accessible name Portfolio value over time.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [frontend/src/App.test.tsx](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/frontend/src/App.test.tsx#L208) — `renders value history as a labelled image`


### W7-10-05 Empty portfolio guidance

**Trace:** FR-12 / US-10 / AC1 boundary

**Level:** UI integration

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** App response fixture with positions=[] and no holdings.

**Steps:** 1. Restore mocks. 2. Supply the empty response. 3. Render the root route.

**Expected:** No holdings yet guidance is displayed.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [frontend/src/App.test.tsx](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/frontend/src/App.test.tsx#L224) — `prompts to add holdings when the portfolio is empty`



## US-19 Risk methodology companion

AC1: Explain volatility, correlation, concentration and drawdown in plain language with formulas.
AC2: Use the analyzed portfolio’s own figures as examples. AC3: Link each metric to its explanation. AC4: State known limitations plainly.


[Original implementation 9794b55](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/9794b55); [PR #63](https://github.com/lam-andrew/portfolio-risk-intelligence/pull/63). Actual implementation date: Aug 30, 2026. [Wireframe WF-19](design/sprint2-wireframes.md).


### W7-19-01 Metric formulas and headings

**Trace:** FR-12 support / US-19 / AC1

**Level:** Component unit

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** MethodologyPage full fixture, MemoryRouter wrapper.

**Steps:** 1. Render the page. 2. Inspect metric headings and formula text.

**Expected:** Volatility, correlation, concentration and drawdown headings and corresponding formulas are present, consistent with ADR 0012.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [frontend/src/pages/MethodologyPage.test.tsx](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/frontend/src/pages/MethodologyPage.test.tsx#L75) — `explains every metric with its formula`


### W7-19-02 Personalized worked examples

**Trace:** FR-12 support / US-19 / AC2

**Level:** Component unit

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** Full fixture: volatility 30.20%, undiversified 34.89%, effective 2.88, 11 holdings, worst decline −24.43%, 249 observations.

**Steps:** 1. Render the fixture. 2. Compare worked examples with the inputs.

**Expected:** Examples display 30.2%, 34.9%, 2.88, 11, −24.4%, 249 and VOO / VTI.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [frontend/src/pages/MethodologyPage.test.tsx](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/frontend/src/pages/MethodologyPage.test.tsx#L104) — `uses the reader's own figures as the worked examples`


### W7-19-03 Explicit model limitations

**Trace:** FR-12 support / US-19 / AC4

**Level:** Component unit

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** Full methodology fixture.

**Steps:** 1. Render the page. 2. Inspect What to scrutinize.

**Expected:** Text addresses crisis correlations, lack of sector look-through, backtesting today’s holdings, stress testing and no investment advice.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [frontend/src/pages/MethodologyPage.test.tsx](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/frontend/src/pages/MethodologyPage.test.tsx#L127) — `states the limitations rather than omitting them`


### W7-19-04 No fabricated examples

**Trace:** FR-12 support / US-19 / AC1/AC2 boundary

**Level:** Component unit

**Method/status:** Automated; Passed October 9

**Preconditions:** Use the linked test module and its fixture. API tests receive an isolated database and authenticated test client except login cases, which create/sign out their own account; frontend uses a fresh DOM and router with mocked API responses. Pure units need no network or database.

**Inputs:** Empty PortfolioData fixture with analytics null.

**Steps:** 1. Render the empty state. 2. Inspect correlation and HHI content. 3. Search for personalized effective count.

**Expected:** General explanations remain; the personalized value 2.88 is absent.

**Actual:** The exact linked test passed with the expected assertions; no failure/error in JUnit.

**Postconditions:** Pure inputs remain unchanged; API data is discarded by fixture teardown; UI components are unmounted and mocks restored.

**Evidence:** [frontend/src/pages/MethodologyPage.test.tsx](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/frontend/src/pages/MethodologyPage.test.tsx#L116) — `still explains the method when there is no portfolio yet`


### W7-19-05 Metric links through the running product

**Trace:** FR-12 support / US-19 / AC2/AC3

**Level:** Full system

**Method/status:** Manual full-system procedure planned; Not executed

**Preconditions:** Running disposable stack, authenticated test account and populated analysis; capture baseline API response.

**Inputs:** Disposable signed-in account with analyzed holdings; save its analysis response.

**Steps:** 1. Open the running dashboard. 2. Follow each volatility, correlation, concentration and drawdown explanation link. 3. Compare destination and personalized figures with the saved response.

**Expected:** Each link reaches the matching methodology section, figures agree after rounding, and holdings remain unchanged.

**Actual:** Not recorded; do not infer success from a component test.

**Postconditions:** Holdings unchanged; preserve comparison and navigation evidence, then reset the disposable account.

**Evidence:** [frontend/src/pages/MethodologyPage.test.tsx](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/cac2730b322345b2b386a5990b46878e225a9d2c/frontend/src/pages/MethodologyPage.test.tsx#L1) (partial component coverage only)


## Analysis and outstanding work

The run found no new application defect. Deterministic math and presentation checks passed, but full browser acceptance, live market-provider/cache verification and native PostgreSQL runs remain outstanding. W7-19-05 extends the metric-link portion of W6-UAT-19-02; record each assertion before sharing evidence. Week 8 must measure coverage by component, finish manual acceptance and resolve the main-based PR #95 typing blocker before closure. No issue is marked Done by this document.
