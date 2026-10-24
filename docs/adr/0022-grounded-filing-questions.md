# 0022. Portable grounded filing questions with a free-tier model adapter

- **Status:** Proposed — implementation and offline verification in progress; live model evaluation pending
- **Date:** 2026-09-26
- **Story:** US-12 / FR-14, issue #12; early implementation, Sprint 3 / eight points unchanged

## Context

US-11 provides a public, traceable filing corpus. US-12 adds natural-language answers
and must abstain when evidence is insufficient. Andrew requested a capable free option
and reaffirmed the existing portability and isolation constraints. A model's fluent answer
or a valid-looking citation alone cannot establish factual support.

## Decision

Preserve ADRs 0001–0004, 0007, 0010, 0014, 0017 and 0019–0021:

- FastAPI remains the authenticated entry point under `/api`. React renders text and
  server-resolved citations. The Risk engine is unchanged. Pure RAG validators import no
  database, HTTP, model SDK or sibling engine.
- Keep filing text, passage offsets, embeddings and request budgets in PostgreSQL 16.
  Alembic migration 0007 adds versioned `vector(768)` rows with passage deletion cascade.
  SQLite JSON vectors are test-only, never a production replacement for pgvector.
- Run an embedding worker using the existing backend Docker image, alongside the SEC
  worker. Both run through Compose; there is no managed Google database, hosted file-search
  index, cloud queue, cloud identity service, machine-specific model installation or GPU.
  A session advisory lock admits one embedding worker per database. Missing embeddings
  form a resumable queue; completed batches survive restarts. Only globally held/watched
  issuers are prepared. Removing the last tracking relationship stops future batches.
- Model I/O implements `QuestionProvider` in the data layer. Initial candidate:
  Gemini Developer API, `gemini-3.8-flash` for answer generation and independent support
  checking, and `gemini-embedding-2` for retrieval. These are initial evaluation choices,
  not a claim that they are the best model for this corpus.
- Use 768 normalized dimensions and version
  `gemini-embedding-2:768:qa-prefix-v1:html-text-v1`. Documents use the documented
  title/text prefix and queries use the question-answering prefix. Changing provider,
  embedding model, dimensions, prefix or parser requires a new version and re-embedding;
  incompatible vectors are never mixed. Another provider requires an adapter and its
  evaluation, plus configuration; the API, UI and risk calculations need no redesign.
- Rank the selected issuer's matching-version vectors by exact cosine distance, returning
  at most eight passages. This implements ADR 0020's staged semantic retrieval. Approximate
  vector indexes from ADR 0002's target are deferred until corpus scale warrants them;
  filtering a global approximate result set can lose an issuer's relevant passages. The
  existing GIN keyword-search index and its public endpoint remain available independently.
- Require all currently indexed passages for that issuer to have matching embeddings before
  answering. Show actual prepared/total counts. This is preparation completeness for the
  bounded cached corpus, not completeness of the company's disclosures.
- Generate at most six claims, each with one to three exact quotations and passage IDs.
  Reject missing IDs, changed quotations, empty claims and invalid output. Ask the model
  separately whether every claim is entailed by its evidence and answers the question.
  Require complete, unique affirmative verdicts. Resolve URLs, dates, accession and normalized
  text offsets on the server. Never accept model-supplied URLs. Otherwise return an explicit
  insufficient-evidence response. Provider errors remain service errors, not negative evidence.
- Treat questions and filing text as untrusted data. Supply no tools, external search or
  executable content. Prompt both generation and verification to reject advice, forecasts,
  instructions embedded in evidence and unsupported knowledge. These are mitigations,
  not a guarantee of factual correctness or resistance to every prompt injection.

### Free operation and data handling

Keep `APP_QA_ENABLED=false` by default; credentials and selection come from environment
variables. Use an AI Studio project with billing disabled. Orbit cannot determine a key's
billing tier from a generation response, and setting a local flag cannot enforce Google's
billing policy. Verify the project tier before enabling it. Never enable paid billing or
switch to a paid fallback automatically.

Embedding batches have at most 16 texts and run every 30 seconds. Database reservations
cap embedding calls at 200 per UTC day (including query embeddings), generation calls at
40, and questions at 20 globally / 10 per account, with 15-second global and 30-second
per-account spacing. These are conservative Orbit budgets, not advertised Google quotas.
Failures consume reservations. A provider 429 pauses that operation for ten minutes;
there are no automatic HTTP retries or fallback models. Google limits vary by project.

Only public passages, source labels and the user's explicit question go to the model;
Orbit does not attach email, account ID, holdings quantities, portfolio values or credentials.
The UI discloses that free-tier submissions may be used for Google's product improvement.
Do not enter confidential data. Use stateless Interactions requests with `store=false`;
this disables conversation storage, not the free-tier data-use terms. Orbit stores no
question/answer history. Budgets contain counters and an internal account identifier only.

## Consequences

All internal components remain containerized and deployable on another Docker host with
its environment variables and database backup. Inference still requires network access to
the selected external provider, as anticipated by ADR 0003; container portability does not
make that service locally hosted. A future self-hosted model can implement the same adapter
but requires resource planning and another ADR. Provider changes preserve the original
filings but require recomputing embeddings.

Free-tier quotas can delay preparation and demos. Two generation requests per supported
answer trade latency/quota for an additional check. Verification by the same model can
share the generator's errors: exact quotes prove provenance, not semantic correctness.
Live grounding and abstention evaluation and user acceptance remain release gates.
No requirement, sprint assignment, estimate, hosted deployment or story closure is changed.

## Evaluation gates

Offline tests must verify issuer isolation, exact quotes, invented IDs, unsupported claims,
missing verdicts, authentication, membership revocation, quota enforcement, malformed
responses and resumable preparation. Native PostgreSQL tests must exercise migration and
cosine retrieval. Frontend tests must cover preparation, cited answers, abstention and errors.
Before marking US-12 accepted, evaluate at least 20 labeled real-filing questions, including
answerable, unanswerable, numeric/time-period and adversarial cases. Target at least 90%
answerable retrieval recall@8 and supported-claim precision, 100% valid citation provenance,
and 100% abstention on the labeled unanswerable/advice/injection set. Report actual counts;
these are proposed acceptance thresholds, not measured results or universal guarantees.

## Alternatives Considered

- Google-managed file search/vector storage: undermines portable corpus ownership.
- Paid inference or paid quota fallback: conflicts with the user's free-only instruction.
- A local inference server now: portable but requires a model/runtime download and sufficient
  memory/compute; not assumed from the existing hosted-model architecture.
- Citation validation alone: real source IDs can accompany unsupported claims.
- Generate from keywords alone: can miss paraphrases; does not implement ADR 0020's planned
  semantic retrieval evaluation.

Sources checked September 26, 2026: [pricing](https://ai.google.dev/gemini-api/docs/pricing),
[embedding formats](https://ai.google.dev/gemini-api/docs/embeddings),
[structured output](https://ai.google.dev/gemini-api/docs/structured-output),
[stateless interactions](https://ai.google.dev/gemini-api/docs/interactions-overview),
[quota guidance](https://ai.google.dev/gemini-api/docs/rate-limits).
