# Sprint 3 acceptance and regression specifications

Created October 20, 2026. Owner: Andrew Lam. Existing test IDs and historical results remain intact. W9 IDs are final-build execution plans, not new executable tests.

## 7 Test strategy and current results

The SAC uses pure numerical unit tests, API/persistence integration tests and browser UAT. SEC and model-dependent paths also need native PostgreSQL checks and real-provider evaluation. Controlled fixtures establish reproducibility; they do not establish real service availability or model answer quality.

| October 20 execution | Result | Scope |
| --- | --- | --- |
| Five backend risk files | 99 passed; 0 failed; 0 skipped | Volatility, correlation, concentration, drawdown and stress. Python 3.12 container; SQLite/API fixtures where applicable; no external network. |
| Coverage | Not measured in this run | No new Week 9 coverage percentage is claimed. |
| Warning | 1 tooling deprecation | Existing Starlette TestClient/httpx warning; did not fail execution. |

Reproduction: from backend, run pytest tests/test_volatility.py tests/test_correlation.py tests/test_concentration.py tests/test_drawdown.py tests/test_stress.py. Assessed application revision: e123023. The retained JUnit/log files record 99 passing tests in 4.66 seconds. No application source or user holdings changed during the run.

### SAC verification mapping

| Requirement and story | Test evidence and expected behavior | Week 9 result |
| --- | --- | --- |
| FR-7 / US-5 | Volatility matches independent sample/covariance calculations; 19 returns yield unavailable; equal-weight uncorrelated series reduce risk. | Passed within 99 |
| FR-8 / US-6 | Correlation is symmetric, bounded and agrees with NumPy; constant series produce null rather than measured zero. | Passed within 99 |
| FR-9 / US-7 | HHI/effective count match known weights; overlap members must meet the threshold with every existing member. | Passed within 99 |
| FR-10 / US-8 | Running-peak drawdown preserves dates, distinguishes recovered and ongoing episodes and ignores future peaks. | Passed within 99 |
| FR-11 / US-9 | Known shocks, cent rounding, missing prices, same-date valuation, cache reuse and account isolation. | Passed within 99 |

[volatility](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/e123023d48daa67516f1e31e5d8e12d80eb510f8/backend/tests/test_volatility.py) · [correlation](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/e123023d48daa67516f1e31e5d8e12d80eb510f8/backend/tests/test_correlation.py) · [concentration](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/e123023d48daa67516f1e31e5d8e12d80eb510f8/backend/tests/test_concentration.py) · [drawdown](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/e123023d48daa67516f1e31e5d8e12d80eb510f8/backend/tests/test_drawdown.py) · [stress](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/e123023d48daa67516f1e31e5d8e12d80eb510f8/backend/tests/test_stress.py)

### Prior evidence and remaining tests

The October 13 full assessment run reported 464 unique automated passes and measured backend statement coverage of 91.12% and frontend line coverage of 85.84%. Those are prior Week 8 results, not a new run on this documentation branch. The October 10 browser acceptance record also remains historical; final integrated-build UAT is planned below.

For every new execution, record the revision, tester, date, inputs, actual/expected outputs, method, result and defect link. Mark a provider or environment problem Blocked, an unattempted procedure Not executed, and a mismatched expected result Failed. Do not substitute a fixture pass for a live acceptance pass.

[Prior acceptance and defects](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/e123023d48daa67516f1e31e5d8e12d80eb510f8/docs/core-acceptance-2026-10-10.md) · [Atlas checks](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/e123023d48daa67516f1e31e5d8e12d80eb510f8/docs/atlas-verification-2026-10-10.md) · [Sprint 3 test specification](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/codex/sprint3-planning/docs/sprint3-tests.md)


## 8 US 9 Stress testing acceptance specification

FR-11 · Must · 8 points · In Progress. Acceptance criterion: given an analyzed portfolio, selecting an adverse scenario estimates and displays its impact. Existing refinement: scenarios are uniform 10%, 20% and 35% price declines, with no probability or time horizon; results use a complete same-date baseline and do not alter holdings.

### W9 UAT 9 01 Scenario results and changed holdings

FR-11 → US-9 → ST-09 | Manual UAT / normal full stack | Not executed this week

Preconditions and inputs: Disposable signed-in account on the selected release; configured market provider; two priced holdings. Record quantities, shared pricing date and adjusted prices.

Execution: Run each scenario. Compute each rounded position baseline and loss independently; compare rows and totals. Edit one quantity through Holdings and run again. Use keyboard controls and inspect desktop/mobile.

