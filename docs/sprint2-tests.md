# Sprint 2 acceptance and test specifications

**Created/reviewed:** September 28, 2026  
**Owner:** Andrew Lam  
**Status:** Specification; all new procedures Not executed at this cutoff.

## Execution conventions

Run against isolated accounts and a disposable database. Use deterministic provider fixtures for numerical checks; label live-provider checks separately. UI response fixtures establish presentation behavior, followed by a full-stack API/UI comparison for integration. Do not mutate the development user’s portfolio. Record date, revision, environment, actual result, status, evidence and defect links. Never commit secrets or cached external data. Statistical tolerance: absolute 0.000001 before UI rounding.

14 UAT procedures plus seven unit and seven system groups cover all selected requirements. Groups may contain many automated cases; the 28 specification records are not a count of executed tests. Existing CI success does not imply these new procedures have passed.

## Traceability

| Requirement/story | UAT procedures | Unit/system groups | Status |
|---|---|---|---|
| FR-15 / US-13 | W6-UAT-13-01, W6-UAT-13-02 | W6-UNIT-13, W6-SYS-13 | Not executed |
| FR-2 and FR-3 / US-2 | W6-UAT-2-01, W6-UAT-2-02 | W6-UNIT-2, W6-SYS-2 | Not executed |
| FR-8 / US-6 | W6-UAT-6-01, W6-UAT-6-02 | W6-UNIT-6, W6-SYS-6 | Not executed |
| FR-9 / US-7 | W6-UAT-7-01, W6-UAT-7-02 | W6-UNIT-7, W6-SYS-7 | Not executed |
| FR-10 / US-8 | W6-UAT-8-01, W6-UAT-8-02 | W6-UNIT-8, W6-SYS-8 | Not executed |
| FR-12 / US-10 | W6-UAT-10-01, W6-UAT-10-02 | W6-UNIT-10, W6-SYS-10 | Not executed |
| FR-12 support / US-19 | W6-UAT-19-01, W6-UAT-19-02 | W6-UNIT-19, W6-SYS-19 | Not executed |

## US-13 Authentication

