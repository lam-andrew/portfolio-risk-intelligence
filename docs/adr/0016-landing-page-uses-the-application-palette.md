# 0016. The landing page uses the application palette; density carries the difference

- **Status:** Accepted
- **Supersedes:** [0015](0015-landing-page-visual-treatment.md)
- **Date:** 2026-09-05

## Context

ADR 0015 gave the landing page its own saturated violet treatment, on the reasoning that a
marketing surface has a different job from an analysis tool and should be free to be louder.

Seen against the running application, that reasoning did not survive contact. The landing
page looked like a **different product**. A visitor's first impression set an expectation of
deep violet and heavy glow, and signing in then delivered a calm blue-grey dashboard. The
gap read as two teams shipping two things, which is the opposite of what a first impression
should do.

The violet was also justified in 0015 by pointing at the logo mark, which gradiented from
the accent into `#7c5cff`. That was the only purple anywhere in the product, and leaning a
whole page on it inflated one incidental detail into an identity.

## Decision

**The landing page uses the application's palette. Density, not hue, carries the
difference.**

Every colour on the landing page resolves to an application token: `--background`,
`--surface`, `--border`, `--foreground`, `--muted-foreground`, `--faint`, and `--accent`.
There is no landing-specific palette, so a change to the app's theme moves the landing page
with it and the two cannot drift apart.

What still separates the two surfaces is everything except colour: larger type, a wider
grid, glow and motion, an orbital hero, oversized wordmark. A marketing page can be
expressive without being a different colour.

The purple was also removed from the logo mark itself, in the sidebar and on the sign-in
screen, so the product no longer contains it anywhere.

The `.landing` scope from 0015 is kept for structure — card treatment, glow, motion path
keyframes — but it now holds no colour definitions of its own.

## Consequences

**Accepted:**

- The landing page has less licence to be visually striking than 0015 allowed. Impact has
  to come from layout, motion and type rather than from a louder palette.
- Anything that genuinely needs a colour the app does not have would now require a token
  added to the app's theme, which is a deliberately higher bar.

**Gained:**

- One product, one identity. The transition from landing page to signed-in dashboard is
  continuous rather than a jolt.
- One palette to maintain. The two-visual-languages maintenance cost that 0015 explicitly
  accepted is gone.
- Retheming the app now retheme the landing page for free.

## Alternatives considered

**Keep the violet and restyle the app to match it.** Rejected. Saturated violet and heavy
glow behind a correlation heatmap or a drawdown chart competes with the data for attention,
and the data is the product. A risk dashboard should not be trying to impress the person
reading it.

**Keep both palettes and accept the seam.** Rejected: this is what 0015 did, and the seam
was the problem being solved.

## Retained from 0015

The content position stands and is restated here so it does not get lost when 0015 stops
being read: the design direction this page was modelled on draws much of its impact from
social proof — partner logos, user counts, a satisfaction statistic, a testimonial. None of
that exists honestly for this project, and fabricating it would misrepresent the product.
Those slots hold claims that are true and checkable instead. Anything added later should
clear the same bar.