Expected result and postconditions: Baseline, total loss, remainder and contributions reconcile to cents; date and hypothetical limitations are visible. Changed quantity is reflected. Scenario execution itself changes no holding.

### W9 UAT 9 02 Unavailable prices and stale requests

FR-11 → US-9 → ST-05 / ST-07 | Controlled system / UAT | Not executed on final build

Preconditions and inputs: Separate QA stack with one missing ticker price, then a complete two-position fixture. Delay one response.

Execution: Run with missing prices; restore data and retry. Start one scenario, switch to another before it finishes, then release the old response.

Expected result and postconditions: Missing prices produce unavailable status and null totals, not partial loss. Retry recovers; old responses cannot overwrite the selected scenario. Holdings remain unchanged.

### Planned unit and automated system coverage

Retain ST-01–ST-06 in test_stress.py and frontend ST-07 in StressTestPage.test.tsx. The backend subset passed in the fresh 99-test run; frontend and live UAT were not rerun. ST-01 uses $1,000 and $500 with a 20% decline: losses $200/$100, total $300, remainder $1,200. ST-02 checks half-up rounding and zero/100% bounds. ST-04 checks fractional quantities and the latest common date.

[Issue #9](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/9) · [Full ST specifications](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/e123023d48daa67516f1e31e5d8e12d80eb510f8/docs/us9-stress-tests.md) · [Stress engine](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/e123023d48daa67516f1e31e5d8e12d80eb510f8/backend/app/engines/risk/stress.py) · [ADR 0018](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/e123023d48daa67516f1e31e5d8e12d80eb510f8/docs/adr/0018-hypothetical-portfolio-stress-tests.md)


## 9 US 11 Filing ingestion acceptance specification

FR-13 · Should · 5 points · In Progress. Acceptance criterion: for a public filer, ingestion retrieves and indexes supported 10-K, 10-Q and 8-K filings. Coverage is bounded to the latest annual report, latest quarterly report and up to five recent current reports. Unsupported issuers and missing forms must be explained, not treated as complete coverage.

### W9 UAT 11 01 Real source and extracted passage

FR-13 → US-11 → FI-08 | Manual UAT / real SEC source | Not executed this week

Preconditions and inputs: Normal PostgreSQL stack; configured SEC identifying contact; disposable account holding AAPL; worker available.

Execution: Observe retrieval to terminal status. Compare issuer, form, accession and date to the SEC source. Search a phrase and open the returned source passage. Test an unsupported holding separately.

Expected result and postconditions: Stored and displayed text match the selected source after documented normalization; source metadata and progress are accurate. Unsupported status explains the limitation. Public cache remains; no portfolio mutation.

### W9 UAT 11 02 Restart and duplicate prevention

FR-13 → US-11 → FI-03 / FI-08 | Semi-automated full-system acceptance | Not executed this week

Preconditions and inputs: Disposable database and normal worker; selected issuer has a queued multi-document job; retained public SEC cache allowed.

Execution: Interrupt only the worker during ingestion; restart it. Observe resumption and final document count. Refresh after cooldown and compare accessions and passage counts.

Expected result and postconditions: Persisted work resumes without duplicate filings/passages. Partial failures remain visible and retryable. A second account without current membership cannot read the protected view. Remove only test account data afterward.

### Planned unit and automated system coverage

Retain FI-01–FI-07: parsing/offset tests, authenticated job/search APIs, retry/lease handling, ownership, mocked SEC network boundaries, native PostgreSQL indexes/locking and frontend progress/error states. Run test_filings.py and test_filings_postgres.py plus FilingsPage tests on the integrated revision. FI-08 previously indexed seven real AAPL filings and 255 passages on September 19; manual rendered-source comparison and live interruption remain open.

[Issue #11](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/11) · [Full FI specifications](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/e123023d48daa67516f1e31e5d8e12d80eb510f8/docs/us11-filing-tests.md) · [Ingestion source](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/e123023d48daa67516f1e31e5d8e12d80eb510f8/backend/app/data/filing_ingestion.py) · [Filings tests](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/e123023d48daa67516f1e31e5d8e12d80eb510f8/backend/tests/test_filings.py)


## 10 US 12 Grounded question acceptance specification

FR-14 · Should · 8 points · In Progress. Acceptance criteria: supported answers cite specific filing passages; unsupported questions abstain. The approved Atlas workflow adds Holding → specific filing → Ask about this filing, with bounded follow-ups, server-enforced filing scope, source navigation and full-screen mobile chat. The model must not broaden evidence to another filing.

### W9 UAT 12 01 Scoped answer follow up and citation

FR-14 → US-12 → QA-01 / ADR 0027 | Manual UAT / selected real filing | Not executed; live evaluation pending

Preconditions and inputs: Reviewed filing-chat build; account has access to two filings from one issuer; selected filing is prepared; generation quota available. Choose a question with known evidence only in the selected filing.

Execution: Ask, follow up using a pronoun, and open every citation. Switch filings and repeat. Inspect desktop side chat and mobile full-screen chat.

Expected result and postconditions: Answers cite exact passages from the selected filing; navigation reaches that passage. Follow-up context is bounded and does not cross filing/user boundaries. Switching clears inappropriate context; holdings remain unchanged.

### W9 UAT 12 02 Abstention provider error and isolation

FR-14 / FR-15 → US-12 → QA-02–04 | Controlled system plus live UAT | Not executed on final build

Preconditions and inputs: Prepared disposable corpus; unsupported question, invented citation fixture, revoked membership and quota/outage fixtures.

Execution: Submit each case; separately run unsupported and hostile questions in the labeled real evaluation. Retry only when service status permits.

Expected result and postconditions: No unsupported claim or invalid citation reaches the user. Auth/membership failures deny access. Quota/outage errors remain distinct from insufficient evidence. No credentials or private conversation content enters logs or Git.

### Planned automation and live quality gate

Retain QA-01–QA-08 and the filing-scope/context regressions in test_questions.py. Run provider and grounding unit tests, native PostgreSQL retrieval/budget tests and reader/chat component tests. The separate local-embedding branch also needs version/migration and worker recovery checks; local embeddings do not remove hosted generation quotas.

Use the existing 20-case labeled evaluation: at least 90% recall@8 and supported-claim precision on applicable answerable cases, 100% valid provenance, and 100% abstention on labeled unsupported/advice/injection cases. Record numerators, denominators, latency and model/index versions. All gates must pass; a small evaluation is not a universal quality guarantee.

[Issue #12](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/12) · [QA specifications](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/e123023d48daa67516f1e31e5d8e12d80eb510f8/docs/us12-question-tests.md) · [Live evaluation](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/e123023d48daa67516f1e31e5d8e12d80eb510f8/docs/us12-live-evaluation.md) · [Scope decision](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/e123023d48daa67516f1e31e5d8e12d80eb510f8/docs/adr/0027-filing-scoped-conversation.md) · [PR #98 local embeddings](https://github.com/lam-andrew/portfolio-risk-intelligence/pull/98)


## 11 Carryover acceptance for portfolio inputs and metrics

These compact rerun specifications supplement the existing W6 UAT and W7 unit/system specifications. Their IDs and historical passes remain intact. All W9 final-build reruns below are Not executed; they do not claim new acceptance merely because related unit tests passed.

### W9 C 13 Authentication

FR-15 → US-13 → W6-UAT-13-01/02 | Manual UAT with automated auth/API regression | Not executed

Preconditions and inputs: Two disposable accounts; account A has a holding, B is empty.

Execution: Log in as A, reload, sign out, then try an incorrect password. Log in as B and request A’s holding identifier.

Expected result and postconditions: Valid login persists until logout; invalid credentials receive a clear generic error; B cannot access A’s holdings. Log out and delete only the temporary data.

### W9 C 2 CSV import and row validation

FR-2 / FR-3 → US-2 → W6-UAT-2-01/02 | Manual UAT with parser/API regression | Not executed

Preconditions and inputs: Empty QA account and recognized fixture symbols; CSV rows AAPL 10, MSFT 2.5, INVALID! 4 and AAPL -1.

Execution: Upload, inspect row results, reload; then upload AAPL 12.

Expected result and postconditions: Valid positions persist with exact quantities; invalid rows identify errors and do not create holdings. Matching AAPL updates to 12; unrelated MSFT remains. Clean up the QA portfolio.

### W9 C 6 Correlation matrix

FR-8 → US-6 → W6-UAT-6-01/02 | Controlled system / UAT; numerical unit regression | Not executed

Preconditions and inputs: QA prices with 21+ shared dates: identical A/B returns, inverse C returns and flat D prices.

Execution: Open correlation, compare cells to API, select pairs and use keyboard interaction. Repeat with 18 and 50 fixture holdings at desktop/mobile widths.

Expected result and postconditions: Identical/inverse pairs show +1/-1, zero variance shows unavailable, matrix is symmetric; all holdings remain reachable without page overflow. Portfolio data stays unchanged.

[Original UAT specifications](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/codex/sprint2-planning/docs/sprint2-tests.md) · [Original unit/system specifications](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/codex/sprint2-planning/docs/sprint2-unit-system-tests.md) · [Acceptance history](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/e123023d48daa67516f1e31e5d8e12d80eb510f8/docs/core-acceptance-2026-10-10.md)


## 12 Carryover acceptance for interpretation and navigation

### W9 C 7 Concentration and overlap

FR-9 → US-7 → W6-UAT-7-01/02 | Controlled system / UAT; numerical unit regression | Not executed

Preconditions and inputs: Four priced positions with weights 55%, 20%, 15%, 10%; a separate valid return fixture with an 80% all-member correlated group.

Execution: Inspect weights, HHI, effective count and overweight marker; load the overlap fixture and compare group weight to API.

Expected result and postconditions: HHI is 0.375; effective holdings approximately 2.67; 55% exceeds the 50% overweight threshold. Group shows 80% with correlation-based limitations, not ETF look-through. Inputs unchanged.

### W9 C 8 Drawdown episodes

FR-10 → US-8 → W6-UAT-8-01/02 | Controlled system / UAT; numerical unit regression | Not executed

Preconditions and inputs: Known portfolio values [100,120,90,72,120], then [100,120,90], with ordered dates.

Execution: Inspect chart, maximum/current decline and recovery; then use the ongoing series and an unavailable response.

Expected result and postconditions: First series shows -40% maximum, 0% current and recovery at final date; second shows -25% current and no recovery. Missing data never says recovered. Holdings unchanged.

### W9 C 10 Dashboard states

FR-12 → US-10 → W6-UAT-10-01/02 | Controlled full-system UAT; component regression | Not executed

Preconditions and inputs: Populated QA portfolio; controllable success, empty, partial and failed API responses.

Execution: Compare tiles/charts to API; trigger each state and retry; inspect dark/light at desktop and narrow widths with keyboard navigation.

Expected result and postconditions: Units and values agree; unknown is not zero; failed and empty states differ; retry restores results; navigation and chart labels remain usable. Restore normal fixture.

### W9 C 19 Methodology

FR-12 → US-19 / #62 → W6-UAT-19-01/02 | Manual UAT; component and API regression | Not executed

Preconditions and inputs: Analyzed QA portfolio plus an empty-account variant.

Execution: Follow each of four metric explanation links; compare formulas and personal examples to APIs; open with unavailable results.

Expected result and postconditions: Correct section opens, formulas match ADR 0012, limitations are visible and unavailable values are not invented. Navigation changes no portfolio data.

[Original detailed test specifications](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/codex/sprint2-planning/docs/sprint2-unit-system-tests.md) · [Methodology issue #62](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/62)


## Regression execution record

October 20: Python 3.12 container, source e123023d48daa67516f1e31e5d8e12d80eb510f8. `pytest tests/test_volatility.py tests/test_correlation.py tests/test_concentration.py tests/test_drawdown.py tests/test_stress.py --junitxml=/tmp/orbit-week9-risk.xml`: **99 passed, zero failed/skipped**, 4.66 seconds. One existing Starlette/httpx deprecation warning. Pure numerical tests and authenticated SQLite/provider-fake API tests; no live market/SEC/model calls. No fresh coverage, frontend suite, native PostgreSQL run or final-build UAT is claimed.

[Sanitized execution summary](evidence/sprint3-planning/risk-regression.json); full JUnit/logs retained with local verification artifacts. Unit outputs match the assertions in the linked test files; later integrated-build results must be recorded separately.

## Current review check finding

October 20, 2026: PR #104's frontend production dependency audit failed on
`follow-redirects` 1.16.0, reporting one high-severity vulnerable dependency and
advisories GHSA-q3jh-wrc6-jgq8 and GHSA-8r9p-f939-6h3c. The audit output reports a
fix is available. [Failed audit evidence](https://github.com/lam-andrew/portfolio-risk-intelligence/actions/runs/39546688571/job/119046337108).

This documentation change does not modify application dependencies. Review and
update the dependency in a focused maintenance change, rerun the audit and
applicable regression/build checks, then reassess merge readiness. The earlier
successful PR #103 checks remain historical evidence and do not override this
new finding. No merge or deployed exploitability conclusion is claimed.
