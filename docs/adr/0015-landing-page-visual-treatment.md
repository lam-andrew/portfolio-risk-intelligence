# 0015. The landing page runs its own visual treatment, scoped away from the app

- **Status:** Superseded by [0016](0016-landing-page-uses-the-application-palette.md)
- **Date:** 2026-09-05
- **Relates to:** [0009](0009-ui-styling-tailwind-shadcn-tremor.md) (Tailwind + shadcn/ui,
  which remains in force for the application), [0013](0013-hand-authored-charts.md)

## Context

US-20 added a public landing page. Until then every surface in the product was the
application itself, so one design system covered everything: a restrained dark palette with
a blue accent, chosen so that the *data* is the loudest thing on screen. That is the right
instinct for a risk dashboard, where a saturated interface competing with a chart actively
harms comprehension.

A landing page has the opposite job. Nobody arrives at it already convinced. It has to
establish what the product is and feel worth signing up for, and a marketing surface styled
with the same deliberate restraint as an analysis tool reads as unfinished rather than calm.

Three options were considered.

## Decision

**Give the landing page a richer, more saturated treatment, scoped entirely under a
`.landing` class so none of it reaches the application.**

The palette is deep violet with heavy glow. That colour is not invented for the occasion:
the application's own logo mark already gradients from the accent into `#7c5cff`, so the
landing page saturates a colour the brand already owns rather than introducing a second
identity.

Everything the page needs — palette, card treatment, glow, orbital keyframes — is defined
under `.landing` in `index.css`. The application's semantic tokens are untouched, so there
is no path by which a marketing style leaks into a risk dashboard.

Motion is CSS-only and disabled wholesale under `prefers-reduced-motion`. The orbital
diagram is hand-authored SVG, consistent with ADR 0013.

## Consequences

**Accepted:**

- Two visual languages exist in one codebase, which is a real maintenance cost. A change to
  the brand now has two places to land rather than one.
- The `.landing` scope is a convention, enforced by review rather than by tooling. Nothing
  mechanically prevents a future contributor from lifting a `lp-` class into the app.

**Gained:**

- The app stays calm and data-first; the marketing surface can be expressive. Neither
  compromises for the other.
- Because the divergence is scoped and deliberate rather than accidental drift, a future
  reader finds a recorded reason instead of an inconsistency.

## Alternatives considered

**Style the landing page with the application's existing tokens.** Rejected. It was the
first attempt, and the result was accurate, readable, and forgettable. The tokens are tuned
to keep the interface quiet behind data, which is precisely wrong for a page whose entire
purpose is to make a case.

**Restyle the whole product to the richer palette.** Rejected, and it would have been the
worse mistake. Heavy glow and saturated violet behind a correlation heatmap or a drawdown
chart fights the data for attention, and the risk figures are the product. A dashboard
should not be trying to impress the person reading it.

**Introduce a separate marketing site.** Rejected as disproportionate. It would mean a
second deployable, a second build, and a duplicated brand definition, all to serve one page
in a solo capstone project.

## Note on content

One decision recorded here because it is easy to reverse by accident. The visual direction
this page was modelled on derives much of its impact from social proof: partner logos, user
counts, a satisfaction statistic, a testimonial. None of those exist honestly for this
project, and fabricating them would misrepresent the product. The equivalent slots are
filled with statements that are true and checkable — the brokerage export formats the CSV
parser genuinely handles, and counts of what the software actually does. Anything added to
this page later should clear the same bar.
