# Sprint 1 Backlog and Definition of Done

**Status:** Week 3 working artifact  
**Sprint:** Sprint 1, Weeks 3-5  
**Sprint goal:** Deliver a running, containerized end-to-end slice that accepts a holding, retrieves real market data, and displays a portfolio risk metric.  
**Source plan:** Week 2 submission dated September 2, 2026  
**Total:** 20 story points

## Purpose

This document reconciles the submitted Week 2 plan, the current GitHub Project board,
the repository roadmap, and the implementation history. It is the working evidence
checklist for the Sprint 1 weekly reports. It does not rewrite the Week 2 submission
or change the historical dates of work completed before the academic sprint.

The six stories below are the authoritative Sprint 1 scope. The GitHub Project board
already places all six in its **Done** column (inspected September 8). No board items
were moved during this reconciliation. This is an observed status, not a substitute
for acceptance: the checklist below is a completion standard, not a claim all tasks
have passed. The [Week 3 report](week3-report.md), Sections 7-12, records per-story
implementation evidence, pending acceptance tasks, and 18 mapped test specifications.

## Reconciliation result

| Source | Result |
|---|---|
| Week 2 submission | Six Sprint 1 stories, 20 points, in dependency order |
| `README.md` and `docs/SRS.md` | Same six stories, same points, same sprint assignment |
| GitHub Project board | US-14, US-15, US-1, US-3, US-4, and US-5 in Done |
| Git history | Implementation commits exist for all six stories, mostly dated August 28-30 |
| Current conclusion | Sprint 1 scope is consistent; implementation was completed before Week 3, so reports must distinguish implementation date from academic sprint evidence date |

## Current evidence snapshot

- Backend suite: **183 tests passed** on September 8, 2026, at c065aef.
- Frontend suite: **53 tests passed** on September 8, 2026, at c065aef.
- Automated coverage includes the Sprint 1 functional paths and the AR-1/AR-2 checks
  documented in [the testing report](testing.md).
- Initial specifications, requirement mapping, creation/review dates, and issue-status
  burndown are assembled in the Week 3 report. Six acceptance procedures remain pending:
  TC-14-01, TC-15-03, TC-1-03, TC-3-03, TC-4-03, and TC-5-03.
- The local verification used the repository's deterministic test setup; it is not a
  substitute for demonstrating the running application in the Week 5 closeout.

## Sprint 1 backlog

| Order | Story | Requirement | Points | Board state | Implementation evidence |
|---:|---|---|---:|---|---|
| 1 | [US-14](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/14) Containerized deployment | AR-1 | 5 | Done | `c2125f6`, PR #19, CI workflow, Docker Compose files |
| 2 | [US-15](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/15) Decoupled analysis API | AR-2 | 3 | Done | `c2125f6`, PR #19, API and engine boundary |
| 3 | [US-1](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/1) Add a holding manually | FR-1 | 2 | Done | `e7546a2`, `3c550e8`, PR #50/#52 |
| 4 | [US-3](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/3) Manage holdings | FR-4 | 2 | Done | `09cc471`, PR #53 |
| 5 | [US-4](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/4) Retrieve and cache market data | FR-5, FR-6 | 5 | Done | `84444a6`, `5ae65cb`, PR #54/#55 |
| 6 | [US-5](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/5) See portfolio and holding volatility | FR-7 | 3 | Done | `1b23564`, PR #56 |
|  | **Sprint total** |  | **20** |  |  |

## Definition of Done

The following checklist applies to every Sprint 1 story. A checked implementation
item does not replace acceptance testing; both implementation and evidence must be
complete before the story is considered fully accepted for the sprint report.

### Required for every story

- [ ] Acceptance criteria are reviewed against the current implementation.
- [ ] The requirement and user story are linked in the traceability matrix.
- [ ] UI or interaction design is documented where the story has a user-facing flow.
- [ ] Backend, frontend, database, and integration tasks are complete as applicable.
- [ ] Unit tests cover the important logic and failure paths.
- [ ] System or API tests cover the delivered behavior across the relevant boundary.
- [ ] User Acceptance Testing scenarios are specified and executed.
- [ ] Test results, failures, bugs, and resolutions are recorded.
- [ ] The story's implementation commits and pull request are linked.
- [ ] Code quality, type checks, formatting, and security checks pass.
- [ ] Documentation affected by the story is updated.
- [ ] The change is reviewed and merged into `main`.
- [ ] No known blocking defect remains against the acceptance criteria.

### US-14 containerized deployment

