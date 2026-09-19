# User Guide — Orbit

**Status:** Living document. Created Week 2; grows as features land.

> Initial version. Sections are added as each feature ships, so that the final user
> documentation is written alongside the product rather than reconstructed from it.

---

## What Orbit is

Orbit helps a self-directed investor understand the risk in their own portfolio. Enter what
you hold, and Orbit measures how much it moves, how concentrated it is, how much its holdings
overlap, and how far it has fallen in the past. Every number comes with an explanation of what
it means and how it was calculated.

**What Orbit does not do.** It does not predict prices, recommend or place trades, or give
investment advice. It measures and explains what your portfolio already is. Treat its output
as one input to your own thinking, not as a recommendation.

---

## Getting started

### 1. Create an account

Orbit requires an account because your portfolio is private to you. Sign up with an email
address and a password. Your password is stored only as an irreversible hash, and Orbit never
asks for your brokerage login.

### 2. Add your holdings

Two ways:

- **Enter them manually.** Type a ticker symbol and the number of shares. This works for any
  brokerage.
- **Import a CSV.** Export a positions file from your brokerage and upload it. Orbit
  understands the export formats used by major brokerages, including their preamble rows,
  currency formatting, and total rows. Rows it cannot read are reported individually by line
  number, so a single bad row never silently drops a position.

A note on brokerage exports: some brokerages export *transactions* rather than *positions*.
Orbit needs positions, meaning what you currently hold. If your export lists individual buys
and sells, enter your positions manually instead.

### 3. Keep your holdings current

Open **Holdings** to view and manage existing positions. Use a row's edit control,
enter a positive share quantity, and save; cancel leaves the previous value unchanged.
Fractional shares are supported. A rejected update shows an error and keeps the row.

Use the delete control only for a position you intend to remove. Confirm the deletion
to proceed, or cancel to keep the holding. After a successful change, the application
refreshes portfolio data and analysis. Deleting a holding removes it from subsequent
analysis, not merely from the displayed table. Recorded end-to-end acceptance of this
workflow is tracked in [Sprint 1 specification TC-3-03](sprint1-tests.md); this guide describes intended use,
not a completed UAT result.

### 4. Read your risk

Once you have holdings, Orbit fetches historical prices and computes:

| Metric | The question it answers |
|---|---|
| **Volatility** | How much does this swing, in a typical year? |
| **Correlation** | Which of my holdings move together, and which are genuinely different? |
| **Concentration** | How much of my money rides on my largest positions? |
| **Stress test** | What would an assumed equal decline mean in dollars? |
| **Drawdown** | How far has this portfolio fallen from a peak, and how long did recovery take? |

---

## Understanding the numbers

Orbit includes a **methodology page** explaining every metric: the formula, why that method was
chosen over the alternatives, and what its limitations are, worked through using your own
portfolio's figures. Each risk card links directly to the relevant section.

Two things worth knowing before you interpret anything:

- **Volatility measures dispersion, not danger.** A high figure means a wide range of outcomes,
  up as well as down. It is not a prediction of loss.
- **Historical metrics are backward-looking.** Volatility, correlation and drawdown describe
  historical behavior. Stress tests instead apply explicit hypothetical assumptions.
  Correlations in particular tend to rise during market stress, which is exactly
  when diversification is most needed. Past behavior constrains your expectations; it does not
  determine the future.

---

## Run a stress test

Open **Stress test** in Risk & Exposure, choose a broad decline of 10%, 20% or 35%, and
select **Run stress test**. Read the baseline value, estimated dollar and percentage loss,
value after the scenario, and the loss contributed by each holding. The same decline applies
to every holding, so larger positions contribute more dollars of loss.

The **From baseline to stressed value** chart shows the starting amount, a hatched loss
step, and the remaining amount on a shared zero-based scale. It compares values rather than
showing a path over time. **What contributes most to the loss?** ranks up to five holdings
by dollar loss; the complete holdings table remains below the charts.

