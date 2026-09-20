# 0021. Automatically follow filings for holdings and private watchlists

- **Status:** Accepted
- **Date:** 2026-09-19

## Context

After testing the first US-11 implementation, the user requested automatic retrieval for
all existing holdings and a watchlist for companies they do not own (US-21, issue #90).
Selecting each company and initiating downloads makes access to evidence unnecessarily
manual. Watchlist preferences must remain private and cannot affect risk calculations.

## Decision

- Extend ADR 0019's scheduling and authorization: the existing single worker discovers
  the union of all held and watched tickers from committed database state. It scans on
  startup and every 30 seconds **between jobs**, queuing up to 100 oldest due tickers per
  scan. Existing holdings, manual additions and CSV imports need no separate queue calls.
  Downloads remain asynchronous and serial; queue backlog or a long job can delay a scan.
- Check ready tickers again after 24 hours, failed/partial after one hour, and unsupported
  after seven days. Reuse parser-versioned accession cache and existing rate limits.
  Atomic conditional upserts prevent scheduler/manual-refresh races from resetting active
  jobs. Manual refresh retains its 15-minute completed/60-second failed cooldown.
- Persist private `(user_id, ticker)` watchlist entries with a unique composite key and
  cascading account deletion. Reuse ticker normalization and symbol recognition, cap each
  account at 100 watched tickers, and serialize additions on the account row. Holdings
  and watches may overlap; removing a watch never removes a holding.
- Add authenticated watchlist list/add/remove endpoints and a combined filings-company
  list with held/watched flags and shared sync status. Authorize each filing operation
  if the caller currently holds **or** watches the ticker. Never expose other users' lists,
  account counts or portfolio quantities in the public filing corpus.
- Before starting each queued job, check global tracking membership. Removing the last
  holder/watcher stops future starts and recurring refreshes; an already running public
  filing job may finish. Retain shared public cache and dormant queued rows for reuse.
  Removal from both sets immediately revokes that caller's access even if another account
  still follows the same company.
- Keep all scheduling in the worker/data layer. Portfolio CRUD, CSV persistence and the
  pure risk engine stay independent of SEC configuration and availability. With no SEC
  contact configured, watches still save and cached sources remain available, but no jobs
  are automatically scheduled. UI states this clearly.
- This is a user-authorized secondary extension implemented early; no existing sprint
  assignments or point estimates change. US-21 remains unassigned/unestimated pending
  planning and acceptance.

## Consequences

One new table and migration are required, with no new service or dependency. The database
is the source of truth, so there is no lost event between saving a holding and queuing its
filings. Background scans work even when the user is offline. Daily checks are eventual,
not real-time SEC alerts. Unsupported funds remain explicit; the worker does not infer
underlying stock holdings. Larger deployments may require more efficient scheduling and
fairness controls; the serial bounded capstone deployment retains its existing throughput.

## Alternatives Considered

- Browser-triggered ingestion: misses companies until the user visits and cannot refresh
  while they are offline.
- Queue directly in every portfolio-write route: couples core persistence to secondary
  features and still needs backfill/reconciliation and recurring scheduling.
- Watchlist positions with zero quantity: contaminates portfolio semantics and risk inputs.
- A separate scheduler/broker: unnecessary additional infrastructure at this scale.
