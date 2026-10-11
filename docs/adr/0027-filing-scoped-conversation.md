# 0027. Filing-scoped reader and bounded conversational questions

- Status: Proposed implementation; security/contract tests pass, live model evaluation pending
- Date: 2026-10-10
- Tracking: US-11 #11, US-12 #12, Atlas #93
- Updates: ADR 0022's single-turn UI and data disclosure. No change to the provider decision.

## Context

Atlas requires a specific filing reader and optional contextual chat. The existing issuer-wide
endpoint cannot truthfully support a “This filing only” label. The owner explicitly requested
server-enforced scope and follow-ups as part of this redesign.

## Decision

Add authenticated document routes under `/api/filings/{ticker}/documents/{accession}`.
Every reader/readiness/question request checks current holding/watch membership and resolves
that ticker's CIK against the stored filing. Return indistinguishable 404s for mismatched or
inaccessible filings. Reader responses contain safe normalized passage text, never SEC HTML.
Pages contain at most 40 passages, ordered by ordinal, with stable passage IDs and global
character offsets. `passage_id` locates the appropriate page after the same authorization and
accession check. The UI labels these indexed passages; original layout/exhibits are not reproduced.

Readiness counts only the selected accession's passages for the configured embedding version.
Retrieval applies CIK, accession and version predicates **before** native pgvector ranking.
Keep at most eight freshly retrieved passages, exact-quote checks, independent support
verification, server-resolved SEC URLs, abstention and all existing model budgets. The legacy
issuer endpoint remains compatible but is not used by the Atlas chat.

Each question includes the document's SHA-256 `revision` and zero to three prior exchanges.
Each exchange has that same accession, a 5–1000-character question and a 1–1500-character
answer. Combined history is capped at 6000 characters. Reject extra fields, mismatched
accessions, oversize history and stale revisions before invoking a model. History is untrusted
context, **never evidence**. Generation and verification receive labeled JSON context. Query
embedding combines the current question, the latest previous question and at most 100 answer
characters; the current question is preserved and the adapter's 2200-character limit respected.
This deterministic context expansion avoids another model call. Its semantic effectiveness
must be measured during the live evaluation; no quality claim follows from offline tests.

After provider I/O, recheck membership, the login session, document revision and every
retrieved passage's text/offsets. Reject replaced sources or revoked access rather than
return stale citations. No conversation database/schema, hosted corpus, model switch, paid
fallback or automatic question retries are introduced. All application services remain
containerized and provider access remains backend-only.

The client retains up to 20 exchanges in component memory, transmits at most three (answers
trimmed to 1000 characters to remain within the aggregate bound), and preserves draft/reader
position when chat closes. Filing/account changes unmount and abort requests, clearing context.
Reloads clear history. No transcript enters localStorage, logs or the application database.
The provider's `store: false` setting remains; Google's free-tier data-use terms still apply.
The disclosure now explicitly includes limited prior conversation as well as the question
and public excerpts; no account details or position quantities are attached.

## Consequences and alternatives

Independent desktop scrolling and full-screen mobile chat require explicit focus management,
software-viewport sizing and citation-to-reader navigation. A citation page can be fetched
without loading a whole large document. Pagination may temporarily display noncontiguous
passages after a citation jump; ordinal labels and loaded counts remain explicit.

Issuer-wide retrieval with a filing badge is rejected as false scoping. Unbounded browser
history or provider-side conversations would expand retention and cost. A persistent chat
service is unnecessary. Client-supplied passage IDs are never accepted as answer evidence.

This PR builds on the hosted-provider branch through the Atlas UI stack. Open local-embedding
PR #98 is a separate unmerged branch: its `retrieve_local`/coverage path must receive equivalent
accession filtering and native integration tests when that branch is reconciled. Do not merge
these branches by taking one side of the questions module wholesale. Neither provider readiness
nor US-12 acceptance is declared complete by this redesign.