- [ ] Docker Compose starts frontend, backend, and database together.
- [ ] Services communicate through the configured service boundaries.
- [ ] Health checks and non-root container behavior are verified.
- [ ] CI builds the same containerized stack and runs the required checks.
- [ ] The report records that continuous deployment is deferred under ADR 0008,
      rather than claiming production deployment is complete.
- [ ] A full-stack smoke test result is attached to the Week 5 evidence.

### US-15 decoupled analysis API

- [ ] Frontend analysis requests use the `/api` contract.
- [ ] Risk engines remain independent of frontend code and external I/O.
- [ ] A new engine can be registered behind the API boundary without changing the
      existing risk calculations.
- [ ] Static review confirms the engine/API separation.
- [ ] An API-level test proves the relevant request and response path.

### US-1 add a holding manually

- [ ] A valid ticker and positive share quantity can be submitted.
- [ ] The new holding is persisted and displayed.
- [ ] An invalid or unrecognized ticker produces a clear error.
- [ ] Invalid input does not create a holding.
- [ ] UAT covers a successful add and rejected input.

### US-3 manage holdings

- [ ] Existing holdings can be viewed.
- [ ] A changed quantity is persisted.
- [ ] Updated holdings are reflected in later analysis.
- [ ] Delete requires confirmation and removes the holding.
- [ ] Deleted holdings are excluded from later analysis.
- [ ] UAT covers edit persistence and delete behavior.

### US-4 retrieve and cache market data

- [ ] Valid holdings retrieve historical prices from the configured provider.
- [ ] Retrieved data is stored in the local cache.
- [ ] A repeat analysis within the cache policy avoids an unnecessary provider call.
- [ ] Provider failures and insufficient data produce controlled errors.
- [ ] Tests use a fake provider and do not depend on live rate limits.
- [ ] The actual provider choice and cache policy are documented in ADR 0011 and
      the testing report.

### US-5 portfolio and holding volatility

- [ ] Holding volatility is displayed when sufficient price history exists.
- [ ] Portfolio volatility is displayed for the analyzed portfolio.
- [ ] The calculation uses the documented return and annualization methodology.
- [ ] Insufficient-history behavior is tested and understandable to the user.
- [ ] UAT verifies the metric is visible in the risk dashboard.
- Metric-to-methodology navigation belongs to US-19; do not add it retroactively
  to US-5 acceptance criteria. Methodology documentation remains relevant to testing.

## Week 3 evidence inventory

The implementation evidence is already in the repository, but the Week 3 report
should assemble it into one coherent record:

- A dated board observation (recorded September 8 in the Week 3 report).
- The six-story backlog with points and dependency order.
- The DoD checklist above, showing current task status.
- A short explanation that implementation occurred before the academic Sprint 1
  window and is being reported as historical work.
- A list of recent commits mapped to stories and spikes.
- The repository and project-board links.
- An issue-status burndown: original scope 20, but actual open-issue points are zero
  at September 7-8 because all six closed before the sprint. No future actuals or
  invented within-sprint velocity. Six acceptance procedures are tracked separately
  as pending at the September 8 first task snapshot; final sign-off follows review.
- Initial UAT specifications for every Sprint 1 story.
- A backlog-grooming statement. Current result: no Sprint 1 scope change is needed;
  the board already matches the Week 2 plan. Sprint 2 stories remain separate.

The report supplies these items and story-specific evidence status; manual UAT and
the engine-extension acceptance exercise have not been executed. Andrew Lam owns
those procedures and must record revision, timestamp, actual outcomes, sanitized
evidence, and defects before final DoD sign-off. Unchecked criteria above are the
standard to assess, not an assertion that existing implementation is absent.

Grooming correction, September 8: Sprint 2's unchanged estimates sum to 21, not 18;
the estimated Sprint 1-3 baseline is 62. README is corrected; the submitted Week 2
report is preserved. Unestimated US-19 (issue #62, Sprint 2) and idea #49 are outside
that total and Sprint 1. No architecture change was made; no new ADR is needed.

## Reporting boundary

The following work is not Sprint 1 scope and should remain separate in reporting:

- US-2 CSV import, currently In Progress on the board.
- Sprint 2 stories US-6, US-7, US-8, US-10, and US-13.
- Sprint 3 stories US-9, US-11, and US-12.
- The Orbi mascot prototype and company-research-agent idea.

Those items may be mentioned as early implementation or future backlog context, but
they should not inflate the Sprint 1 velocity or burndown.
