# US-21 / FR-16 — automatic filing following

Implementation date: September 19, 2026. [Issue #90](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/90)
is a user-requested secondary extension, with no sprint assignment or estimate. US-11's
Sprint 3 assignment and five-point estimate are unchanged. Design: [ADR 0021](adr/0021-automatic-filing-following.md).

## AF-01 — discover existing, manual and imported holdings

- **Traceability:** FR-13 / US-11; FR-16 / US-21.
- **Preconditions:** authenticated account; configured SEC contact; worker running; supported
  ticker provider; no corresponding sync row.
- **Inputs:** existing AAPL position; later manual or CSV additions of MSFT.
- **Steps:** start the worker; inspect status without POSTing an ingestion request. Add/import
  MSFT, leave the filings page closed, then inspect the next scan.
- **Expected:** one shared job per tracked ticker; AAPL is backfilled and MSFT is discovered
  from committed holdings. Scan occurs every 30 seconds between jobs, so a busy queue may
  delay discovery. Indexed documents are reused on the next due check.
- **Postconditions:** portfolio quantities are preserved; successful jobs retain source corpus.
- **Evidence:** `test_backfills_existing_manual_and_imported_holdings_without_filing_requests`;
  isolated browser AAPL automatically indexed 3/3 synthetic documents before opening filings.

## AF-02 — watch without ownership and display progress

- **Traceability:** FR-16 / US-21; source indexing remains FR-13 / US-11.
- **Preconditions:** authenticated account with an empty watchlist; valid company ticker;
  worker and SEC configured. Also repeat with an empty portfolio.
- **Inputs:** ` msft `, duplicate `MSFT`, invalid ticker and a full 100-entry watchlist.
- **Steps:** add the ticker; wait for background discovery without selecting Retrieve;
  inspect sources and keyword search. Attempt duplicate/invalid/over-limit additions.
- **Expected:** normalized unique MSFT membership, one job, automatic progress to indexed
  sources; duplicates are idempotent; invalid symbols and excess entries are rejected.
  Holdings, portfolio valuation and risk inputs are unchanged. No holdings are required.
- **Postconditions:** private watch survives page reload; source access remains authorized.
- **Evidence:** backend watch/input/limit tests; frontend add/error/idle-poll tests; browser
  MSFT transitioned from automatic-wait state to 3/3 indexed using synthetic SEC responses.

## AF-03 — membership isolation, overlap and removal

- **Traceability:** FR-16 / US-21; authenticated access FR-15 / US-13.
- **Preconditions:** two accounts; one owns and watches AAPL, the other initially does neither.
- **Steps:** compare each account's lists. Attempt foreign reads, search, refresh and removal.
  Remove AAPL's watch while still held, then test watch-only access after holding deletion.
  Remove both memberships; repeat with another account still watching AAPL.
- **Expected:** private lists stay isolated; foreign/removed access is 404, anonymous access
  401. Removing a watch never deletes a position. Shared corpus is reused when another
  account follows the same ticker, without exposing the first account's membership.
- **Postconditions:** no new job starts for a globally untracked ticker; retained public
  corpus is not deleted. A running job may finish. Re-adding can reuse dormant queued work.
- **Evidence:** backend account/overlap/removal/unauthenticated tests; browser watch removal
  immediately selected an existing holding. Frontend tests cover failed removal, retained
  holding access and an old list response arriving after successful watch removal.

## AF-04 — due intervals and scheduling races

- **Traceability:** FR-16 / US-21; ADR 0021 technical concurrency policy.
- **Preconditions:** tracked terminal jobs with a known update timestamp; controlled clock.
- **Inputs:** ready: 24 hours; failed/partial: one hour; unsupported: seven days.
- **Steps:** schedule one second before each boundary and at the boundary. Repeat for queued
  and running jobs. Queue a manual refresh from a separate database connection between
  scheduler discovery and its upsert. Add the same watch concurrently in two sessions.
- **Expected:** no early requeue; one due job at boundary; active work preserved; conditional
  upsert retains the manual job; one watch entry after concurrent adds; no duplicate download.
- **Postconditions:** corpus/issuer mapping retained; account deletion cascades watch entries.
- **Evidence:** parameterized clock tests and cache reuse; two new native PostgreSQL tests
  exercise the real conditional upsert, account lock, uniqueness and deletion cascade.

## AF-05 — configuration, unsupported tickers and recovery

- **Traceability:** FR-16 / US-21; FR-13 / US-11.
- **Preconditions:** SEC contact unset, then restored; BND unsupported by synthetic provider.
- **Steps:** add a watch while downloads are unconfigured; inspect message and cache; enable
  configuration and scan. Follow BND and inspect its status. Restart worker after interruption.
- **Expected:** preferences save even while automatic downloads are paused; no scheduling
  without configuration; first scan after configuration discovers the watch. Unsupported
  tickers remain explicit. Existing interrupted-job recovery applies; no risk dependency.
- **Postconditions:** source cache survives failures; recurring checks follow AF-04 intervals.
- **Evidence:** disabled/resume unit test; existing FI-03/FI-06 configuration/recovery coverage;
  browser showed BND as “No supported filings.” Live interruption UAT remains pending FI-08.

## AF-06 — user acceptance and accessibility

- **Traceability:** FR-16 / US-21.
- **Preconditions:** local app on `/filings`, signed-in user; desktop and narrow mobile viewport.
- **Steps:** review automatic behavior and membership labels; add/remove a test watch; select
  a company; verify sources, status and errors are readable; navigate controls by keyboard.
- **Expected:** labeled inputs/actions, selected company and membership are clear, sources
  remain available after refresh failures; no horizontal overflow; no manual ingestion required.
- **Postconditions:** remove test watch; keep user's real holdings unchanged.
- **Evidence:** controlled real-HTTP browser check with isolated SQLite and injected test
  identity, synthetic SEC/market data; desktop and 390px mobile inspected, width 390/390.
  Browser auth isolation is not claimed from the injected identity; API tests cover it.
- **Acceptance:** user review and full keyboard-only acceptance remain pending. No instructor
  acceptance or production deployment claimed.

## Automated results

September 19 local validation: **244 backend tests passed**, four native PostgreSQL cases
skipped by the ordinary suite and **all four passed separately** against a disposable
PostgreSQL database. **82 frontend tests passed**. Ruff lint/format, strict mypy, ESLint,
Prettier, TypeScript and production build passed. Existing nonblocking Fast Refresh and
Starlette/httpx warnings remain. Migration 0006 was applied to the local app without
resetting accounts or holdings; a 0006 → 0005 → 0006 round trip passed in the disposable
database. The normal local worker automatically checked existing tickers: 11 ready and
seven unsupported at inspection, with no queued/running/failed jobs remaining. This is live
backfill integration evidence, not user acceptance of every extracted source. CI/security
results are recorded in the PR.

This evidence supplements [US-11 tests](us11-filing-tests.md); it does not establish
FR-14 grounded Q&A. Automated and controlled browser checks use synthetic SEC documents.
