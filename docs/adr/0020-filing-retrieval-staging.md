# 0020. Full-text retrieval before hosted embeddings and generation

- **Status:** Accepted
- **Date:** 2026-09-19

## Context

US-11 requires an index for retrieval. US-12 separately requires grounded generated answers.
ADR 0002 selects pgvector and the project plans hosted embedding/generation providers, but
no model has yet been evaluated or configured. Source extraction and citation traceability
must be demonstrable independently of model quality, expense or credentials.

## Decision

US-11 uses PostgreSQL English full-text search over stored passages, with an expression
GIN index and parameterized plain-text queries. Return up to 20 ranked passages, each
with its source accession, filing date, section and original URL. This is keyword search,
not semantic retrieval or Q&A. SQLite unit tests use a simple substring fallback;
PostgreSQL integration tests exercise the actual index/query and migrations.

US-12 will add a separately evaluated hosted embedding adapter and pgvector columns,
then generation with passage IDs and server-resolved citations. ADR 0002 remains the
target vector-storage decision; this stages its use rather than replacing it. Do not
silently choose a paid provider, fabricate embeddings, or label indexed text as AI-ready
evidence of successful grounded generation. Record provider, model, vector dimensions,
embedding version, data handling and evaluation thresholds in a future ADR.

I/O and persistence live in the data/orchestration layer. The RAG engine's extraction
and chunking functions accept text and return plain structures. This follows ADR 0004
and clarifies the architecture document's older shorthand about the RAG engine performing
network calls. The risk engine and its API remain unchanged.

## Consequences

Ingestion and source search work without LLM credentials. Keyword search can miss
paraphrases and is not a substitute for the planned semantic search. The next story can
evaluate hybrid retrieval against this deterministic baseline. Embeddings must be rebuilt
when their model or chunking version changes. Citation existence alone will not prove
claim support; US-12 needs separate grounding and abstention evaluations.

## Alternatives Considered

- Select a hosted model immediately: couples ingestion acceptance to an unevaluated provider.
- Add local embeddings now: adds model/runtime downloads before assessing retrieval needs.
- Store documents without searchable passages: does not fulfill indexing for retrieval.

Source: [PostgreSQL full-text indexing](https://www.postgresql.org/docs/16/textsearch-tables.html).
