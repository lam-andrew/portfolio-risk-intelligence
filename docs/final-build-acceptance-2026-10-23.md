# Final-build acceptance execution — October 23, 2026

## Scope and release boundary

Run by Claude Code at Andrew's request on October 23 PDT. Like the
[October 10 record](core-acceptance-2026-10-10.md), this is agent-run acceptance testing,
**not** Andrew's sign-off. It moves no story to Done and doesn't change sprints, estimates or board
fields.

- Revision: integrated PR #92 head `07be0bb`. The cooldown defect below was fixed in #106 and retested at `4a021b7`.
- **Normal stack** (live providers): Compose project `orbit` with the local-embeddings overlay, migrated
  0007 → 0008 after a private database backup. Real Tiingo prices, the real SEC worker, and a disposable
  account `orbit-qa-…@example.com` holding synthetic quantities. Andrew's own holdings weren't touched.
- **Fixture stack** (controlled): separate project `orbit-final` (ports 5188/8088, ephemeral
  `orbit_acceptance` database), built from `docker-compose.acceptance.yml` with the same revision.
  The existing `orbit-acceptance` demo stack wasn't changed.
- Not covered: the live Gemini Q&A evaluation (labels frozen, execution pending; see
  [US-12 runbook](us12-live-evaluation.md)), OptiPlex or homelab deployment, a screen-reader audit,
  and Andrew's product review.

## Live-provider procedures (normal stack)

| Requirement / story | Case | Actual result | Result |
|---|---|---|---|
| FR-11 / US-9 #9 | W9-UAT-9-01 / ST-09 | Prices dated 2026-10-23 for AAPL 10, MSFT 5, KO 20. 10%: baseline $7,954.00, loss $795.41 ($347.73 + $262.26 + $185.42), after $7,158.59. 35%: loss $2,783.90 ($1,217.04 + $917.89 + $648.97), after $5,170.10. AAPL edited to 12 (keyboard: Tab to Save, Enter), then 20%: baseline $8,649.45, loss $1,729.89 ($834.54 + $370.84 + $524.51). Each row was checked independently against `quantity × price × shock` with half-up cent rounding, and totals equal the row sums. Running scenarios didn't change any holding. Run via keyboard. | Pass |
| FR-13 / US-11 #11 | W9-UAT-11-01 / FI-08 | AAPL resolved to Apple Inc. / CIK 0000320193. Selected 10-K `0000320193-25-000079`, 10-Q `0000320193-26-000020` and the five latest 8-Ks match SEC's `submissions` list exactly; the 8-K/A `0001140361-26-035325` was correctly excluded. Search for "cash dividend" returned 10-Q passages. Three sentences were found verbatim in the rendered SEC document. VOO (watchlist) shows "No supported corporate filer matches this ticker." | Pass |
| FR-13 / US-11 #11 | W9-UAT-11-02 / FI-03 / FI-08 | KO's first live download: only `orbit-filing-worker-1` was killed (SIGKILL) at 1/7 documents. After restart it resumed 1/7 → 6/7 → ready 7/7 in about 10 s: 7 filings, 582 passages, no duplicates. AAPL manual refresh after the 15-minute cooldown was accepted (202) and stayed at 7 filings / 255 passages. A second account got identical 404s for a real, fake and cross-ticker accession; anonymous got 401. | Pass after fix (defect 1) |

## Controlled procedures on the final build (fixture stack)

API results via the real routes. Desktop and 375 px views were checked in a browser.

| Case | Actual result | Result |
|---|---|---|
| W6-UAT-13-01/02 | Login → holdings 200, logout 204, replayed session 401. Wrong password and unknown account both returned 401 with "Incorrect email or password." and set no cookie. | Pass |
| W6-UAT-2-01/02 | AAPL 10 and MSFT 5.5 imported. Partial file: AAPL added; row 3 `abc` and row 4 `-5` rejected with reasons. | Pass |
| TC-1-03, TC-3-03 | ZZZZ rejected (422) with count unchanged. AAPL 10 → 12.5 and MSFT 4 reflected in the summary. | Pass |
| W6-UAT-6-01/02 | Correlated pair 1.00. Constant MSFT: cross and diagonal `null`, no measured zero. | Pass |
| TC-5-03 | AAPL/NVDA ±1% fixture: holdings and portfolio 16.22%, matching the independent `100·√252·√(24·0.01²/23) = 16.2159`. The October 10 record listed 11.47 for this case; the fixture formula in that same record gives 16.22. | Pass (expected value corrected) |
| W6-UAT-7-01/02 | HHI 0.39, effective holdings 2.60, BIG 2.20×. Overlap QQQ/VOO/VTI = 80.0% at minimum ρ 0.93; BND excluded. | Pass |
| W6-UAT-8-01/02 | Recovered: worst −40%, current 0%, recovery dated. Ongoing: −25%, `recovered: false`, no recovery date. | Pass |
| W6-UAT-10-01/02 | $10,000.00, 9.32% volatility, average correlation 0.48, weights 30/25/25/20, closest pair VOO/VTI 1.00 shown. Empty account: no positions and null total. Provider error: 503 with holdings retained. Analytics-only failure: summary 200, drawdown/stress 503. | Pass |
| W9-UAT-9-02 | One holding unpriced: `unavailable`, null totals, `missing_tickers: ["ZZTEST"]`, holdings unchanged. Restored pricing: ready, losses reconcile. Stale-response ordering is still covered by frontend ST-07, not repeated in the browser. | Pass |
| UI sweep | Dashboard, correlation, concentration, drawdown, stress and methodology: no horizontal overflow at desktop or 375 px. All 10 methodology anchors resolve. Light mode at mobile width renders. Only console errors were the expected pre-login 401 session checks. | Pass |

## Defects and observations

1. **Fixed — filing refresh cooldown notice disappeared.** A 429 from **Refresh filings** was cleared
   by the next successful 10 s status poll (present at 6 s, gone by 9 s). It also offered the
   unrelated **Refresh status** button. [#106](https://github.com/lam-andrew/portfolio-risk-intelligence/pull/106)
   keeps refresh errors in separate state. The regression test failed before the fix; 123
   frontend tests pass after it. A live retest at `4a021b7` showed the notice persisting through 21 s of polling.
2. **Observation, not changed:** pressing Enter in the inline holding-quantity editor does nothing, and
   Escape doesn't cancel. Keyboard users can still Tab to **Save**. Left for Andrew's review rather than
   expanding scope.

## Remaining gates

US-12's live 20-case evaluation (Gemini daily limits), Andrew's product review of the integrated
preview, #92 review/merge, and separate-VM deployment. Stories remain In Progress until their
evidence is reviewed and accepted.
