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
