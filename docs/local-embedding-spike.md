# Local embedding experiment — October 2, 2026

Related story: [US-12 / FR-14](https://github.com/lam-andrew/portfolio-risk-intelligence/issues/12).
Decision: [proposed ADR 0024](adr/0024-local-embedding-homelab-prototype.md).
This is a technical feasibility experiment. US-12 remains open, Sprint 3 / eight points.

## Goal and boundary

Test a CPU-only embedding service suitable for the planned OptiPlex homelab, removing
filing preparation's dependency on Google's embedding quota. The existing app, live vector
index, Gemini configuration and homelab are unchanged. Gemini generation still has quotas.
No live questions or Gemini calls are needed for this experiment.

The user's read-only inspection reports an OptiPlex 7050 Micro with an i5-7500T, four CPU
cores, AVX2 and 16 GB RAM. The proposed dedicated guest has 2 vCPUs, 6 GiB RAM and 48 GiB
SSD space. Those are starting allocations, not measured full-stack requirements. Proxmox,
existing applications, Tailscale enrollment, deployment automation and backups are not
modified by this branch. Do not install the Orbit stack directly on the Proxmox host.

## Implementation

The separate `experiments/local_embeddings/compose.yaml` project runs one non-root ONNX
service with a read-only root filesystem and model volume, no published ports, and an
internal network. It holds one FP32 BGE-small-en-v1.5 model instance. The runtime uses one
CPU thread; Docker limits it to one CPU and 1 GiB RAM, with no additional swap allowance.
A nonblocking lock rejects concurrent inference with 503/Retry-After instead of growing a
queue. This does not yet implement interactive priority over background batches.

Artifact revision and SHA-256 digests are pinned in `download_model.py`. Provisioning is
an explicit network-enabled step; inference loads verified local files only. Model and
tokenizer total 133,804,886 bytes, excluding runtime/image overhead. No model weights,
public corpus exports, generated vectors or credentials belong in Git.

The service accepts at most four bounded texts, or one query. BGE query prefixes, CLS
pooling and L2 normalization follow the model card. Oversized token sequences are rejected.
The benchmark splits long source passages into overlapping 450-token windows while
retaining offsets into their original text. This is experimental windowing; production
storage, citation-offset composition and migration still need implementation and tests.

## Reproduction

From the repository root, with Docker running:

```bash
docker compose -f experiments/local_embeddings/compose.yaml run --rm --build provision
docker compose -f experiments/local_embeddings/compose.yaml up -d --build encoder
docker compose -f experiments/local_embeddings/compose.yaml exec -T encoder python -c \
  "import urllib.request; print(urllib.request.urlopen('http://localhost:8081/health').read().decode())"
```

The host does not expose port 8081. A client on the internal experiment network can call
`http://encoder:8081/embed` with `{"texts":["What are the supplier risks?"],"query":true}`.
The experiment has no user authentication and must never be publicly published; production
integration must call it through Orbit's authenticated API and private service network.

For the benchmark, supply a JSON array of public passage objects with `id` and `text`.
Use only one issuer at a time, at most 1,000 passages. Export from the local corpus with
read-only SQL into a git-ignored `.cache/` directory. Never export user/portfolio tables.
Then, using the runtime image built by Compose:

```bash
docker run --rm -i --network none --memory 1g --memory-swap 1g --cpus 1 \
  --pids-limit 64 --read-only --tmpfs /tmp:size=16m --cap-drop ALL \
  --security-opt no-new-privileges:true \
  -v orbit-embedding-spike_models:/models:ro \
  orbit-embedding-spike-encoder python benchmark.py \
  < .cache/embedding-spike/amd.json > .cache/embedding-spike/benchmark.json
```

The benchmark reports model load, corpus encoding, 15 sequential query/search samples,
process peak RSS and top source-window identifiers. Its three fixed diagnostic questions
are not independent labeled evaluation cases; do not interpret them as a recall score or
proof of financial-answer accuracy. Query timing includes embedding and in-memory exact
search, excluding HTTP, PostgreSQL retrieval and Gemini generation.

Stop the experiment when finished (the model volume is retained):

```bash
docker compose -f experiments/local_embeddings/compose.yaml down
```

## Verification

- 15 offline pytest cases pass: window coverage/source offsets, explicit overlength
  rejection, query-prefix length accounting, CLS normalization, invalid vectors,
  bounded inputs, artifact checksum rejection, HTTP validation/recovery and concurrency.
- Ruff lint/format and mypy checks of the four prototype modules pass. Mypy checks
  untyped bodies; this prototype check is not the backend's strict-mode gate.
- Runtime dependency audit: no known vulnerabilities reported on October 2.
- Real model downloaded and SHA-256 verified; internal HTTP health and query inference
  returned successfully, with 384 dimensions and unit-length normalization.
- Docker inspection confirmed the memory/CPU caps, healthy service, no published ports
  and an internal inference network.
- New CI job builds the experimental linux/amd64 test image and runs offline tests,
  lint/format, type checks and the runtime dependency audit. CI does not download the model;
  passing synthetic CI is not proof of real-model behavior on the OptiPlex.
- Existing backend/frontend implementation was not changed; their standard CI jobs remain.
- TestClient reports an upstream Starlette/httpx deprecation warning; tests still pass.

## Measurements

Completed on October 2 on Apple Silicon Docker (`linux/arm64`), one ONNX thread and a
one-CPU / 1-GiB container limit. This is **not** an OptiPlex benchmark.

- Input: 470 cached AMD passages, expanded into 500 windows; 30 passages required splitting.
- Model load, including artifact verification: 0.785 seconds (already downloaded files).
- Initial corpus encoding: 790.793 seconds (13 minutes 11 seconds), 0.632 windows/second.
- Fifteen sequential question-embedding + in-memory search samples: median 0.101 seconds;
  95th percentile 0.103 seconds. Three questions repeated five times; not a concurrency SLO.
- Peak benchmark-process RSS: 453.14 MiB. A sampled cgroup peak counter reached 513.73 MiB
  while running; that sample is not a final full-container peak. No OOM or swap allowance.
- Separate internal HTTP smoke measurement: ten repeated query-embedding requests,
  median 0.103 seconds and maximum 0.166 seconds. No database or generation latency included.
- GitHub linux/amd64 prototype, backend, frontend, integration and security checks passed
  for implementation commit `27e2749`; the real model remains locally tested on arm64 only.

Interpretation: interactive embedding looks promising, but single-CPU FP32 backfill is slow.
Preserve completed work, schedule bounded incremental preparation and evaluate quantization
before committing to full-corpus rebuild expectations. The target i5 may perform differently.
The full 20-case retrieval/grounding evaluation and target-host load test remain pending.

Manual inspection of three diagnostic rankings found supply-chain and export-control text
in the top results. The manufacturing query ranked a mixed third-party-IP/platform-components
passage first, so these results do not establish optimal ordering or accepted retrieval quality.
No model-generated answers, citation verification or abstention cases ran in this benchmark.
The raw output and source export remain in ignored local cache, not in the repository.

## Gates before switching the app

1. Benchmark the same pinned artifact on the proposed linux/amd64 VM; confirm steady and
   peak memory, cold startup, query latency and backfill behavior alongside other services.
2. Separate embedding and generation interfaces/configuration. Implement query priority and
   bounded backpressure; avoid local preparation failures consuming user question allowance.
3. Add reversible, versioned 384-dimensional storage and offset-aware window records.
   Keep the existing corpus and old index recoverable; never mix embedding spaces.
4. Run the [labeled 20-case evaluation](us12-live-evaluation.md), including paraphrases,
   numeric/time-period questions and unanswerable/adversarial inputs. Existing recall,
   grounding, citation and abstention targets continue to apply.
5. Expose useful source-search results during generation outages, with accurate quota/error
   messaging. Do not treat a service outage as evidence that a filing lacks an answer.
6. Accept/supersede the architecture decision only after evidence supports the switch;
   record deployment design separately before provisioning or publishing Orbit.
