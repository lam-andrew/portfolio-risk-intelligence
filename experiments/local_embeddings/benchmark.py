"""Read public passage JSON from stdin; never connects to Orbit's DB or Gemini.

Input: [{"id": ..., "text": ...}]. Output has timing, sizes and source IDs only.
This is a performance/smoke experiment, not a labeled retrieval-quality evaluation.
"""

import json
import os
import platform
import resource
import sys
import time
from pathlib import Path

import numpy as np

from model import VERSION, Encoder

QUESTIONS = [
    "What supply chain risks does the company disclose?",
    "How does the company depend on third-party manufacturing?",
    "What export restrictions affect the company?",
]


def main():
    rows = json.load(sys.stdin)
    if not rows or len(rows) > 1000:
        raise ValueError("Use one to 1000 public passages")
    threads = int(os.environ.get("EMBEDDING_THREADS", "1"))
    started = time.perf_counter()
    encoder = Encoder(Path(os.environ.get("MODEL_PATH", "/models")), threads)
    load_seconds = time.perf_counter() - started
    windows = []
    split_count = 0
    for row in rows:
        spans = encoder.windows(row["text"])
        split_count += len(spans) > 1
        for start, end in spans:
            windows.append(
                {
                    "id": row["id"],
                    "start": start,
                    "end": end,
                    "text": row["text"][start:end],
                }
            )
    started = time.perf_counter()
    vectors = []
    for offset in range(0, len(windows), 4):
        vectors.extend(encoder.embed([w["text"] for w in windows[offset : offset + 4]]))
    index_seconds = time.perf_counter() - started
    matrix = np.asarray(vectors, dtype=np.float32)
    samples, retrieved = [], []
    for question in QUESTIONS:
        for repetition in range(5):
            started = time.perf_counter()
            vector = encoder.embed([question], query=True)[0]
            scores = matrix @ vector
            best = np.argsort(-scores)[:8]
            samples.append(time.perf_counter() - started)
            if repetition == 0:
                retrieved.append(
                    {
                        "question": question,
                        "top_windows": [
                            {k: windows[i][k] for k in ("id", "start", "end")}
                            for i in best
                        ],
                    }
                )
    print(
        json.dumps(
            {
                "version": VERSION,
                "architecture": platform.machine(),
                "threads": threads,
                "passages": len(rows),
                "windows": len(windows),
                "split_passages": split_count,
                "load_seconds": load_seconds,
                "index_seconds": index_seconds,
                "windows_per_second": len(windows) / index_seconds,
                "query_samples": len(samples),
                "query_p50_seconds": float(np.median(samples)),
                "query_p95_seconds": float(np.percentile(samples, 95)),
                "process_peak_rss_mib": resource.getrusage(
                    resource.RUSAGE_SELF
                ).ru_maxrss
                / 1024,
                "retrieval_smoke": retrieved,
                "quality_evaluation": "unlabeled; no recall or correctness claim",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
