# Orbit Atlas implementation verification — October 10, 2026

## Scope and provenance

Owner-authorized Atlas redesign, linked to #93, US-11 #11 and US-12 #12.
Read `IMPLEMENTATION-HANDOFF.md`, `manifest.json` and all 64 exported design previews.
Confirmed editable pen.dev source was the separate **Orbit** project: overview `wmTtL`,
reader `RwYwr`, conversation `L5Klvq`, mobile chat `N7ETB`; no Offscreen edits.
See ADR 0026 for appearance and ADR 0027 for the new document/conversation contract.

The visual branch builds on PR #94 (including merged acceptance PR #99), not main.
PR #100 contains the shared Atlas visual system. The dependent filing-chat PR adds the
reader/API, tests, evidence and browser-driven layout refinements. No merge or deployment
is claimed. Sprint assignments/estimates remain unchanged; US-12 is not Done.

## Automated verification

- Frontend: ESLint, Prettier, TypeScript, Vitest and production build. 117 tests passed.
  One existing `react-refresh/only-export-components` warning remains in `button.tsx`.
- Backend container (Python 3.12): Ruff lint/format, mypy and full pytest suite.
  336 passed; seven native-PostgreSQL cases skipped by the offline suite.
- Native PostgreSQL: all seven filing/question integration cases passed in a separate,
  freshly migrated `orbit_atlas_native` database. Includes accession filtering before
  pgvector ranking, issuer/version isolation and per-document coverage.
- Dependency audits: production npm audit found zero vulnerabilities; pip-audit found
  no known vulnerabilities (the local Orbit package is not a published PyPI package).
- `git diff --check` passed. Required remote CI/security checks are recorded on the PRs.

An initial native run accidentally shared the seeded browser-test corpus and hit fixture
accession collisions. It was rerun in the empty native-test database; no production data
was involved. Browser inspection also caught a Strict Mode canceled-request race causing
a stale error after successful loading; the fix has a dedicated regression test.

Commands: frontend `npm --prefix frontend run lint`, `run format:check`, `run typecheck`,
`test`, `run build` (repeat prefix); backend container `ruff check .`, `ruff format --check .`,
`mypy app`, `pytest`; native suite with `APP_TEST_POSTGRES=1` and the disposable database URL.
Local frontend checks used Node 24; CI uses the repository's Node 20 container.

## Browser evidence and exercised behavior

Screenshots are in [the evidence directory](evidence/atlas-2026-10-10/). All portfolio
numbers came through real authenticated APIs and the unchanged risk engine using the
repository's deterministic acceptance price provider. Filing text is explicitly marked
synthetic, and the isolated question provider supplies controlled responses. These are
integration/interaction tests, **not live Gemini quality evidence**. No real user's
portfolio, cached SEC corpus, credentials or API keys are committed.

Desktop 1440×1000 and narrow 390×844, both themes:

- Overview: proportional allocation, all history observations, drawdown, correlation and
  server-owned stress preview. Exact values remain available through chart controls.
- Holdings: mobile edit/save changed AAPL 300 → 310 and API values updated; restored 300.
  Added VTI 50 and completed its explicit delete confirmation. Stacked rows retain labels
  and controls. CSV import and validation/retry paths retain automated regression coverage.
- Correlation, concentration, drawdown, stress, SEC filings and methodology: data-loaded
  route checks, screenshots, no whole-page horizontal overflow. `route-sweep.json` records
  dimensions and visible states; dense matrices keep their own scroll region.
- Public landing, sign-in and account-creation form inspected in both themes; sign-out
  returns to the landing page and a fresh sign-in restores API-backed holdings. A forced
  market-data failure shows an explicit error, never empty holdings or zero measurements.
- Holding ticker → company → Open filing → reader with chat closed → explicit chat opening.
- Initial question → supported controlled answer → citation highlights the exact quote.
- “Does it name those suppliers?” → second answer with fresh selected-document evidence.
- Mobile chat fills the viewport. Citation returns to the reader with the cited passage
  focused. Escape/Back closes chat; reopening retains a draft and the current conversation.
- Composer remains within a 390×460 reduced viewport; this is a resize simulation, not
  evidence of an actual iOS/Android software keyboard.

Selected proof:

- [Desktop overview, dark](evidence/atlas-2026-10-10/overview-desktop-dark.png)
- [Desktop overview, light](evidence/atlas-2026-10-10/overview-desktop-light.png)
- [Mobile overview, dark](evidence/atlas-2026-10-10/overview-mobile-dark.png)
- [Mobile overview, light](evidence/atlas-2026-10-10/overview-mobile-light.png)
- [Desktop filing chat, dark](evidence/atlas-2026-10-10/chat-desktop-dark.png)
- [Desktop filing chat, light](evidence/atlas-2026-10-10/chat-desktop-light.png)
- [Mobile filing chat, dark](evidence/atlas-2026-10-10/chat-mobile-dark.png)
- [Mobile filing chat, light](evidence/atlas-2026-10-10/chat-mobile-light.png)

## Acceptance boundaries still open

- Owner review against Atlas and full mobile/assistive-technology UAT, including a real
  phone keyboard and screen reader. Browser resizing does not establish those results.
- Live grounded-Q&A evaluation under `us12-live-evaluation.md`, including contextual
  reference resolution and unsupported questions. No provider/model/budget change is made.
- Reconcile accession filtering with the separate unmerged local-embedding PR #98 before
  deploying the combined provider stack. Its local retrieval path is not in this branch.
- Required PR review, CI/security gates and dependency-stack integration before merge.
  Homelab deployment remains outside this implementation's completed evidence.

## Reproduce without production data

Start `ORBIT_ACCEPTANCE_CHAT=1 docker compose -f docker-compose.acceptance.yml up -d --build`
with `.acceptance/current.json` containing `{"profile":"overlap"}`. Create a disposable
account and holdings in this isolated app. Run `python -m tests.seed_atlas_acceptance` inside
its backend. The test-only entry point rejects a database not named `orbit_acceptance`;
production `app.main` cannot activate the controlled provider with this environment flag.
Use 127.0.0.1:5187 (UI) and 127.0.0.1:8087 (API), separate from the user's existing stack.
Native integration tests need a different empty disposable database, not the seeded corpus.
