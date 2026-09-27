# US-12 / FR-14 — Grounded filing question specifications and results

Implementation date: September 26, 2026 (early; Sprint 3 and eight points unchanged).
Story: [#12](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/12).
Decision: [ADR 0022](adr/0022-grounded-filing-questions.md).
Status: implementation under review; offline checks passed; live evaluation and UAT pending.

## Reproduction

Backend: `cd backend && pytest`. Frontend: `cd frontend && npm test`.
Provider tests use `httpx.MockTransport`; no credentials, real documents or network calls.
SQLite system tests create an authenticated owner, another account, two public issuers,
synthetic passages and deterministic fake vectors. They test software contracts, not LLM quality.

For native tests, use a **disposable** migrated PostgreSQL 16/pgvector database, then run
`APP_TEST_POSTGRES=1 pytest tests/test_questions_postgres.py tests/test_filings_postgres.py`.
Never use production for this opt-in suite. CI runs it in its disposable Compose database.

## Requirements traceability and executable specifications

All cases below trace to US-12 / FR-14, with AR-1/AR-2 and FR-15 where stated.
The linked test functions contain exact inputs, assertions and synthetic fixtures.

### QA-01 — Answer and citation provenance (AC1), automated, passed

Precondition: caller watches AAPL; AAPL has a prepared passage stating reliance on a single
supplier; an untracked issuer has different text. Ask about supplier risks through POST
`/api/filings/AAPL/questions`. Expect an answered response with the AAPL accession,
unchanged quotation, date, section, SEC URL and exact normalized-text offsets. Verify only
AAPL evidence reached generation. Postcondition: no question history or holdings mutation.
Implementation: `test_answer_links_exact_evidence_for_only_selected_company` in
[API tests](../backend/tests/test_questions.py).

### QA-02 — Abstention and unsupported claims (AC2), automated, passed

Use the same prepared corpus; separately return an explicit provider abstention, an invented
passage ID and a false support verdict. Ask the same question. Every response must have
`insufficient_evidence`, no claims and no citations. Invalid IDs must not trigger verification.
Pure tests also reject changed quotations, duplicate IDs, incomplete/duplicate claim verdicts,
whitespace claims and inconsistent answer status. See [grounding tests](../backend/tests/test_grounding.py)
and the parametrized withholding case in API tests. This proves enforcement of verdicts,
not that a real model always judges support correctly.

### QA-03 — Authentication and current membership (FR-15), automated, passed

Request status and questions signed out (401); ask about an untracked company (404); sign
in as another account and request AAPL (404). Provider-call count must stay zero. Remove
AAPL's watch while the fake provider is answering: the final response must be 404 even though
remote work already began. See ownership and revocation cases in API tests.

### QA-04 — Validation, readiness and service errors, automated, passed

Submit whitespace or 1,001 characters (422, no model calls). Remove matching-version
embeddings (409, readiness false). Disable Q&A (503), then confirm cached sources still load.
Inject provider outage (503) and quota failure (429): neither may return an evidence-abstention
payload. Immediately repeat a successful question: 429, without extra provider calls.

### QA-05 — Portable cache and worker recovery (AR-1), automated, passed

Delete synthetic embeddings; run one preparation batch. Only the tracked issuer is prepared.
Run again: zero work and no duplicate vectors. A changed embedding version has zero ready
passages. Remove tracking: no future batch starts. Simulate quota failure: no partial vector
batch is committed and missing rows remain resumable. See API tests and native tests below.

### QA-06 — Provider boundary and hostile responses, automated, passed

[HTTP adapter tests](../backend/tests/test_gemini.py) check fixed HTTPS host, header-only key,
separate vectors, 768 dimensions, task prefixes, finite/nonzero normalized values, no tools,
`store=false`, untrusted data outside system instructions and bounded output. Inject 301, 401,
403, 429, 500, timeout, oversized JSON, missing fields and incomplete generation. Expect a
sanitized error, no redirects, no retries and no raw provider diagnostics/key in the message.

### QA-07 — Actual PostgreSQL behavior (AR-1), automated, passed

[Native tests](../backend/tests/test_questions_postgres.py): persist 768-dimensional vectors;
rank matching issuer/version by cosine distance; exclude a different issuer and old version;
delete a passage and assert vector cascade. Race two budget reservations with a one-call cap:
exactly one succeeds. Acquire the worker advisory lock from two connections: only one succeeds.
Migration 0007 upgrade, downgrade to 0006 and re-upgrade were executed in `orbit_us12_test`.

### QA-08 — User workflow, automated, passed

[Frontend tests](../frontend/src/components/FilingQuestions.test.tsx): show 3/12 preparation,
disable unavailable questions, submit a ready question, display claim/quote/source, show
abstention without links, distinguish service errors and permit retry, discard a previous
company's in-flight response after switching, and render script markup as inert text.

## September 26 execution results

- Backend full regression: **293 passed**, seven native tests skipped in the ordinary suite.
- Native PostgreSQL integration: **7 passed** (four existing filing tests, three US-12 tests).
- Frontend full regression: **89 passed**; production build passed.
- Focused US-12 offline backend checks: **49 passed**, included in the full total.
- Backend lint/strict types and frontend types/lint passed; the pre-existing button-component
  Fast Refresh warning remains. Dependency audit results are reported with the PR checks.
- No risk-engine implementation files changed. Offline provider substitution exercises the
  same API contract; a second live provider is not implemented or claimed.

## Live quality evaluation and acceptance — NOT EXECUTED

A configured billing-disabled Gemini project is required. Synthetic HTTP tests cannot verify
model availability, real quota, retrieval recall, entailment, prompt-injection resistance or
latency. Do not mark the story Done from these tests alone.

Andrew owns final acceptance after model setup and review. Before acceptance, label at least
20 questions against retained real filings: answerable factual questions, paraphrases,
numeric/time-period distinctions, unanswerable questions, advice requests and injected
instructions. Store evaluation metadata and results without committing SEC corpus text,
credentials or private questions. For each item record ticker/accession/passage IDs, expected
support or abstention, retrieved IDs, model/version, outcome, claim-support judgments and
elapsed time. Manually open every cited source and compare its quotation.

Proposed gates from ADR 0022: at least 90% retrieval recall@8 and supported-claim precision
on answerable items, 100% valid citation provenance, 100% abstention on labeled unsupported,
advice and injection cases. Report numerators and denominators separately; no aggregate
success rate may hide an unsupported answer. Failures require corrective work and a fresh
run before acceptance. A passing small evaluation does not guarantee universal correctness.

Browser UAT remains pending for live answers, quota recovery and visual confirmation of
real citation passages. Until then the branch/PR is a reviewable implementation, not an
accepted release.

## Additional handoff verification — September 26

The API test suite also checks invalid/non-SEC source URLs, a verifier outage or quota
failure after generation (no unverified draft escapes), source replacement during an
embedding call (no stale vector is saved), and a durable ten-minute provider pause followed
by recovery. These eight cases extend QA-01/04/05/06. The containerized backend regression now
passes **301 tests**, with seven native tests skipped in the ordinary suite. Ruff lint,
format checks and strict mypy also pass. No application behavior or dependencies changed
in this follow-up; the earlier frontend/native results remain applicable.

Live setup and operational limits: [API-key guide](qa-setup.md). The
[20-case runbook](us12-live-evaluation.md) defines label preparation, mixed case classes,
quota-aware execution and metric denominators. It remains **not executed**.

## First live activation and REST adapter correction — September 26, 2026

Andrew confirmed that the locally saved key belongs to a Free-tier project with billing
not set up. Enabled the ignored local configuration and recreated backend/embedding-worker.
Google billing state is user-confirmed, not independently inspectable by Orbit.

The first live generation response exposed a contract error: `output_text` is an SDK
convenience property, while REST returns `steps[].content[]` in a `model_output` step.
Both initial diagnostic attempts were rejected with a sanitized service error; neither
was accepted as an answer. Corrected in `7cdc4aa`. The parser now requires completed status,
one final text output and the existing strict answer/verdict schemas. Thought steps are
ignored; tool steps, multiple outputs and malformed content fail closed. Synthetic adapter
fixtures now match the documented REST envelope instead of inventing an SDK response.
Source: [Interactions REST response](https://ai.google.dev/api/interactions-api).

Container checks after correction: Ruff lint/format and strict mypy pass;
**316 backend tests pass**, seven PostgreSQL-only cases skipped in this ordinary run.
The 15 additional cases cover valid split text, thought exclusion and malformed/unexpected
response structures. Native database and frontend behavior were not changed by this fix;
CI checks those separately. Existing Starlette/httpx warning remains.

Two bounded **provider-adapter smoke checks** then passed using one already cached public
AMD 10-Q passage (accession `0000002488-26-000123`, filed August 5, 2026). The factual case
identified TSMC's role for microprocessor/GPU wafers at 7 nm or smaller nodes, returned an
exact source quotation and passed the separate support check. Manual comparison confirmed
the claim matches the supplied excerpt. The future stock-price request returned
`insufficient_evidence` with no claims. Five generation calls in total were reserved in
the normal persistent daily budget, including the two failed diagnostics. No automatic
retry, paid fallback, quota reset or private account/portfolio payload was used.

Preparation persisted **112 of 6,522 passages** before a real provider quota response paused
embedding work. The worker's existing ten-minute backoff is active; it will try again
without resetting budgets. This proves initial embedding success and the pause path, not
quota recovery or full corpus readiness. Browser checks show the provider is enabled and
company preparation counters are present. An enabled provider does not bypass preparation.

These smoke checks supply known evidence directly to the adapter: they do **not** exercise
authenticated question routing, semantic retrieval, complete-company readiness or source-link
navigation. They are not counted toward the 20-case evaluation. Full evaluation and user
acceptance remain pending. Raw local evidence stays under ignored `data/cache/us12-evaluation/`;
no cached filing text, credentials, thought signatures or private questions are committed.
