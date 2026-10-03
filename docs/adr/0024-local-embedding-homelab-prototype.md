# 0024. Evaluate CPU-only local embeddings for the homelab

- **Status:** Proposed — isolated prototype; application migration and host benchmark pending
- **Date:** 2026-10-02
- **Related work:** US-12 / FR-14, issue #12. Sprint 3 / eight points unchanged.

## Context

On October 2, background Gemini embedding requests received provider 429 responses.
The resulting shared ten-minute embedding cooldown blocked Andrew's first interactive
question before generation. A better error message cannot remove that shared external
dependency. Andrew requested exploration of local embeddings and supplied a read-only
homelab inspection: OptiPlex 7050 Micro, i5-7500T (four cores), 16 GB RAM, SATA SSD,
Proxmox with an existing application VM. AVX2 is available; GPU access is not provisioned.
The inspection recommends a separate Orbit VM with 2 vCPUs, 6 GiB RAM and 48 GiB disk.
Those allocations are estimates, not measured Orbit capacity or provisioned resources.

## Decision

Build an isolated technical prototype before replacing ADR 0022's live model adapter.
Evaluate BAAI/bge-small-en-v1.5 with ONNX Runtime on CPU, a pinned upstream revision and
SHA-256 verification of the tokenizer and model artifacts. Use the published FP32 ONNX
artifact first; quantization is a later experiment, not an assumed quality improvement.

The experimental Compose project has no connection to the application database, no provider
keys, no published ports, and an internal inference network. A separate explicit setup
operation downloads approximately 134 MB of model/tokenizer artifacts to a named volume;
inference mounts it read-only and performs no downloads. One service process holds one
model instance. Start with one runtime thread, a one-CPU limit, 1 GiB RAM without swap,
one active request and batches of at most four texts. Busy requests receive 503 instead
of building an unbounded inference queue. Interactive priority is a future integration gate,
not implemented by this prototype's nonblocking lock.

Use CLS pooling and L2 normalization, following the model's instructions. Queries receive
the model's retrieval prefix; documents do not. Reject inputs exceeding 512 tokens.
The benchmark splits source passages into 450-token windows with 32-token overlap, preserving
character offsets into the original text. It never silently truncates long filing passages.
The version identity includes model revision, dimensions, pooling and window policy.

The proposed integrated design splits embedding and generation interfaces. The API and
worker share the internal embedding service; PostgreSQL retains the corpus and vectors;
Gemini remains the external answer/verifier provider. The risk engine stays isolated.
This would change the 768-dimensional schema to support a separately versioned 384-dimensional
index, with a reversible migration and no mixing of old/new vectors. No schema change is
part of this experiment. Do not mark ADR 0022 superseded until the replacement is adopted.

## Consequences

- Local embeddings remove the external embedding quota, not Gemini generation quotas.
- CPU/memory use moves onto the host and competes with other services. Initial backfill
  must be bounded and resumable; prioritize queries, and cache completed work.
- Smaller models and shorter windows can change retrieval quality. Evaluate the existing
  labeled 20-case runbook before acceptance; throughput alone is not sufficient.
- Local measurements on Apple Silicon Docker are not OptiPlex performance results.
  The same container must be built/tested for linux/amd64 and benchmarked on the target VM.
- The homelab is the intended hosting destination. Provisioning, ingress, registry access,
  production configuration, migration recovery and recurring off-host backups remain pending.
  ADR 0008's deferred deployment automation remains in effect. Do not reuse another
  application's database volume or deployment credentials without verifying access.
- Source-search fallback and clearer quota errors remain integration work. The running app
  continues using its current provider until migration and acceptance checks pass.

## Alternatives Considered

- Throttle Gemini background work only: useful mitigation, but preserves dependence on its
  embedding quota and availability.
- Pay for hosted embeddings: possible later, but does not meet the present no-billing preference.
- Host a conversational LLM too: materially different memory/latency/quality requirements;
  unnecessary for evaluating retrieval and not selected.
- Load the model in each API/worker process: duplicates resident memory on a small host.
- Quantize immediately: defer until the FP32 baseline provides a quality/performance reference.

Sources: [BGE model and usage](https://huggingface.co/BAAI/bge-small-en-v1.5),
[ONNX runtime guidance](https://sbert.net/docs/sentence_transformer/usage/efficiency.html),
[Google quota guidance](https://ai.google.dev/gemini-api/docs/rate-limits).
Reproduction and results: [local embedding experiment](../local-embedding-spike.md).
