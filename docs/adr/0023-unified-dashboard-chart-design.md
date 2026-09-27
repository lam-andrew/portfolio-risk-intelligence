# 0023. Unified dashboard and chart treatment using the existing palette

- **Status:** Accepted — user approved September 26, 2026; implementation under review
- **Date:** 2026-09-26
- **Tracking:** [UI refresh #93](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/93)

## Context

Andrew approved a dashboard reference and an Orbit-palette interactive preview, then clarified
that the plotted marks themselves—not only panel chrome—must carry the direction: point markers
on fine lines, rounded highlighted bars and separated allocation segments. He requested a
full application sweep while configuring the independent US-12 model key.

## Decision

Retain ADR 0013's React/SVG components and ADR 0016's shared application palette. No charting
library, hosted design service, new network dependency, backend API or risk model is added.
Extract reusable presentation components for historical lines, zero-based bars and proportional
allocation sectors. All signed-in charts consume existing API results. Marketing illustrations
remain illustrative and never appear as real portfolio data.

Use rounded neutral panels, one blue primary metric, a compact labeled desktop navigation rail,
pill controls and restrained ambient light outside the plotting surfaces. Keep signed-out,
signed-in and documentation routes visually continuous. Both themes use existing tokens; a
local theme preference survives reload. Finite SVG dimensions, native keyboard controls,
visible values, readable axes and reduced-motion support are required.

Sparse markers improve legibility but do not downsample the historical line. Date inspection
exposes every observation. Drawdown keeps its non-positive scale and red semantic color.
Correlation retains its signed diverging heatmap. Stress keeps the value bridge and an explicit
hypothetical label; bar heights use a common zero baseline. Allocation angles represent weights,
with a labeled Other group for portfolios exceeding six slices and no invented unpriced weights.

The UI branch is stacked on the unmerged US-12 branch so its question screen participates in
the shared styling. The UI PR does not approve, activate or merge the model integration. No
existing sprint assignment, estimate or story completion status changes.

## Consequences

One shared styling layer reaches forms, tables, unavailable states and charts. The chart
components own their responsive labels and controls, creating a bounded maintenance cost.
More generous layout can increase page length; wide tables remain scrollable inside their
panels. Extra visual polish must not alter axes, hide provenance or imply forecasting.

## Alternatives Considered

- CSS-only panel refresh: rejected because it omits the chart treatment explicitly requested.
- Copying the reference's decorative equal-sized pie wedges: rejected where those shapes
  would misrepresent unequal portfolio weights.
- Adding the mockup's D3 dependency to production: unnecessary for these bounded SVG charts
  and inconsistent with ADR 0013 without a demonstrated need.
- Combining this work with US-12 in one PR: rejected; review and live model acceptance are
  separate concerns, even though the UI branch builds on that implementation.
