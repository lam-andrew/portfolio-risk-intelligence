# 0029. Optional self-hosted answer generation on the owner's model server

- **Status:** Accepted; implemented as an option, Gemini remains the default. Live evaluation pending
- **Date:** 2026-10-23

## Context

Grounded questions (US-12, ADR 0022/0027) generate and verify answers with Gemini's free tier.
Orbit's own budgets (ten questions per account and twenty per deployment per UTC day, forty
generation calls) exist to stay inside that tier. They make the twenty-case evaluation take at
least two days and cap everyday use. Billing must stay disabled.

The owner has an NVIDIA GB10 machine ("the Spark") at home: 121 GiB of unified memory, CUDA 13,
and Ollama 0.40.8. On October 23 we ran a synthetic benchmark there (fictional company,
[record](../../experiments/local_generation/README.md)) against Orbit's unchanged answer/verify contract: same rules, strict
schemas, exact-quote provenance and independent support verification.

- `qwen3:30b-a3b` with thinking: **9/9** answerable and **7/7** unsupported or adversarial cases
  correct in three of three runs, median about 11 s per question, max about 29 s.
- `gpt-oss:20b` (low reasoning) answered a question about a different company with the
  selected company's facts, and its own verifier approved the answer.
- Two adapter details were essential. A status-first schema made both models abstain before
  drafting anything. Asked for both claims and a status, the models labelled correct cited
  claims `insufficient_evidence`.

## Decision

We add an optional answer generator, `APP_QA_PROVIDER=ollama`, behind the existing
`AnswerProvider` interface. Gemini stays the default, and embeddings are unchanged (ADR 0025).

- **Adapter:** Ollama's native `/api/chat` with `stream=false`, temperature 0, thinking on, and
  a JSON-schema `format`. Its schemas list `claims` first, and the answer schema has **no status
  field**: the adapter sets `answered` exactly when claims exist, which is the invariant
  `AnswerDraft` already enforces. Prompts reuse Gemini's rules, with "empty claims" in place of
  the status instruction. `message.thinking` is discarded and never evidence. Responses are
  size-bounded, never follow redirects, ignore proxy environment variables, and fail closed
  with sanitized errors.
- **Unchanged checks:** strict `AnswerDraft`/`GroundingVerdict` validation, `citations_match`,
  `support_passes`, post-I/O source rechecks, retrieval scope and the conversation rules all
  apply to both generators.
- **Model:** `APP_OLLAMA_MODEL` defaults to `qwen3:30b-a3b`. A different model needs its own
  benchmark and evaluation.
- **Network:** the model server is reachable only over the owner's Tailscale network. A tailnet
  rule allows only the Orbit VM (and the development Mac) to reach its port. Ollama has no
  authentication, so it is never exposed on the LAN or the internet.
- **Limits:** the per-account, per-deployment and generation daily limits become settings. Their
  defaults are today's Gemini-safe values, and a deployment using the local generator may raise
  them. Spacing between questions remains.
- **Disclosure:** the question-status API reports which generator is active (an additive
  field), and the UI states where questions go. Gemini keeps its Google free-tier notice. The
  local generator says questions and public excerpts are processed on the deployment owner's
  model server and are not sent to an outside AI service.
- **Evaluation:** the US-12 live evaluation runs against the generator selected for production
  and records its model name and digest.

## Consequences

- Everyday questions and the evaluation no longer depend on Gemini's free-tier quota, and
  questions stay on owner-controlled hardware.
- Answers are slower (about 11–29 s in the benchmark) and depend on the Spark being on and
  reachable. When it isn't, questions fail with a service error and risk analysis is unaffected.
- The owner must run the model server: Tailscale, Ollama bound to the tailnet address, the
  access rule, model updates and power.
- The synthetic benchmark isn't the US-12 acceptance gate. The frozen real-filing evaluation is
  still required.
- A future model or Ollama change can change behaviour, so the model is pinned by name and its
  digest is recorded with each evaluation.

## Alternatives Considered

- **Stay on Gemini only:** the simplest option, but it keeps the daily cap and sends questions to Google.
- **OpenAI-compatible `/v1/chat/completions` on Ollama:** portable, but thinking control and
  JSON-schema formatting are less direct than the native endpoint we benchmarked. The interface
  boundary keeps this switch cheap later.
- **vLLM or NVIDIA NIM:** higher throughput, but more setup on an Arm machine for one user.
  Revisit if concurrency matters.
- **`gpt-oss:20b`:** faster, but it failed the cross-company refusal case in the benchmark.
- **Also moving embeddings to the Spark:** the pinned CPU encoder already works next to the
  database. Not needed now.
