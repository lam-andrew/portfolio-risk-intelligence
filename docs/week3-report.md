# Orbit | Week 3 Progress Report I

**Andrew Lam | Group 5**  

**SWENG 894 Capstone Experience | Penn State World Campus**  

**Instructor: Dr. Raghu Sangwan**

Sprint 1: Weeks 3-5, September 7-27, 2026. Reporting period: September 7-8, 2026. Evidence cutoff: September 8, 2026, Pacific time. Assignment due: September 13, 2026, at 11:59 p.m., as displayed in Canvas.

## 1. Executive summary

Orbit measures and explains portfolio risk through a quantitative Risk & Exposure engine, with evidence-grounded SEC filing research planned as a secondary capability. It does not predict prices, execute trades, or provide personalized investment advice.

The Sprint 1 goal remains a running, containerized application that accepts holdings, retrieves historical market data, and displays holding and portfolio volatility: a thin end-to-end slice through the architecture. The six highest-priority foundation stories remain unchanged at **20 story points**.

Implementation progressed ahead of the course calendar. The foundation and Sprint 1 feature commits were created primarily on August 28-30, and all six issues were closed on August 30 Pacific time (August 31 UTC). This report treats that work as the entering baseline, not as development newly completed during Week 3. The GitHub board's Done status is reported as an observed project-management state, not substituted for documented user acceptance.

This week's work reconciled the submitted Week 2 plan with the board and repository, refined story-specific completion checklists, documented initial test specifications for every Sprint 1 requirement, and reran the existing regression suites. **183 backend and 53 frontend tests passed** on September 8. These 236 tests cover the repository as a whole, including early later-sprint work; they are not 236 new Sprint 1 tests.

Eighteen initial test specifications and their requirement mappings appear in Sections 7-12. Browser UAT, an engine-extension demonstration, and final acceptance sign-off remain pending. No new functional story, point estimate, or sprint assignment was introduced for this report. Continuous deployment remains deferred under ADR 0008; successful CI is not a claim of production deployment.

## Report navigation

- Section 2: groomed product backlog and estimation.
- Section 3: Sprint 1 priorities and Definition of Done.
- Sections 4-5: contributions, commit evidence, and burndown.
- Section 6: test strategy, results, and limitations.
- Sections 7-12: acceptance criteria, story tasks, and mapped test specifications.

## Project records

