# 0026. Orbit Atlas interface

- Status: Accepted direction; implementation under review
- Date: 2026-10-10
- Tracking: UI #93; separate filing contract in ADR 0027

## Context and decision

The owner requested the full Atlas handoff, including analytical visuals and both themes.
The separate Orbit pen.dev project and all 64 manifest previews were inspected. Atlas
supersedes ADR 0023's compact rail, pill controls and ambient lighting. Retain ADR 0013's
hand-authored SVG approach and the existing React/Tailwind application; no chart library,
new runtime service or risk calculation changes are needed.

Use labeled top navigation, a full-screen mobile menu, cobalt actions, restrained navy
or white surfaces, Space Grotesk headings, Geist body text and IBM Plex Mono data labels.
Shared tokens cover authentication, marketing, analytic views, forms and failure states.
Public sample charts are explicitly illustrative; authenticated charts use API data only.

Historical paths retain every observation with sparse markers and exact-value controls.
Allocation sectors remain proportional and use distinct colors. Correlation cells retain
signed values and add keyboard/touch pair inspection. Bars retain zero baselines. Null
current drawdown is unavailable, never inferred as recovery. Narrow holdings use labeled
stacked rows retaining edit/delete controls; dense matrices scroll within their panel.

## Consequences and alternatives

No deployment topology, provider selection, financial model or sprint estimate changes.
Existing font loading has system fallbacks. Reduced motion and theme preference remain.
The visual PR is independently reviewable. Reader/chat requires the separate API/security
change; styling the issuer endpoint as filing-scoped would be misleading and is rejected.
Browser evidence and automated checks are recorded in the Atlas verification document.