FR-15 · 3 points · [Issue #13](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/13) · [Implementation 734419e](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/734419e) · [PR #67](https://github.com/lam-andrew/portfolio-risk-intelligence/pull/67)

- AC1: Given an existing account, valid credentials grant access to that user’s portfolio.
- AC2: Invalid credentials deny access and produce a clear message.

### W6-UAT-13-01

**Mapping:** AC1  
**Method:** Manual browser / semi-automated fixture setup  
**Status:** Not executed

**Preconditions:** Existing disposable account A with a known test password and one holding; fresh signed-out browser.

**Inputs:** Correct email and password for account A.

**Steps:** 1. Open Orbit and sign in. 2. Open Holdings and Risk. 3. Reload the page. 4. Sign out and revisit the protected route.

**Expected result:** Login grants access; A’s holding is shown; reload preserves the valid session. After logout, protected portfolio data is unavailable and sign-in is required.

**Postconditions:** Account data remains intact; session is revoked after logout.

### W6-UAT-13-02

**Mapping:** AC2  
**Method:** Manual browser / semi-automated fixture setup  
**Status:** Not executed

**Preconditions:** Same account; signed out. Capture only sanitized screenshots and HTTP status.

**Inputs:** Account A email with an incorrect password, then an unknown email.

**Steps:** 1. Submit each credential pair. 2. Inspect the visible response. 3. Request the protected holdings route without a session.

**Expected result:** Each login is denied with a clear error and no portfolio displayed; unauthenticated API access returns 401. The error must not expose whether an email is registered.

**Postconditions:** No authenticated session or holding is created.

### W6-UNIT-13

**Method:** Automated pytest or Vitest  
**Status:** Planned regression group; not newly executed for this specification.

test_auth.py: hashing, verification, expired/revoked sessions and case-normalized email. Existing automated tests are the starting point; add regressions for any acceptance defects.

### W6-SYS-13

**Method:** Automated API/component regression plus specified browser integration verification  
**Status:** Planned regression group; not newly executed for this specification.

test_auth.py and test_api.py plus App.test.tsx: login cookie, authenticated requests, unauthorized access, logout and user isolation. Execute across a disposable PostgreSQL-backed stack as well as deterministic fixtures.

## US-2 CSV portfolio import

FR-2 and FR-3 · 3 points · [Issue #2](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/2) · [Implementation e4baa80](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/e4baa80) · [PR #57](https://github.com/lam-andrew/portfolio-risk-intelligence/pull/57)

- AC1: A correctly formatted CSV imports all valid holdings.
- AC2: Unparseable rows are reported while valid rows still import.

### W6-UAT-2-01

**Mapping:** AC1 / FR-2  
**Method:** Manual browser / semi-automated fixture setup  
**Status:** Not executed

**Preconditions:** Signed-in disposable account with an empty portfolio. Use backend/tests/fixtures/simple.csv.

**Inputs:** Ticker/quantity rows AAPL 10 and MSFT 5.5.

**Steps:** 1. Open Holdings. 2. Upload simple.csv. 3. Read the import result. 4. Reload Holdings.

**Expected result:** Two valid holdings import; AAPL quantity 10 and MSFT quantity 5.5 appear and persist after reload. Import response reports no row problems.

**Postconditions:** The account contains exactly these two holdings; preserve the evidence before resetting the disposable fixture.

### W6-UAT-2-02

**Mapping:** AC2 / FR-3  
**Method:** Manual browser / semi-automated fixture setup  
**Status:** Not executed

**Preconditions:** Separate empty disposable portfolio. Create a UTF-8 CSV with header Symbol,Quantity.

**Inputs:** Rows: AAPL,10; MSFT,abc; TSLA,-5 (file lines 2, 3 and 4).

**Steps:** 1. Upload the file. 2. Inspect imported holdings and error details. 3. Reload and compare the stored portfolio.

**Expected result:** AAPL imports with quantity 10. Lines 3 and 4 are rejected with quantity-related reasons; neither invalid holding is stored. The successful row is not rolled back.

**Postconditions:** Only AAPL remains. Capture the row numbers and reasons, without real brokerage-account information.

### W6-UNIT-2

**Method:** Automated pytest or Vitest  
**Status:** Planned regression group; not newly executed for this specification.

test_csv_import.py: simple, Fidelity, Schwab and Vanguard fixtures; decimal formatting, repeated tickers, missing columns, invalid quantities and empty files.

### W6-SYS-2

**Method:** Automated API/component regression plus specified browser integration verification  
**Status:** Planned regression group; not newly executed for this specification.

test_csv_import.py: multipart upload to /api/holdings/import followed by /api/holdings persistence checks. ImportCard.test.tsx: counts, detected columns, row errors and request failures.

## US-6 Correlation among holdings

FR-8 · 5 points · [Issue #6](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/6) · [Implementation c003351](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/c003351) · [PR #58](https://github.com/lam-andrew/portfolio-risk-intelligence/pull/58)

- AC1: For two or more holdings with price data, the correlation view displays their correlation structure.

### W6-UAT-6-01

**Mapping:** AC1  
**Method:** Manual browser / semi-automated fixture setup  
**Status:** Not executed

**Preconditions:** Disposable portfolio with AAPL and MSFT, each with 25 aligned adjusted closes supplied by a deterministic test provider.

**Inputs:** AAPL prices P(t)=100×1.01^ceil(t/2)×0.99^floor(t/2), t=0…24; MSFT prices 2×P(t).

**Steps:** 1. Load the fixture through the test provider. 2. Analyze the portfolio. 3. Open correlation. 4. Compare each matrix cell with the API result.

**Expected result:** Both labels appear; diagonal values are 1 and off-diagonal correlation is approximately +1 (absolute tolerance 0.000001). The displayed rounding agrees with the API.

**Postconditions:** Read-only analysis; holdings and fixture prices remain unchanged.

### W6-UAT-6-02

**Mapping:** AC1 boundary  
**Method:** Manual browser / semi-automated fixture setup  
**Status:** Not executed

**Preconditions:** Same dated fixture, but MSFT prices are constant at 200.

**Inputs:** AAPL variable-return history; MSFT zero-variance history.

**Steps:** 1. Analyze again with the constant series. 2. Open the correlation view. 3. Inspect the API’s corresponding undefined value.

**Expected result:** The pair is explicitly unavailable/undefined, with no crash. The UI does not show a measured 0 or +1 for an undefined pair.

**Postconditions:** No fabricated correlation is stored or displayed; record a defect if the unavailable state is ambiguous.

### W6-UNIT-6

**Method:** Automated pytest or Vitest  
**Status:** Planned regression group; not newly executed for this specification.

test_correlation.py: independently calculated Pearson results, perfect positive/negative relationships, symmetry, diagonal, range, constant returns and mismatched series.

### W6-SYS-6

**Method:** Automated API/component regression plus specified browser integration verification  
**Status:** Planned regression group; not newly executed for this specification.

test_api.py and App.test.tsx: analysis response through the correlation view, correct holding labels and insufficient-data state. Use a deterministic market provider with aligned dates.

## US-7 Concentration and overlapping exposure

FR-9 · 3 points · [Issue #7](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/7) · [Implementation bd0bcf9](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/bd0bcf9) · [PR #60](https://github.com/lam-andrew/portfolio-risk-intelligence/pull/60)

- AC1: The exposure view highlights overweight positions and overlapping exposure across analyzed holdings.

### W6-UAT-7-01

**Mapping:** AC1 overweight  
**Method:** Manual browser / semi-automated fixture setup  
**Status:** Not executed

**Preconditions:** Authenticated browser using an analysis fixture with four positions; all valuation inputs are available.

**Inputs:** Weights BIG 0.55, MID 0.25, A 0.10, B 0.10.

**Steps:** 1. Open Exposure. 2. Read position weights and highlighted positions. 3. Compare HHI and effective count with the fixture calculation.

**Expected result:** Only BIG exceeds 2/4=0.50. HHI is 0.385; effective holdings are 1/0.385≈2.60. Displayed percentages and rounding agree with these values.

**Postconditions:** Viewing the exposure does not change the portfolio.

### W6-UAT-7-02

**Mapping:** AC1 overlap  
**Method:** Manual browser / semi-automated fixture setup  
**Status:** Not executed

**Preconditions:** Authenticated test browser with the correlation matrix from test_concentration.py.

**Inputs:** VOO/VTI/QQQ weights 0.30/0.25/0.25; BND 0.20. Equity pair correlations 1.00, 0.93, 0.92; BND pairs below 0.75.

**Steps:** 1. Open overlapping exposure. 2. Inspect group membership and total weight. 3. Read the explanatory text.

**Expected result:** VOO, VTI and QQQ form the overlapping group with combined weight 80%; BND is excluded. The explanation identifies similar historical behavior rather than claiming identical underlying holdings.

**Postconditions:** No portfolio mutation. Save the fixture, response and screen as acceptance evidence.

### W6-UNIT-7

**Method:** Automated pytest or Vitest  
**Status:** Planned regression group; not newly executed for this specification.

test_concentration.py: normalized HHI, effective holdings, top-N weights, 2/n overweight rule, correlation-based groups and undefined-correlation exclusions.

### W6-SYS-7

**Method:** Automated API/component regression plus specified browser integration verification  
**Status:** Planned regression group; not newly executed for this specification.

test_api.py and App.test.tsx: exposure payloads render matching weights, flags and groups. Exercise a known analysis-response fixture and then compare a real stack response with the displayed result.

## US-8 Historical drawdown

FR-10 · 2 points · [Issue #8](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/8) · [Implementation bd0bcf9](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/bd0bcf9) · [PR #60](https://github.com/lam-andrew/portfolio-risk-intelligence/pull/60)

- AC1: With sufficient price history, the drawdown view shows the largest peak-to-trough declines over the period.

### W6-UAT-8-01

**Mapping:** AC1 recovered decline  
**Method:** Manual browser / semi-automated fixture setup  
**Status:** Not executed

**Preconditions:** Authenticated browser; deterministic analysis fixture. Provide 20 initial daily values of 100, then the six listed values on consecutive fixture dates.

**Inputs:** Subsequent values: 100, 80, 100, 120, 72, 130.

**Steps:** 1. Analyze the fixture. 2. Open Drawdown. 3. Inspect the deepest episode and chart. 4. Compare peak, trough and recovery with the input dates.

**Expected result:** Largest drawdown is 72/120−1=−40%; its peak is the date at 120, trough the following date at 72, and recovery the date at 130. Current drawdown is 0.

**Postconditions:** Read-only; retain the dated fixture and displayed rounding.

### W6-UAT-8-02

**Mapping:** AC1 ongoing decline  
**Method:** Manual browser / semi-automated fixture setup  
**Status:** Not executed

**Preconditions:** Same setup, replacing the final sequence after the 20 baseline observations.

**Inputs:** Subsequent values: 100, 120, 90.

**Steps:** 1. Analyze. 2. Inspect current drawdown and the deepest episode. 3. Check its recovery field.

**Expected result:** Current and maximum drawdown are −25%. The decline remains ongoing/unrecovered; no future recovery date or completed recovery duration is invented.

**Postconditions:** Record the unrecovered episode without altering history.

### W6-UNIT-8

**Method:** Automated pytest or Vitest  
**Status:** Planned regression group; not newly executed for this specification.

test_drawdown.py: running rather than future peak, maximum/current decline, recovered and ongoing episodes, shallow moves, limits and date/value length mismatches.

### W6-SYS-8

**Method:** Automated API/component regression plus specified browser integration verification  
**Status:** Planned regression group; not newly executed for this specification.

test_api.py and App.test.tsx: portfolio history becomes drawdown metrics and correctly labeled episodes. Compare an independent value-series calculation with the displayed chart and API.

## US-10 Risk dashboard

FR-12 · 5 points · [Issue #10](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/10) · [Implementation 23ca50b](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/23ca50b) · [PR #59](https://github.com/lam-andrew/portfolio-risk-intelligence/pull/59)

- AC1: Opening an analyzed portfolio’s dashboard presents risk metrics with supporting visualizations.

### W6-UAT-10-01

**Mapping:** AC1 analyzed portfolio  
**Method:** Manual browser / semi-automated fixture setup  
**Status:** Not executed

**Preconditions:** Signed-in account with four holdings and sufficient cached history; record the assessed commit and analysis response.

**Inputs:** The same completed analysis response supplies every displayed metric.

**Steps:** 1. Open the dashboard. 2. Compare headline values with the response. 3. Inspect supporting charts and risk views. 4. Use keyboard navigation and repeat at desktop and narrow viewport widths.

**Expected result:** Metrics and chart values agree with the response and show meaningful labels/units. Key figures remain readable; navigation works without a pointer; chart values are available through labels or equivalent text.

**Postconditions:** No holdings change; save viewport sizes, screenshots and response comparison.

### W6-UAT-10-02

**Mapping:** AC1 boundary and resilience  
**Method:** Manual browser / semi-automated fixture setup  
**Status:** Not executed

**Preconditions:** Use a fresh empty account, then a populated fixture whose analysis request is forced to fail in the test harness.

**Inputs:** Empty holdings; controlled analysis error.

**Steps:** 1. Open each state. 2. Observe guidance/loading/error messaging. 3. Restore the response and retry.

**Expected result:** Empty state explains how to add holdings. Failure shows a useful error without fabricated or mismatched metrics. Retrying the recovered request displays the correct results.

**Postconditions:** The account’s holdings remain available; clear the injected test failure.

### W6-UNIT-10

**Method:** Automated pytest or Vitest  
**Status:** Planned regression group; not newly executed for this specification.

App.test.tsx and risk-feature component tests: metric formatting, loading/empty/error state, navigation and chart interactions. Existing Vitest tests supply the regression baseline.

### W6-SYS-10

**Method:** Automated API/component regression plus specified browser integration verification  
**Status:** Planned regression group; not newly executed for this specification.

Authenticated browser → /api risk analysis → summary/history/exposure/correlation/drawdown views. Run the current main baseline first; repeat affected procedures on PR #94 before merge.

## US-19 Risk methodology companion

FR-12 support · 2 points · [Issue #62](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/62) · [Implementation 9794b55](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/9794b55) · [PR #63](https://github.com/lam-andrew/portfolio-risk-intelligence/pull/63)

- AC1: Explain volatility, correlation, concentration and drawdown in plain language with formulas.
- AC2: Use the analyzed portfolio’s own figures as examples. AC3: Link each metric to its explanation. AC4: State known limitations plainly.

### W6-UAT-19-01

**Mapping:** AC1 and AC4  
**Method:** Manual browser / semi-automated fixture setup  
**Status:** Not executed

**Preconditions:** Authenticated user can open Methodology; no personal analysis is required.

**Inputs:** Sections for volatility, correlation, concentration and drawdown.

**Steps:** 1. Open each section. 2. Read its explanation and formula. 3. Compare with ADR 0012 and the relevant engine. 4. Read assumptions and limitations.

**Expected result:** Each metric has a plain-language explanation and the matching formula. Historical estimates, data sufficiency, fixed holdings and correlation-based overlap limitations are plainly stated where relevant.

**Postconditions:** Reading creates no portfolio change and makes no prediction or recommendation.

### W6-UAT-19-02

**Mapping:** AC2 and AC3  
**Method:** Manual browser / semi-automated fixture setup  
**Status:** Not executed

**Preconditions:** Analyzed disposable portfolio; save its response. Repeat with an account without an analysis.

**Inputs:** Current portfolio figures and each available metric explanation link.

**Steps:** 1. Follow each metric’s explanation link. 2. Verify the destination section. 3. Compare worked examples with the saved response. 4. Repeat without analysis.

**Expected result:** Links reach the relevant explanation. Worked examples use that portfolio’s figures; without analysis, guidance replaces personalized results and no other account’s figures appear.

**Postconditions:** Navigation leaves holdings unchanged; retain link destinations and comparison evidence.

### W6-UNIT-19

**Method:** Automated pytest or Vitest  
**Status:** Planned regression group; not newly executed for this specification.

MethodologyPage.test.tsx: metric sections/formulas, personalized examples, no-analysis behavior, limitations and anchors.

### W6-SYS-19

**Method:** Automated API/component regression plus specified browser integration verification  
**Status:** Planned regression group; not newly executed for this specification.

App.test.tsx plus browser navigation from dashboard metric links to the methodology page. Check API-supplied examples against the same analysis used on the dashboard.

## Result record template

For each procedure record: test ID; requirement/AC; date; commit; environment/fixture; expected result; actual result; Passed/Failed/Blocked/Not executed; evidence URL; defect and corrective action. Use the original Sprint 1 procedures for carryover rather than inventing replacement results.
