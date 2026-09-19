# 0018. Hypothetical portfolio stress tests

- **Status:** Accepted
- **Date:** 2026-09-18
- **Story:** US-9 / FR-11, issue #9; early implementation, Sprint 3 assignment unchanged

## Context

Orbit calculates historical risk but cannot yet answer what a defined adverse scenario
would mean in dollars. US-9 requires a selectable scenario and estimated portfolio impact.
Sector classification, historical crisis replay and factor exposures are not available;
scenario names must not imply that these mechanisms have been calibrated.

## Decision

Provide three server-owned hypothetical scenarios: equal 10%, 20% and 35% price declines
across every holding. There is no probability or time horizon. The scenarios apply to all
assets, including bonds and ETFs; they do not infer diversification or differential responses.

Add authenticated, read-only `GET /api/portfolio/stress-scenarios` and
`GET /api/portfolio/stress?scenario=<id>` routes. Unknown IDs return 422. Only the signed-in
user's holdings are loaded. The API obtains prices through the existing cache-aware market
service and calls a pure Decimal engine with position values and a fractional shock. No
holdings mutation, result persistence, new provider, database migration or statistical fitting.

Use the most recent shared date with finite positive adjusted closes for **every** holding
within a 30-calendar-day lookback. This matches Orbit's adjusted-close valuation convention;
it is an analytical baseline, not a live liquidation quote. Report that date prominently.
Cached data can be stale. Withhold all totals when a holding cannot be priced or there is no
shared date. Empty and unavailable responses contain null totals, not zero-loss estimates.
Configuration/service dependency failures retain the existing HTTP error handling.

For each holding: baseline = quantity × adjusted close; loss = baseline × decline fraction;
after = baseline − loss. Round baseline and loss per position half-up to cents, then sum
rows for totals. Report realized loss / baseline × 100 to two decimal places; cent rounding
can cause tiny differences from the scenario percentage. Withhold a zero-cent portfolio.
This deterministic what-if calculation needs one price per holding, not 20 daily returns:
the statistical minimum in ADR 0012 still applies unchanged to estimated historical metrics.

The frontend fetches the catalogue on entry and computes only after Run stress test. Changing
selection clears the old result and invalidates in-flight responses; changing holdings or
leaving the screen also invalidates old requests. All math remains behind the API.

## Consequences

- A reproducible, independently testable end-to-end scenario feature with complete-price checks.
- Dollar contributions show position size, not a model of individual asset sensitivity.
- No live quotes, predicted losses, scenario probabilities, taxes, fees, currency modeling,
  crisis replay, custom shocks or trading. These limitations appear next to results.
- Baselines may differ from the overview, which values holdings at individually latest dates.
- Historical replay or differentiated shocks require a later explicit methodology decision.

## Alternatives considered

- **Historical crisis replay:** useful but needs agreed event windows and a policy for assets
  without sufficient history. Deferred rather than presenting invented crisis estimates.
- **Sector/factor shocks:** needs exposure data and calibrated sensitivities not in the product.
- **Partial portfolio totals:** rejected because missing positions would understate the estimate.
- **Calculating in React:** rejected because the API owns financial calculations and validation.
