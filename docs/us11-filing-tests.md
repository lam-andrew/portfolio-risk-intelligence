# US-11 — Filing ingestion and retrieval specifications

**Requirement:** FR-13 · **Story:** [US-11 / issue #11](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/11)
**Planned:** Sprint 3, 5 points, unchanged. **Early implementation:** September 19, 2026.
**Design:** ADR 0019 (ingestion) and ADR 0020 (retrieval staging).

## Acceptance boundary

Given a holding with a supported public corporate filer, ingestion retrieves and indexes
the latest 10-K, latest 10-Q and five latest 8-K primary documents present in SEC's recent
submissions list. This bounded first-release selection is explicitly visible to the user.
Amendments, exhibits, older archives and fund forms are excluded. No fabricated issuer
mapping, semantic search, embedding, LLM answer or full-history claim is permitted.

## Reproducible tests and traceability

### FI-01 — Parse, chunk and preserve source identity (unit)

- Preconditions: synthetic HTML with Item 1A heading, visible paragraphs, nested hidden
  blocks, script/style and inline-XBRL hidden content.
- Inputs: `BODY` in `backend/tests/test_filings.py`; 60 supplier-risk paragraphs.
- Steps: extract text/passages; slice normalized text with every returned offset.
- Expected output: nonempty overlapping passages no longer than 1,800 characters, exact
  offset/text equality, section label, and no script or hidden text. Thin text is rejected.
- Postcondition: pure operation, no network or persistence.
- Automation: `test_extraction_excludes_active_and_hidden_content_and_preserves_offsets`,
  `test_parser_handles_inline_text_entities_and_hidden_nested_elements`.
- Trace: FR-13 → US-11 → FI-01 → local pytest / CI result.

### FI-02 — Catalogue, downloads and index (system)

- Preconditions: signed-in user owns AAPL; test SEC contact; isolated database; synthetic
  provider returns one 10-K, one 10-Q and one 8-K with fixed accession/source URLs.
- Inputs: POST `/api/filings/AAPL/ingest` twice; process persisted job; GET status/search.
- Steps: queue, ingest, search `supplier`, repeat ingestion, compare counts/download calls.
- Expected: HTTP 202/idempotent queue, ready 3/3, three sources, matching passages with
  accurate accessions and URLs; repeating ingestion performs no extra downloads/duplicates.
- Postconditions: committed searchable corpus; second immediate refresh returns 429.
- Automation: `test_ingestion_search_deduplication_and_source_identity`.
- Trace: FR-13 → US-11 → FI-02 → local pytest / CI result.

### FI-03 — Partial failures and restart (system)

- Preconditions: same isolated corpus; one document download fails; another run has a
  persisted running job simulating process interruption.
- Inputs: 10-Q failure, retry with healthy provider; recover running jobs after lock acquisition.
- Steps: ingest, inspect 2/3 status, retry, then check resumed job and prior source availability.
- Expected: partial 2/3 then ready 3/3; only the missing document is downloaded on retry.
  Recovery requeues interrupted work. Catalogue failures retain all previously indexed sources.
- Postconditions: no partial filing/passages committed; source search remains usable.
- Automation: `test_partial_ingestion_retries_only_missing_document`,
  `test_interrupted_job_is_recovered_and_completed`, `test_refresh_failure_preserves_existing_sources`.
- Trace: FR-13 → US-11 → FI-03 → local pytest / CI result.

### FI-04 — Ownership and disabled/unsupported states (system)

- Preconditions: anonymous client, two distinct accounts, one owned AAPL/BND position.
- Inputs: read/search/ingest as anonymous and nonowner; delete holding; blank SEC contact;
  provider has no supported corporate match.
- Steps: attempt each route; queue unsupported ticker after enabling test configuration.
- Expected: 401 anonymous, 404 nonowner/deleted holding, 503 unconfigured ingestion,
  explicit unsupported status with no invented sources. No contact address returned in API.
- Postconditions: no unauthorized job or corpus access; shared documents are retained.
- Automation: ownership assertions in FI-02, `test_filing_reads_require_auth`,
  `test_filing_write_requires_auth`, `test_deletion_revokes_filing_access`,
  `test_unsupported_and_configuration`.
- Trace: FR-13 / FR-15 → US-11 → FI-04 → local pytest / CI result.

### FI-05 — External network boundaries (unit)

- Preconditions: HTTP mock transport, no real SEC traffic.
- Inputs: exact class-share mapping; >5 8-Ks; malformed/traversal primary-document path;
  403, redirect, 429/503 and oversized body responses.
- Steps: resolve issuer, select recent documents, request each failure case.
- Expected: exact normalized match; newest 1/1/5 selection; fixed SEC hosts; malformed path
  rejected; no redirected request; at most three transient attempts and one 403 attempt;
  bounded body size. Identifying header present, mapping cached within 24 hours.
- Postconditions: no external traffic, no provider response bodies exposed to users.
- Automation: `test_sec_mapping_and_selection_use_exact_issuer_and_bounded_forms`,
  `test_sec_retries_are_bounded_and_no_redirects`, `test_size_limit_and_host_allowlist`,
  `test_malicious_document_path_is_rejected`.
- Trace: FR-13 → US-11 → FI-05 → local pytest / CI result.

### FI-06 — PostgreSQL index and deployment lock (integration)

- Preconditions: disposable PostgreSQL 16 database migrated through 0005.
- Inputs: `APP_TEST_POSTGRES=1 pytest tests/test_filings_postgres.py`.
- Steps: ingest synthetic forms with partial failure/retry; search `suppliers manufacturing`
  through the actual API function; test SQL-like input; inspect GIN index; acquire same
  test advisory lock on two connections. Roll back test corpus transaction.
- Expected: stemmed matches for `Supplier`, correct source IDs, parameterized input,
  no SQL mutation, one lock owner. Upgrade and downgrade of 0005 succeed independently.
- Postconditions: corpus transaction rolled back. Migration state restored to head.
- Automation: both tests in `test_filings_postgres.py`; added to CI integration job.
- Trace: FR-13 → US-11 → FI-06 → PostgreSQL test / CI result.

### FI-07 — Screen behavior (frontend unit and controlled browser)

- Preconditions: owned holding, idle/running/ready/partial/unconfigured fixture responses.
- Inputs: select holding, Retrieve/Refresh, keyword query, status retry, switch holding
  while search is in flight.
- Steps: inspect stages/progress; follow displayed source metadata; search; switch holdings;
  exercise empty account and error states.
- Expected: progress equals server completed/total; disabled duplicate start; safe text
  rendering; sourced excerpts; honest no-match message; no stale search from previous
  holding. Existing sources stay visible after errors. Layout works at desktop/mobile widths.
- Postconditions: polling stops on terminal state/unmount; no live account changes in QA.
- Automation: `frontend/src/pages/FilingsPage.test.tsx` (nine cases).
- Trace: FR-13 → US-11 → FI-07 → Vitest and browser evidence.

### FI-08 — Live-provider UAT (pending)

- Preconditions: completed project inbox; `APP_SEC_CONTACT_EMAIL` configured locally;
  normal PostgreSQL/Compose worker; signed-in test account owns supported corporate ticker.
- Inputs: Retrieve filings; search a phrase visibly present in one selected filing.
- Steps: watch progress to terminal state; compare selected forms/dates/issuer against SEC;
  open a source and locate the exact excerpt; refresh after cooldown; restart worker mid-job
  and confirm resumption; separately try an unsupported holding.
- Expected: real traceable documents, accurate bounded coverage, matching source text,
  duplicates avoided, partial/unavailable states truthful, restart resumes.
- Postconditions: retain public cached corpus; record acceptance date and any limitations.
- Result: **Pending.** Synthetic tests and CI do not establish live SEC access or user acceptance.
- Trace: FR-13 → US-11 → FI-08 → reviewer/UAT result required before story Done.

## Evidence log

- September 19: backend Ruff lint/format and strict mypy passed; **228 tests passed**,
  two PostgreSQL-only tests skipped in the ordinary suite and passed separately.
- PostgreSQL 16: clean migrations through 0005, downgrade to 0004 and re-upgrade succeeded
  in a separate disposable local database. Both native database tests passed, including
  actual API search with stemming, parameterized SQL-like input and deployment lock exclusion.
- Frontend: **76 tests passed**; lint, Prettier, TypeScript and production build passed.
  The existing non-blocking Fast Refresh warning in `button.tsx` remains.
- Controlled browser: separate local API/database and synthetic SEC provider; queued →
  ready 3/3, three form/source entries, keyword search returned nine traceable passages;
  switching to BND cleared the old corpus and produced an explicit unsupported-filer state.
  Desktop and 390px mobile layouts inspected; measured mobile content width equaled viewport
  width. This fixture check uses an injected test identity; authentication isolation is
  covered by API tests, not claimed from this browser run. No live holdings were modified.
- Existing Starlette/httpx deprecation warnings remain. Synthetic fixtures make no SEC calls.
- Live SEC UAT remains pending project-contact configuration and external-provider access.
- Project-board access remains unavailable with the current token (`read:project` missing).
  Issue #11 remains open; no sprint, point estimate or board status was changed.
