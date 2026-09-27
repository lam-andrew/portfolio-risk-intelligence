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
