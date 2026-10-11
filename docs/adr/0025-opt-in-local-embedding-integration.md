# 0025. Opt-in local retrieval embeddings with independent answer generation

- **Status:** Proposed for release; opt-in integration implemented, quality and target-host gates pending
- **Date:** 2026-10-10
- **Story:** US-12 / FR-14, issue #12; Sprint 3 / eight points unchanged
- **Builds on:** ADRs 0001–0004, 0010, 0020, 0022 and 0024

## Context

The October 2 prototype established a bounded CPU encoder and measured it on Apple Silicon.
Hosted embedding quotas prevented reliable filing preparation. The user requested continuing
this work after the Week 7 assessment. The OptiPlex inspection supports evaluating a separate
2-vCPU / 6-GiB VM, but it does not establish target performance or authorize provisioning.

## Decision

Implement an opt-in local embedding path, preserving the default Gemini path and original
index. This integrates the ADR 0024 candidate; it does not declare it accepted for production.

- Separate `EmbeddingProvider` and `AnswerProvider`. The API composes the two; the preparation
  worker only constructs the embedding adapter. Local preparation requires no Gemini key.
  Generation and support verification still use the existing Gemini adapter, free-tier key
  and shared budgets. There is no automatic provider, paid-tier or remote-embedding fallback.
- Keep one CPU encoder behind internal HTTP, with no published port. The API and worker
  share it; neither loads ONNX nor a tokenizer. Model files remain revision/checksum pinned,
  explicitly provisioned into a volume and mounted read-only for inference. The optional
  Compose overlay bounds the encoder to one CPU and 1 GiB including swap allowance, a
  read-only filesystem and a private network. This is a development overlay, not a complete
  hardened homelab deployment: the base stack still publishes API/database development ports.
- `/windows` returns tokenizer-aware character ranges; `/embed` encodes at most four slices.
  The client requires the exact expected model revision, window policy and 384-dimensional
  unit vectors, validates full non-whitespace source coverage, bounds response bytes, and
  rejects redirects and malformed responses. Credentials and external proxy settings are
  not sent to the encoder. No silent truncation or model-version substitution is allowed.
- One active inference/tokenization operation is allowed. One query can wait up to ten
  seconds for the current batch; queued queries take priority over subsequent background
  requests. Additional work receives 503 and Retry-After. Current work is not preempted.
  Client timeouts and the server's eight-request concurrency cap keep pressure bounded.
- Migration 0008 adds `local_passage_windows`, separate from `passage_embeddings` (768).
  Each row includes parent passage ID, version, ordinal, character offsets and `vector(384)`.
  All windows for one passage are committed atomically after rechecking source text and
  tracking membership. Missing passages form a resumable queue; source deletion cascades.
  A batch prepares one passage, using at most four windows per encoder request. The existing
  database advisory lock admits one preparation worker. Successful local work pauses 250 ms;
  idle/error work pauses 30 seconds. Hosted preparation retains its prior cadence/budgets.
- Readiness counts distinct parent passages, not windows. Exact cosine retrieval is filtered
  by issuer and model version, then ranks each parent passage by its best window and returns
  at most eight distinct original passages. Evidence uses the original passage IDs/text;
  citations retain the original source offsets. Windowing therefore changes retrieval,
  not the public citation contract or the pure grounding validators.
- Encode and retrieve before reserving a user's question allowance. Preparation/search
  failures therefore consume no question allowance. Hosted embedding calls still have their
  independent budget. Generation attempts retain existing limits and failure accounting.
  Busy/unavailable services return errors rather than an insufficient-evidence answer.

## Rollback and consequences

Omit the local overlay and recreate API/worker to restore the Gemini embedding path. The
old 768-dimensional index is untouched; readiness depends on that index's actual coverage.
Leave migration 0008 installed for a reversible provider switch. Explicit schema downgrade
removes only the new local windows and would require rebuilding them on the next opt-in.

Local preparation and query encoding no longer consume Google embedding requests. Answer
and verification requests still consume generation quota, so this change does not promise
unlimited Q&A. Existing authenticated keyword source search remains available during model
outages. Better fallback presentation, query caching and target-host tuning remain future work.

Storing windows alongside the original index costs additional disk. Exact ranking may become
expensive as the corpus grows; an approximate index is deliberately deferred until measured.
Ranking full parent passages by a window needs evaluation, especially for dates, figures and
similar repeated filing language. Automated tests cannot establish semantic retrieval quality.

## Release gates

1. Native PostgreSQL migration, ranking, version/issuer isolation, cascade and rollback checks.
2. Service/adapter validation, failure recovery, priority scheduling, atomic/resumable worker
   behavior and authenticated answer/citation regression tests.
3. The labeled 20-case evaluation in `us12-live-evaluation.md`, using the local index, including
   retrieval recall and adversarial/unsupported abstention. No acceptance claimed until measured.
4. OptiPlex Linux/amd64 runtime/resource benchmark under representative concurrent load.
5. Separate homelab deployment, private ingress, secrets and backup/restore work.

No core Risk & Exposure behavior, sprint assignment, estimate, story acceptance or deployment
status changes. The implementation date is October 10; it is not backdated into the assessment.

## Alternatives considered

- Replace the existing vector column in place: destroys the reversible provider path and
  mixes incompatible dimensions. A separate window table retains both versions safely.
- Load the model independently in API and worker: duplicates memory on the small host.
- Queue unbounded work: increases memory and interactive latency; bounded admission and
  one priority waiter make overload explicit.
- Finish a full local generator now: exceeds the measured homelab capacity evidence and
  changes the answer-model evaluation scope. Generation remains behind its own adapter.
