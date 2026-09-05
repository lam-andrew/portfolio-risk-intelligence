# 0017. The API is namespaced under `/api`, so one origin can serve both

- **Status:** Accepted
- **Date:** 2026-09-05
- **Enables:** single-origin deployment (see the forthcoming deployment ADR)

## Context

Until now the frontend and the API ran on separate origins: the Vite dev server on
`:5173`, the API on `:8000`. Both mounted routes at the root of their own origin, so
nothing collided.

Preparing to deploy exposed two problems with keeping that arrangement.

**1. Path collisions.** The frontend has page routes at `/`, `/holdings`, `/correlation`,
`/concentration`, `/drawdown`, `/methodology` and `/signin`. The API owned `/holdings`
outright. Served from one origin, a browser navigating to `/holdings` is handed a JSON
array instead of the application. Only one path actually collided today, but the collision
is structural: any future top-level API route can silently shadow a page route, and the
failure appears in the browser rather than in a test.

**2. Cookies across origins.** The alternative — two deployed apps, as in development —
looks appealing because it matches the container diagram. On Fly.io those are
`orbit-api.fly.dev` and `orbit-web.fly.dev`. **`fly.dev` is on the Public Suffix List**, so
those are separate registrable domains and therefore *cross-site*, not merely
cross-origin. A `SameSite=Lax` cookie is not sent on cross-site requests, so the session
would simply never arrive and authentication would break.

The only ways to keep two origins are to weaken the cookie to `SameSite=None`, which gives
up the CSRF protection [ADR 0014](0014-authentication.md) deliberately chose, or to buy a
domain and use two subdomains of it, which are same-site. Neither is warranted to preserve
a topology that has no other benefit in production.

## Decision

**Mount the entire API under an `/api` prefix**, leaving the root namespace to the
frontend.

`api_router` carries `prefix="/api"`, so every route moves together and no individual
router has to know about it. The frontend's single `baseURL` carries the prefix, so no call
site changed. In production that base URL is the bare path `/api`, which the browser
resolves against whatever host serves the page — meaning the same build works on any
domain without rebuilding.

`/health` moved under the prefix too rather than being kept at the root as an
infrastructure exception. One namespace is easier to reason about than one-plus-a-special-case,
and the two probes that referenced it (the container healthcheck and the CI integration
job) are one line each.

## Consequences

**Accepted:**

- A one-off breaking change to the public contract. Acceptable now, when the only client is
  in this repository; it would be expensive later.
- 143 test call sites moved. Mechanical, and the suite proved the change.

**Gained:**

- Page routes and API routes can never collide, now or as either side grows.
- One origin in production, so the session cookie stays same-site and `SameSite=Lax`
  continues to hold with no weakening.
- No CORS in production at all, since there is no cross-origin request to permit. CORS
  configuration remains only for local development, where the two servers really are
  separate.
- A conventional, self-describing URL layout: `/api/*` is the contract, everything else is
  the application.

## Alternatives considered

**Rename the colliding frontend route** (`/holdings` to `/positions`). Rejected. It is a
one-line change that fixes today's collision and leaves the structural hazard in place: the
next top-level API route collides again, and nothing warns you.

**Serve the frontend at a subpath** such as `/app`. Rejected: it puts the ugliness in the
URLs users actually see, to protect an API namespace users never see.

**Two deployed apps with `SameSite=None`.** Rejected. It trades a real security property
for a topology that only benefits development, and development already keeps two servers.

**Two deployed apps under a purchased domain.** Not rejected on merit — two subdomains of
one domain are same-site, so this works. Deferred because it requires buying a domain to
solve a problem the prefix solves for free, and the prefix is worth having regardless.