[Repository](https://github.com/lam-andrew/portfolio-risk-intelligence) | [GitHub Project board](https://github.com/users/lam-andrew/projects/2/views/1) | [Week 3 assessment](https://psu.instructure.com/courses/2480621/assignments/18300598) | [Architecture and ADRs](https://github.com/lam-andrew/portfolio-risk-intelligence/tree/c065aef/docs/adr)

The submitted Week 2 report, dated September 2, is retained unchanged. This is an early Week 3 snapshot; September 9-13 activity is not represented as completed.

<!-- pagebreak -->

## 2. Groomed product backlog

Fibonacci points express relative effort and uncertainty, not hours. US-1 anchors a small full-stack change at two points. Priorities retain the Week 2 MoSCoW definitions: Must for foundational/core capability, Should for valuable secondary or convenience capability, and Could for uncommitted stretch. Dependencies determine execution order within priority classes.

| Story | Requirement / capability | Priority | Sprint | Points |
|---|---|---|---|---|
| US-14 | AR-1: containerized deployment skeleton | Must | 1 | 5 |
| US-15 | AR-2: decoupled analysis API | Must | 1 | 3 |
| US-1 | FR-1: manual holding entry | Must | 1 | 2 |
| US-3 | FR-4: view, edit, delete holdings | Must | 1 | 2 |
| US-4 | FR-5, FR-6: retrieve and cache prices | Must | 1 | 5 |
| US-5 | FR-7: holding and portfolio volatility | Must | 1 | 3 |
| US-2 | FR-2, FR-3: CSV import and validation | Should | 2 | 3 |
| US-13 | FR-15: authentication | Must | 2 | 3 |
| US-7 | FR-9: concentration and exposure | Must | 2 | 3 |
| US-8 | FR-10: historical drawdown | Must | 2 | 2 |
| US-6 | FR-8: correlation | Must | 2 | 5 |
| US-10 | FR-12: risk dashboard | Must | 2 | 5 |
| US-9 | FR-11: scenario stress testing | Must | 3 | 8 |
| US-11 | FR-13: SEC filing ingestion | Should | 3 | 5 |
| US-12 | FR-14: grounded Q&A | Should | 3 | 8 |
| US-16-18 | Regimes, anomalies, brokerage connection | Could | Backlog | Unestimated |

**Estimated baseline: Sprint 1 = 20; Sprint 2 = 21; Sprint 3 = 21; total = 62 points.** Sprint 4 remains stretch or hardening, with no committed point total.

### Grooming decisions and rationale

No Sprint 1 scope, priority, estimate, or assignment changed this week. The README's Sprint 2 subtotal is corrected from 18 to 21 because its existing estimates sum to 3 + 3 + 3 + 2 + 5 + 5. The corresponding baseline total is 62. This is an arithmetic correction, not a re-estimation; the original Week 2 submission is not rewritten.

The issue inventory also includes [US-19 / issue #62](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/62), a core methodology explanation supporting FR-12 with Sprint 2 stated in its body but no point estimate, and [idea #49](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/49), an unestimated pre-trade research/portfolio-fit assistant. They are outside the 62-point estimated baseline and outside Sprint 1. Their presence is disclosed, not treated as a new Week 3 addition. US-19 still needs estimation in future grooming.

The Orbi mascot remains a saved design prototype, not Sprint 1 application functionality. Neither it nor broader research-agent work is pulled into this sprint. Stress testing and SEC/RAG remain later work; early implementation of other stories does not change their scheduled sprint.

Sources: submitted Week 2 report, [SRS story inventory](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/c065aef/docs/SRS.md), and live [issues](https://github.com/lam-andrew/portfolio-risk-intelligence/issues?q=is%3Aissue), inspected September 8.

<!-- pagebreak -->

## 3. Sprint planning and Definition of Done

Dependency order is US-14 -> US-15 -> US-1 -> US-3 -> US-4 -> US-5. Containers establish a reproducible workspace; the API boundary protects the core; holding entry and management establish persistent inputs; data retrieval supplies prices; volatility supplies the first end-to-end risk result. All six are Must priority. Owner for all development and report tasks: Andrew Lam.

| Story | Points | Observed issue / board | Current acceptance evidence |
|---|---|---|---|
| US-14 | 5 | Closed / Done | CI boot and database probe pass; browser-to-stack check pending |
| US-15 | 3 | Closed / Done | API tests and import review support isolation; extension exercise pending |
| US-1 | 2 | Closed / Done | API and component tests pass; recorded browser UAT pending |
| US-3 | 2 | Closed / Done | Persistence and confirmation tests pass; analysis-after-edit/delete UAT pending |
| US-4 | 5 | Closed / Done | Retrieval/cache tests pass with fake provider; recorded live-provider UAT pending |
| US-5 | 3 | Closed / Done | Math and risk API tests pass; recorded dashboard UAT pending |

The board was inspected on September 8 and already matched these six Sprint 1 stories. No board items were moved in preparing this report. Closed issues alone do not establish that every acceptance task below has been satisfied.

### Common Definition of Done, applied to every story

1. Acceptance criteria match the authoritative issue and map to identifiable test cases.
2. Applicable interaction/UI design, API/engine design, persistence, and implementation tasks are complete. Non-applicable work is explicitly identified.
3. Unit and API/system tests cover successful behavior and relevant failure paths. Actual results and limitations are recorded against a source revision.
4. The relevant UAT or developer acceptance procedure has been executed, its evidence retained, and blocking failures resolved. Specification alone is not a pass.
5. Living documentation and any architecturally required ADR are current; implementation and test commits are linked.
6. The change has received diff review, applicable CI/security gates have passed, and integration occurs through a GitHub PR. No direct commit or push to main.
7. No unresolved defect blocks the story's acceptance criteria, and the acceptance decision is recorded.

Story-specific implementation and remaining evidence tasks are defined in Sections 7-12. Existing code and automated tests are distinguished there from acceptance work still to execute. No blanket claim of full DoD completion is made.

### Remaining acceptance work

The six pending acceptance procedures are TC-14-01, TC-15-03, TC-1-03, TC-3-03, TC-4-03, and TC-5-03. Execute them during Sprint 1 in an isolated test environment, record date, revision, screenshots or sanitized responses, actual result, and defect links, then reassess DoD. Review and sign off the six stories individually before sprint closeout. These are evidence tasks for existing scope, not six new pointed stories.

Production CD is not a hidden completion claim: [ADR 0008](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/c065aef/docs/adr/0008-defer-continuous-deployment.md) defines the locally deployable Sprint 1 boundary. A new hosted deployment decision and pipeline remain separate future work.

<!-- pagebreak -->

## 4. Source code development and contributions

The [repository](https://github.com/lam-andrew/portfolio-risk-intelligence) and [project board](https://github.com/users/lam-andrew/projects/2/views/1) connect requirements to issues, and implementation PRs reference the corresponding stories. Andrew Lam is the solo project contributor responsible for the sprint. Dates below use Pacific time for consistency with the local development record.

### Entering baseline: historical implementation, not Week 3 throughput

| Date | Commit / review record | Story contribution |
|---|---|---|
| Aug 28 | [c2125f6](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/c2125f6), [PR #19](https://github.com/lam-andrew/portfolio-risk-intelligence/pull/19) | US-14/15: FastAPI, React, PostgreSQL/pgvector skeleton; Compose and API boundary |
| Aug 28 | [4b54392](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/4b54392) | US-14: lint, types, test/security gates; explicit deferred-CD decision |
| Aug 30 | [e7546a2](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/e7546a2), [3c550e8](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/3c550e8) | US-1: API persistence/validation and entry UI, PRs #50/#52 |
| Aug 30 | [09cc471](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/09cc471) | US-3: quantity edits and confirmed deletion, PR #53 |
| Aug 30 | [84444a6](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/84444a6), [5ae65cb](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/5ae65cb) | US-4: provider selection and retrieval/cache implementation, PRs #54/#55 |
| Aug 30 | [1b23564](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/1b23564) | US-5: volatility math, API, presentation, and tests, PR #56 |
| Aug 31 | [53c0189](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/53c0189) | US-4: concurrent-fetch/cache regression hardening, PR #69 |
| Sep 5 | [24d39ef](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/24d39ef) | US-14/15: namespace API under /api; update probes and tests, PR #79 |

### Week 3 contributions through September 8

- September 7: [92a3d84](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/92a3d84) assembled the Sprint 1 backlog/DoD working document; [811222a](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/811222a) refreshed the testing record. This report refines their evidence wording and removes unsupported completion implications.
- September 8: [PR #80](https://github.com/lam-andrew/portfolio-risk-intelligence/pull/80), merged as [c065aef](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/c065aef), added root AGENTS.md instructions. Its diff was reviewed and all reported CI, integration, and security checks passed before GitHub merge.
- September 8: existing regression suites were rerun; [6e643ff](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/6e643ff) assembles this report's 18 initial test specifications and DoD in [PR #81](https://github.com/lam-andrew/portfolio-risk-intelligence/pull/81). The user guide is also refined for holding management. No new application functionality or automated test code was added for this assessment.

**Process exception and correction.** The September 7 documentation changes reached main without the required PR workflow. That is recorded as a process deviation, not retroactively described as reviewed. PR #80 makes the workflow explicit for agents; this assessment's source is maintained on a separate documentation branch for PR review.

**Spike guidance.** Environment setup and investigation of containers, CI/security, market-data providers, and risk methodology were performed early and recorded in ADRs 0003, 0007, 0008, 0011, and 0012. They are not relabeled as new Week 3 spike stories or given invented effort/timebox values.

<!-- pagebreak -->

## 5. Burndown and remaining work

### Sprint 1 issue-status burndown

The plotted measure is the sum of original Sprint 1 points on issues still open, reconstructed from the six issues' current closedAt timestamps. It measures recorded issue closure, not independently verified acceptance or developer hours. All six issues were already closed before September 7, so issue-status work remaining is zero at sprint entry and at this report's September 8 checkpoint. Future observations are deliberately absent.

<!-- burndown -->

**Figure 1.** Original planned scope: 20 points. Dashed reference: hypothetical linear burn of that original scope from September 7 to September 27; it is not an actual or revised forecast. Solid observed line: 0 open-issue points at September 7 and September 8 only. Gray region: dates after the evidence cutoff; no actual completion values are asserted there. A flat zero line does not mean acceptance work is finished, nor does it establish 20 points of Week 3 velocity.

### Audit trail behind the observed baseline

| Issue | Points | GitHub closedAt (UTC, August 31, 2026) |
|---|---|---|
| US-14 / #14 | 5 | 04:34:50 |
| US-15 / #15 | 3 | 04:34:54 |
| US-1 / #1 | 2 | 04:38:04 |
| US-3 / #3 | 2 | 04:38:11 |
| US-4 / #4 | 5 | 04:38:12 |
| US-5 / #5 | 3 | 05:00:43 |

All timestamps above fall on August 30 in Pacific time. Source: live GitHub issue records inspected September 8; the current board also shows all six in Done. This reconstruction uses latest closure timestamps, not a complete historical board event export.

### Acceptance work remaining at the cutoff

Six acceptance procedures remain to be executed and recorded: full-stack browser connectivity, engine extension, manual entry, management with reanalysis, live retrieval/cache behavior, and displayed volatility (Section 3). These procedures have no historical task-burn series yet; the first explicit evidence snapshot is six pending on September 8. Final per-story sign-off follows their review. Their counts are not added to or subtracted from story points.

The next report will update observations from actual activity and record acceptance outcomes. No artificial daily decreases, backdated UAT, or reassignment of Sprint 2 work is used to make the chart resemble a conventional first sprint.

<!-- pagebreak -->

## 6. Software testing: strategy and execution evidence

### Environments and reproducibility

Source under test: [c065aef](https://github.com/lam-andrew/portfolio-risk-intelligence/tree/c065aef). Local backend: Python 3.13 virtual environment, pytest, FastAPI TestClient, SQLite test databases, and the deterministic FakeProvider. Portfolio fixtures create a signed-in test user because the current application already includes authentication. Frontend: Vitest and React Testing Library with mocked API calls. Container CI uses the repository's Python 3.12 image. These environments are disclosed rather than assumed identical.

Backend execution: from backend, run `.venv/bin/pytest -q`. Frontend execution: from frontend, run `npm test -- --run`. On September 8, both exited successfully: 183 backend tests and 53 frontend tests, no failed tests. One backend Starlette/httpx TestClient deprecation warning was emitted; it did not fail execution. No coverage percentage was measured in this run.

[CI run 34183424793](https://github.com/lam-andrew/portfolio-risk-intelligence/actions/runs/34183424793), on PR #80's head a457ae4, passed backend lint/format/types/tests, frontend lint/format/types/tests/build, and Compose integration. Its code matches the application tested at c065aef; the PR adds agent guidance only. [Security](https://github.com/lam-andrew/portfolio-risk-intelligence/actions/runs/34183424779) and [CodeQL](https://github.com/lam-andrew/portfolio-risk-intelligence/actions/runs/34183424737) checks also passed. These are prior GitHub results inspected this week, not fresh local security scans.

### Evidence boundaries

- Unit tests validate risk math independently of HTTP, persistence, and the provider.
- API tests exercise actual routes, persistence, and cache services with a fake provider. They are component-integration tests, not full live-system UAT.
- Frontend tests use mocks; successful component assertions do not prove a browser communicates with the deployed backend.
- CI starts the Compose stack and asserts that /api/health reports a connected database. It does not explicitly test browser-to-API connectivity or a live Tiingo request.
- No manual UAT is claimed in this report. No new tests are claimed merely because existing tests were assigned reporting IDs. Automated failures observed this run: none; absence of blocking acceptance defects remains to be established through UAT.

### Incremental test specification and traceability

Sections 7-12 define three initial specifications per story, 18 total, with explicit requirement/acceptance mappings. Each includes setup or data, actions, expected outcomes, evidence location, and current result. All reporting IDs were created and last reviewed September 8, 2026. Existing automated tests retain their original source history; these IDs do not backdate their creation.

Source filenames and exact test names identify automation. Implementation/test origin commits are listed per story; the source links pin the reviewed version. API paths use the current /api namespace introduced by PR #79. For each future manual execution, record tester, date/time, source revision, actual results, sanitized evidence, and any defect issue. A pass requires every expected result; otherwise record failure or blockage, not partial acceptance.

### Next steps within the sprint

Execute the six pending procedures and address any demonstrated acceptance gap; expand specifications as work proceeds; retain test/implementation timestamps; measure and explain coverage for sprint closeout. Do not use genuine-looking financial holdings or credentials in published test evidence. Use an isolated test account and disposable data.

<!-- pagebreak -->

## 7. US-14 | Containerized deployment

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

**Traceability:** implementation/initial tests c2125f6 (PR #19); CI gates 4b54392; current probe/test-path update 24d39ef (PR #79). Report IDs created/reviewed September 8.

<!-- pagebreak -->

## 8. US-15 | Decoupled analysis API

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

**Traceability:** skeleton c2125f6 (PR #19), API contract ADR 0004, namespace and contract regression 24d39ef (PR #79). Report IDs created/reviewed September 8.

<!-- pagebreak -->

## 9. US-1 | Add a holding manually

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

**Traceability:** backend implementation and tests e7546a2 (PR #50); frontend and form tests 3c550e8 (PR #52); API paths updated in 24d39ef (PR #79). Report IDs created/reviewed September 8.

<!-- pagebreak -->

## 10. US-3 | Manage holdings

**FR-4 | Must | 2 points | Owner: Andrew Lam**  
[Authoritative issue #3](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/3)

### Acceptance criteria

AC3.1: Editing an existing holding's quantity saves the change and reflects it in analysis. AC3.2: Confirming deletion removes the holding and excludes it from further analysis.

### Story-specific DoD tasks and current evidence

- Provide view, inline edit/save/cancel, and delete-confirmation interaction: present in holding components; interaction tests pass.
- Persist changes through PATCH/DELETE and validate quantities/missing identifiers: implemented and covered by passing API tests.
- Document the interaction in the living user guide; retain implementation/test links: management instructions are refined in this Week 3 documentation change, with links below.
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

**Traceability:** implementation/API and interaction tests 09cc471 (PR #53); API paths updated 24d39ef (PR #79). [User guide update in PR #81](https://github.com/lam-andrew/portfolio-risk-intelligence/pull/81). Report IDs created/reviewed September 8.

<!-- pagebreak -->

## 11. US-4 | Retrieve and cache market data

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

**Traceability:** configuration 84444a6 (PR #54), retrieval/cache and tests 5ae65cb (PR #55), concurrency regression 53c0189 (PR #69), API paths 24d39ef. [ADR 0011](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/c065aef/docs/adr/0011-market-data-provider.md). Report IDs created/reviewed September 8.

<!-- pagebreak -->

## 12. US-5 | Holding and portfolio volatility

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

**Traceability:** implementation and initial math/API tests 1b23564 (PR #56); later dashboard integration 23ca50b (PR #59, Sprint 2 baseline, not Sprint 1 throughput); API paths 24d39ef. [ADR 0012](https://github.com/lam-andrew/portfolio-risk-intelligence/blob/c065aef/docs/adr/0012-risk-methodology.md). Report IDs created/reviewed September 8.