Check the **pricing date** above the results: all holdings use the latest shared date in
the last 30 days, at current share quantities. Prices are adjusted closing prices from the
market-data cache, not live quotes, and may be stale. The baseline can differ from Overview,
which uses each holding's individually latest price. Dollar amounts round per holding and
the totals sum the displayed rows.

Changing the scenario clears the old estimate; run again to calculate the new selection.
After editing/importing/deleting holdings, return to Stress test and run again. Empty
portfolios show an Add holdings prompt. If prices are missing or have no shared date, no
partial total is shown. Resolve the pricing problem and retry. Request failures provide a
retry path; a new calculation never silently retains an old result.

These scenarios are **assumptions, not forecasts or historical crisis replays**. They have
no probability or time horizon. Bonds and ETFs receive the same decline as stocks. There
is no sector sensitivity, diversification effect, taxes, fees, currency modeling or trade
execution. Use **How this is calculated** for the formula and limitations.

## Retrieve and search SEC filings

Open **SEC filings** under Insights. Orbit automatically retrieves filings for all your
holdings, including ones saved before this feature and positions added by CSV import.
You do not need to open this screen or select each company to start retrieval. The worker
looks for new companies on startup and every 30 seconds between jobs; a busy queue can
delay retrieval. Choose a company to inspect its sources.

The **Watchlist** lets you follow up to 100 companies without owning them. Enter a ticker
and select **Add to watchlist**; its filings join the same automatic process. A watchlist
works even with an empty portfolio and never changes quantities or risk calculations.
**Remove** stops your watch. If you also hold the company, it remains followed through
your holdings. Removing it from both lists revokes your access; cached public documents
remain shared, and an already running download may finish. A company still followed by
another account continues receiving refreshes without exposing either account's list.

The status reports finding the company, finding filings, downloading and indexing. Once
the catalogue is known, the progress bar counts indexed documents. Work continues if you
leave the page; returning reads the stored status. A job can remain queued while the worker
is stopped. A failed status read has a **Refresh status** action.

This release selects the latest 10-K, latest 10-Q and five latest 8-K primary documents in
SEC's recent submissions list. It does not ingest all history, amendments, exhibits or
fund-specific forms. A missing corporate ticker match or absent supported forms is
reported explicitly; an ETF is not mapped to its underlying companies. Missing form types
and partial failures appear in the status message.

Each indexed source shows its form, filing date, accession and passage count, with a link
to the original SEC document. **Search filing passages** performs keyword search, returning
up to 20 matching excerpts with source links. Try specific terms such as “supply chain”.
No match means this search found no indexed passage, not that the company has no such risk.
These are original excerpts, not generated answers. Financial tables may lose layout during
text extraction; consult the source before interpreting their numbers.

Orbit checks successfully indexed companies for new filings daily, retries failed/partial
downloads hourly and rechecks unsupported tickers weekly. These checks run while the
worker is running, including when you are offline. They are not real-time filing alerts.
**Retrieve filings** / **Refresh filings** also lets you request an earlier check. Manual
completed refreshes are limited to once every 15 minutes; partial/failed attempts can retry
after one minute. Indexed documents are reused rather than downloaded again.
Previously indexed filings remain available after failures and accumulate over time. The
source list shows up to 50 newest filings; search includes all retained filings. Cached
accessions are not periodically re-downloaded to detect later SEC corrections.

If downloads are unconfigured, the operator must set `APP_SEC_CONTACT_EMAIL` locally and
recreate backend/worker services. Never enter a personal password or model API key on this
screen. Source search requires no LLM. Grounded Q&A and semantic search follow in US-12.

## Sections to be added

As the remaining features ship, this guide will gain:

- **Asking questions about your holdings** — the grounded, cited Q&A over SEC filings
  (US-11, US-12).

---

## Change log

| Date | Change |
|---|---|
| 2026-09-02 | Initial user guide created as a living document. |
| 2026-09-08 | Documented edit/save/cancel and confirmed deletion for US-3; distinguished usage instructions from pending UAT evidence. |
| 2026-09-18 | Added hypothetical stress-test workflow, pricing completeness rules and limitations for early US-9 implementation. |
