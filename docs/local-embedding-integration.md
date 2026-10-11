# Local embedding integration — US-12

Implementation: October 10, 2026. See [ADR 0025](adr/0025-opt-in-local-embedding-integration.md).
This is an opt-in development path. Homelab deployment and model-quality acceptance remain
pending. The [October 2 prototype measurements](local-embedding-spike.md) are Apple Silicon
measurements, not evidence of OptiPlex performance.

## What changes

Filing preparation and question embeddings run in a private CPU encoder container. The
worker resumes from missing passages, writes all windows for a passage together and shares
a single model with the API. Queries get priority after the current background batch.
Existing filing text, citations, access controls and Gemini embeddings are preserved.
Gemini still generates and verifies answers, and its free generation quota still applies.

## Try the opt-in path

Use the integration branch and an existing ignored `.env`. Do not put credentials in this
document or pass them as command arguments. Set `APP_QA_ENABLED=true`; a Gemini key is
needed for answers but **not** for local preparation. Keep billing disabled.

From the repository root:

```bash
# Explicit download of the revision/checksum-pinned public model (~134 MB).
docker compose -f docker-compose.yml -f docker-compose.local-embeddings.yml run --rm --build provision-encoder
# Apply migration 0008 and start the shared encoder, API and preparation worker.
docker compose -f docker-compose.yml -f docker-compose.local-embeddings.yml up -d --build backend embedding-worker
```

The overlay selects `APP_EMBEDDING_PROVIDER=local` and the internal encoder URL. It removes
the Gemini key from the embedding worker. Normal `docker compose` remains the hosted default.
The inference container cannot download anything; a missing/incompatible model fails startup.
The encoder has no host port. The **base development stack** still publishes API/database
ports: do not treat this overlay as a production ingress/security configuration.

Open SEC filings, select a held/watched company and check preparation counts. Counts refer
to original passages; one passage may produce several internal vectors. Ask a question after
all indexed passages for the company are ready. Returned citations should still open the
original SEC filing and quote its text. A full backfill can take time on a small CPU.

For rollback, omit the overlay and recreate API/worker:

```bash
docker compose up -d --build --force-recreate backend embedding-worker
```

The unused encoder can be stopped with the overlay's `stop encoder` command. Keep both model
and database volumes; no volume deletion or schema downgrade is needed. The old hosted index
is retained, but may be incomplete and still subject to its original preparation quotas.

## Failure behavior

- Encoder busy: one question may wait up to ten seconds for the active batch; further work
  gets a bounded service error. Retry later. Background work resumes after its cooldown.
- Encoder unavailable, wrong version, malformed vectors or incomplete windows: reject the
  result. No partial passage is marked prepared and no user allowance is consumed by a
  failed query embedding/search step.
- Source replaced or no longer tracked during preparation: discard that result.
- Generator quota/outage: answer generation still returns a service error. Existing source
  search and indexed filings remain available; an outage is never presented as no evidence.

## Validation and remaining gates

Automated coverage is in `backend/tests/test_local_embeddings.py`, the extended
`backend/tests/test_questions_postgres.py`, and `experiments/local_embeddings/tests/test_spike.py`.
Tests include HTTP contracts, source-window coverage, malformed responses, worker restart,
source changes, tracking removal, index preservation, query priority, exact ranking and
citation provenance. Run the backend suite and native PostgreSQL tests on a disposable DB.

The 20-case live retrieval/grounding evaluation, OptiPlex benchmark and user acceptance remain
open. This implementation does not provision a VM, enable billing, switch the current preview
or mark US-12 complete. No dependency was added to the backend; ONNX stays in the encoder image.

### Recorded checks — October 10

Implementation commit `b46ca75`, [CI run 38108993349](https://github.com/lam-andrew/portfolio-risk-intelligence/actions/runs/38108993349)
and [Security run 38108993369](https://github.com/lam-andrew/portfolio-risk-intelligence/actions/runs/38108993369):

- Backend container: **349 passed, 8 skipped** (native PostgreSQL cases run separately);
  Ruff lint/format and strict mypy passed.
- Native PostgreSQL: **8 passed**, including 384-dimensional window ranking, issuer/version
  isolation, distinct-parent coverage, old-index preservation and deletion cascade.
- Encoder: **18 passed**, lint/format/type checks passed, Linux/amd64 image built in CI.
- Frontend regression on this stacked branch: **89 passed**, lint/type/format/build passed.
  The separate UI refresh branch has additional tests; it is not included in this branch.
- Security jobs passed. Local encoder/runtime and backend dependency audits found no known
  vulnerabilities; the local `orbit-backend` project itself is not a PyPI dependency to audit.
- Disposable PostgreSQL migration: upgrade through 0008 → downgrade to 0007 → re-upgrade
  succeeded. No live database was migrated.
- A separately executed **real local encoder smoke passed** (`test_local_encoder_live.py`):
  HTTP windowing/embedding → preparation → retrieval → authenticated cited response, with a
  deterministic answer/verifier stub and no Google requests. This is one synthetic passage,
  not a real-filing retrieval-quality score or a live Gemini answer evaluation.
- Runtime inspection confirmed a read-only encoder, no published ports, 1 CPU, 1 GiB memory
  and no extra swap allowance. Smoke ran on this Apple Silicon Docker host, not the OptiPlex.

The real-encoder test is opt-in (`APP_TEST_LOCAL_ENCODER=1` and
`APP_LOCAL_EMBEDDING_URL` pointing at the private provisioned encoder). Normal CI skips it
so routine tests do not download models or call external APIs. This adds one explicit skip
in subsequent default backend suite runs. The draft integration is tracked in [PR #98](https://github.com/lam-andrew/portfolio-risk-intelligence/pull/98), stacked on prototype PR #96.

A final budget preflight rejects known cooldowns/daily exhaustion before query encoding,
while actual reservations still occur after successful retrieval. This avoids wasting CPU
or hosted embedding quota on already-limited requests without charging preparation failures.
The regression includes exhaustion and next-day recovery.
