# Local answer generation benchmark — October 23, 2026

Evidence for [ADR 0029](../../docs/adr/0029-self-hosted-answer-generation.md). It's a
**synthetic** benchmark, not the US-12 acceptance gate: every passage describes a fictional
company. No Orbit data, keys or questions were used, and nothing left the owner's machine.

## Setup

- Model server: NVIDIA GB10 ("the Spark"), 121 GiB unified memory, CUDA 13, Ollama 0.40.8.
- Models: `qwen3:30b-a3b` (30.5B MoE, Q4_K_M, digest `ad815644918f`) and `gpt-oss:20b`
  (`f38aa0c53da5`).
- Contract: Orbit's Gemini system rules, answer/verify instructions, strict schemas,
  `citations_match` and `support_passes`, re-implemented in [`benchmark.py`](benchmark.py)
  with the standard library so it runs on the model server over stdin.
- Cases: 9 answerable and 7 unsupported or adversarial. The answerable cases cover supplier
  dependency, a paraphrase, geography, customer concentration, cybersecurity, two quarters of
  one metric kept apart, debt, and an 8-K event. The other seven are a forecast, advice, a
  secret, a future event, an instruction override, an instruction injected in a passage, and a
  different company.
- A case passes only if the full pipeline gives the expected result. Answerable cases must also
  cite the labelled passage and contain the labelled fact.

## Results

| Configuration | Answerable | Unsupported refused | Seconds per question (median / max) |
|---|---|---|---|
| **qwen3:30b-a3b, thinking** | **9/9** (3 of 3 runs) | **7/7** (3 of 3 runs) | 10.7–11.3 / 26–29 |
| qwen3:30b-a3b, no thinking | 4/9 | 7/7 | 0.4 / 7.3 |
| gpt-oss:20b, low reasoning | 9/9 | 6/7: answered the other-company case and the verifier approved it | 3.0 / 4.5 |
| gpt-oss:20b, medium reasoning | 6/9 | 7/7 | 8.6 / 13.9 |

**Real adapter check:** `app.data.ollama.OllamaAnswers` with Orbit's own validators, through a
temporary SSH tunnel: `qwen3:30b-a3b` scored **9/9** answerable and **7/7** refused, median 12.0 s,
max 19.6 s.

## Adapter findings (why ADR 0029's format differs from Gemini's)

1. With Orbit's status-first schema and constrained decoding, both models refused **every**
   case, answerable ones included, in under a second.
2. With claims first but a model-chosen status, models drafted correct cited claims and then
   labelled them `insufficient_evidence`. Orbit's strict validation rejected those.
3. Asking only for claims, and deriving the status as Orbit's `AnswerDraft` invariant already
   defines it, fixed both. Every safety check is unchanged.

The scores above are from the final configuration. Rounds 1–3 are recorded as findings, not as
model scores. Sixteen synthetic cases with one fictional issuer can't prove real-filing quality
or universal safety; the frozen 20-case live evaluation is still required.

Reproduce on a model server (synthetic data only):

```bash
ssh <user>@<spark> 'python3 - qwen3:30b-a3b true' < experiments/local_generation/benchmark.py
```
