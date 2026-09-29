# Sprint 2 plan and Definition of Done

**Planning date:** September 28, 2026  
**Owner:** Andrew Lam  
**Window:** Weeks 6–8, September 28–October 18 (planned)  
**Committed scope:** 23 points; seven stories.

## Goal

Accept the core portfolio workflow: authentication, CSV import, correlation, concentration, drawdown, dashboard and explanations. Existing implementations predate this sprint. Story points burn on acceptance, not merely on code availability.

## Selected backlog

| Story | Requirement | Points | Implementation | Priority and dependency |
|---|---|---:|---|---|
| [US-13](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/13) Authentication | FR-15 | 3 | [734419e](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/734419e), PR #67, Aug 31 | First: protects every portfolio workflow; session and ownership failures have high impact. Existing implementation reduces coding uncertainty, but browser acceptance is still required. |
| [US-2](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/2) CSV portfolio import | FR-2 and FR-3 | 3 | [e4baa80](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/e4baa80), PR #57, Aug 30 | Second: gives realistic portfolios to all risk stories. Brokerage formatting and partial failures create more risk than a simple upload control suggests. |
| [US-6](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/6) Correlation among holdings | FR-8 | 5 | [c003351](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/c003351), PR #58, Aug 30 | Third: supplies the relationship information needed to explain diversification and overlapping exposure. Date alignment and constant returns require careful verification. |
| [US-7](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/7) Concentration and overlapping exposure | FR-9 | 3 | [bd0bcf9](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/bd0bcf9), PR #60, Aug 30 | Fourth: translates weights and correlation into understandable exposure. It depends on valuation and US-6, while pure concentration math can be verified independently. |
| [US-8](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/8) Historical drawdown | FR-10 | 2 | [bd0bcf9](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/bd0bcf9), PR #60, Aug 30 | Fifth: extends the existing portfolio value series into a downside measure. Peak/trough/recovery dates and ongoing declines are the main correctness risks. |
| [US-10](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/10) Risk dashboard | FR-12 | 5 | [23ca50b](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/23ca50b), PR #59, Aug 30 | Sixth for final acceptance: integrates the preceding metrics into one usable product. Review begins earlier so visual defects can be found before all stories close. |
| [US-19](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/62) Risk methodology companion | FR-12 support | 2 | [9794b55](https://github.com/lam-andrew/portfolio-risk-intelligence/commit/9794b55), PR #63, Aug 30 | Companion verification for explanatory quality. Andrew approved 2 points on September 28 for verification and refinement of the existing implementation. |

Original six estimates total 21 points. Andrew approved 2 points for US-19 on September 28 for verification/refinement of the existing methodology implementation. The issue and Project fields now reflect Sprint 2, 2 points. No historical implementation date or original estimate changes. All seven issues remain open.

## Shared Definition of Done

- [ ] Acceptance criteria reviewed and requirement/test IDs linked.
- [ ] UI/design, implementation, persistence and API integration complete where applicable.
- [ ] Automated unit/system tests and required CI/security checks pass on the reviewed revision.
- [ ] UAT executed with expected/actual results and evidence; no blocking acceptance defect remains.
- [ ] Focused PR reviewed and merged through GitHub; living docs and board synchronized.

### US-13

- [ ] Verify valid and invalid login, session persistence and logout; confirm unauthenticated access and cross-user portfolio access are denied. Retain session and password-handling tests under ADR 0014.

### US-2

- [ ] Verify generic and brokerage-format files, precise quantities, actionable row errors and persistence. Confirm existing holdings follow the documented update behavior; preserve user ownership.

### US-6

- [ ] Verify matrix labels, symmetry, diagonal values, range and missing-data handling. Compare displayed figures with the API; confirm undefined correlations are not presented as measured zero.

### US-7

- [ ] Verify HHI, effective holding count, top weights and overweight highlighting. Check correlation-based overlap groups and their combined weights; explain that this is not fund constituent look-through.

### US-8

- [ ] Verify current and maximum drawdown, episode ordering and recovery status. State the observed period and historical limitations; insufficient history must not produce invented precision.

### US-10

- [ ] Verify summary metrics, holdings/history and supporting risk views, loading/error/empty states, readable units and keyboard access. Check desktop and narrow-screen layouts; review PR #94 independently before integrating its optional refresh.

### US-19

- [ ] Verify all four explanations and formulas against ADR 0012, own-portfolio examples, metric anchors and limitations. The approved estimate is 2 points; include it in the committed burndown.

## Sprint 1 verification carryover

The September 23 Week 5 assessment recorded TC-15-03 (isolated engine extension) and the API contract check as passed. Five procedures remain Not executed at September 28. These are verification tasks, not additional pointed stories. The older Sprint 1 documents retain their original dated snapshots.

| Procedure | Requirement | Work | Method |
|---|---|---|---|
| TC-14-01 | AR-1 / #14 | Disposable Compose stack and authenticated browser/API connectivity | Manual system |
| TC-1-03 | FR-1 / US-1 | Valid holding entry and invalid ticker rejection in browser | Manual UAT |
| TC-3-03 | FR-4 / US-3 | Quantity edit, cancel/confirm removal and refreshed analysis | Manual UAT |
| TC-4-03 | FR-5/6 / US-4 | Live provider retrieval followed by demonstrated cache reuse | Live integration |
| TC-5-03 | FR-7 / US-5 | Displayed holding and portfolio volatility compared with API | Manual UAT |

Andrew will execute these first, record failures as defects and reconcile acceptance evidence with the already-closed Sprint 1 issues. Closed issues do not substitute for the missing acceptance evidence.

## Retrospective actions and iteration plan

- Week 6: Andrew owns carryover verification, reviewed acceptance criteria and mapped test specifications. Make acceptance evidence a closure gate; begin repeatable per-component coverage reporting.
- Week 7: refine UI design and unit/system specifications, automate gaps and integrate fixes.
- Week 8: execute tests/UAT, report coverage and defects, close the sprint and prepare the prototype demo.
- Limit active core acceptance/refinement work to one story. Defer secondary work before reducing core scope; scope changes require explicit approval.

## Grooming and boundaries

US-9 (8), US-11 (5) and US-12 (8) retain Sprint 3. US-12 draft PR #92 and UI PR #94 remain unmerged. US-21, UI #93, technical maintenance #85 and stretch/research ideas remain outside this 23-point scope unless separately approved. Unselected, unestimated items are not assigned artificial points. No original requirement was removed. Technical work is tracked separately from functional stories.

## Progress baseline

September 28: approved scope 23; accepted 0; remaining 23. Five carryover verification tasks tracked separately. Ideal remaining points reach zero October 18; no future actual results are asserted. Record actual date/revision/evidence for each accepted item and scope adjustment. Sprint 1 implemented 20 points before its academic window, so it does not establish a 20-point accepted velocity forecast.

## References

- [Sprint 2 test specifications](sprint2-tests.md)
- [Project board](https://github.com/users/lam-andrew/projects/2)
- [Risk conventions](adr/0012-risk-methodology.md)
- [Authentication](adr/0014-authentication.md)

No new architecture decision is introduced by this planning update.

## Integration blocker observed September 28

The documentation PR #95 triggered fresh CI on the main-based planning branch.
Backend type-checking fails in `app/data/filing_schedule.py` (lines 21 and 45):
SQLAlchemy `CompoundSelect` return typing and a missing inferred list annotation.
The compatibility fix already exists in unmerged commit `5de4b25` on PR #92.
This is an existing code/dependency compatibility problem, not a documentation
change. Keep #95 unmerged until the fix is integrated and required checks pass.
[Failure evidence](https://github.com/lam-andrew/portfolio-risk-intelligence/actions/runs/36521193675).
