# Application UI and chart refresh — September 26, 2026

Tracking: [#93](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/93).
Design decision: [ADR 0023](adr/0023-unified-dashboard-chart-design.md).
This is user-requested presentation work, with no new sprint assignment or functional-story
completion claim. It is stacked on the US-12 branch; provider activation and live Q&A
acceptance remain separate.

## Scope and acceptance evidence

- Overview: four summary cards, full history plot, proportional allocation, compact
  correlation and full holdings/detail panels. Real API values and source captions remain.
- Holdings: shared cards, controls and tables; horizontal scrolling remains inside the
  panel at narrow widths. Editing/import behavior is covered by the existing tests.
- Correlation: signed heatmap and numeric cells retained; colors now follow theme tokens
  immediately. Existing nine heatmap tests pass.
- Concentration: proportional allocation with native selection controls and explicit
  aggregation of small holdings; original concentration measures remain visible.
- Stress: rounded value bridge and zero-based vertical loss bars, exact readouts and
  hypothetical-scenario limitations. Five chart and eight screen tests pass.
- Drawdown: fine red line with sparse markers, dotted zero baseline, exact date inspection,
  negative scale and existing episode table.
- Filings/Q&A: shared cards and rounded controls; company selection, source links, unavailable
  issuers and the disabled-provider state remain visible. Existing filing/question tests
  cover loading, failures, citations, isolation-facing screen behavior and disabled states.
- Methodology: shared panels/type and working section links; formulas unchanged.
- Public landing, sign-in and account-creation screens: same theme, controls and panel design.
  Public miniature charts are illustrations, not live portfolio results.
- Mobile navigation: labeled dialog, initial focus, Tab/Shift+Tab wrap, Escape dismissal,
  focus restoration and scroll locking. Dedicated regression case in `App.test.tsx`.

## Automated checks

Executed in the existing Docker Compose frontend service:

- Prettier, ESLint and TypeScript checks pass. ESLint retains the existing non-blocking
  Fast Refresh warning in `button.tsx`.
- **99 frontend tests pass** (12 files), including seven new chart cases, two theme cases
  and one mobile-navigation case. Tests verify aggregation, unavailable/single/zero inputs,
  finite SVG coordinates, exact date selection, proportional bar heights, theme persistence
  and storage failures. Existing data-entry and risk behavior tests remain green.
- Production build passes. No dependencies, API contracts or backend calculations changed.
- `npm audit --omit=dev --audit-level=high`: **zero vulnerabilities**.
- Full development-dependency audit: five existing findings (three moderate, one high,
  one critical), in the unchanged Vite/Vitest/esbuild toolchain. This refresh does not
  resolve them. The coordinated tooling migration is tracked by
  [#85](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/85).
- Host Node could not run the current ESLint formatter (`util.styleText` unavailable);
  supported container commands above were used instead. No runtime upgrade is included.

## Manual browser checks

The running Compose application was inspected using existing local holdings, without
changing portfolio data or calling a model. Desktop dashboard and stress graphics,
mobile history/allocation/drawdown, both themes, company selection, unavailable and
indexed issuers, methodology, public landing, and sign-in/account-mode switching were
checked. At 390px, overview, correlation, concentration, filings and methodology fit
without page-level horizontal overflow; wide tables retain their own horizontal scroll.
A holdings-table overflow found during this sweep was corrected by allowing cards to
shrink and containing positioned accessible labels inside the table scroller.

Private portfolio screenshots were used only for local inspection and are not published
as repository fixtures. Automated tests use existing synthetic data. No coverage percentage,
full screen-reader audit, live Q&A pass or user acceptance is claimed. User review of
visual density, spacing and chart emphasis remains pending; issue #93 stays open.

## Core acceptance follow-up — October 10, 2026

[The core acceptance sweep](core-acceptance-2026-10-10.md) exercised real browser/API/
PostgreSQL flows, chart keyboard controls and a narrow dashboard. It found and fixed
five presentation/navigation defects, with red/green regression proof.
The updated frontend suite passes 101 tests. Screenshots use disposable synthetic
portfolios; no personal holdings or model credentials are included.

## Atlas superseding direction — October 10, 2026

Atlas replaces the earlier rail/ambient treatment (ADR 0026), while preserving chart
geometry, API values and interaction controls. Full reader/chat behavior is added under
ADR 0027. See [Atlas verification](atlas-verification-2026-10-10.md) for current automated
results, route screenshots in both themes and remaining UAT. Historical evidence above
is retained as a record of the earlier refresh, not a claim of Atlas acceptance.

## Atlas correlation scaling refinement — October 10, 2026

Owner review found that automatic table layout stretched the row-label column, while
shared table padding made values tall rectangles. The overview also hid grids above six
holdings. The matrix now uses a bounded label column based on ticker length, equal square
value cells, and sizes based on both holding count and available space. Cells shrink from
80px to a 44px touch target; larger matrices scroll within a 400px overview / 640px detail
region with pinned column and row labels. All holdings remain available in both views.
Selected-pair feedback now works in the overview too. API values, null handling, and risk
calculations are unchanged. This is a reversible refinement under ADR 0026, with no new
architecture decision or story/sprint status change (US-6 #6, UI #93).

Verification: 121 frontend tests passed, including 2/7/18/50-holding completeness and
large-overview pair selection. ESLint, Prettier, TypeScript, production build and production
dependency audit passed (zero vulnerabilities). Existing button-export Fast Refresh and
filing-reader test `act` warnings remain. Backend code is unchanged.

A temporary browser fixture mounted the production CorrelationCard and stylesheet with
explicitly synthetic 2/5/12/30/50-holding inputs at 1440px and 390px, overview and full mode:
20 layouts, all n² values retained, square cells at least 44px, no page-level overflow.
The fixture was removed after inspection. The last pair in a 50-holding mobile matrix was
selected after scrolling; headers stayed pinned. The five-holding authenticated acceptance
app was also checked in both themes; its matrix fits the 390px phone width without scrolling.
See [measured geometry](evidence/correlation-scaling/measurements.json),
[desktop dark](evidence/correlation-scaling/desktop-dark.png),
[desktop light](evidence/correlation-scaling/desktop-light.png),
[mobile dark](evidence/correlation-scaling/mobile-dark.png),
[mobile light](evidence/correlation-scaling/mobile-light.png),
[overview mobile](evidence/correlation-scaling/overview-mobile-dark.png),
[12-holding layout](evidence/correlation-scaling/twelve-desktop-dark.png), and
[50-holding mobile selection](evidence/correlation-scaling/fifty-mobile-dark.png).
These checks establish layout/interaction behavior, not new financial-engine evidence.
Owner acceptance and PR review remain pending.
