"""CPU-only BGE spike. Token windows retain offsets into unchanged source passages."""

from pathlib import Path

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

from download_model import FILES, MODEL, REVISION, verify

VERSION = f"{MODEL}@{REVISION}:384:cls-l2:window450-overlap32:v1"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


class Encoder:
    def __init__(self, root: Path, threads: int = 1):
        if threads not in (1, 2):
            raise ValueError("Prototype supports one or two CPU threads")
        if not all(verify(root / name, *spec) for name, spec in FILES.items()):
            raise ValueError("Provision the verified model before starting inference")
        self.tokenizer = Tokenizer.from_file(str(root / "tokenizer.json"))
        self.tokenizer.no_truncation()
        self.tokenizer.no_padding()
        options = ort.SessionOptions()
        options.intra_op_num_threads = threads
        options.inter_op_num_threads = 1
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        self.session = ort.InferenceSession(
            str(root / "onnx/model.onnx"), options, providers=["CPUExecutionProvider"]
        )

    def windows(self, text: str) -> list[tuple[int, int]]:
        """No silent truncation: make overlapping windows at source token boundaries."""
        encoding = self.tokenizer.encode(text, add_special_tokens=False)
        offsets = encoding.offsets
        if not offsets:
            raise ValueError("Text contains no usable tokens")
        result = []
        for start in range(0, len(offsets), 418):
            stop = min(start + 450, len(offsets))
            result.append((offsets[start][0], offsets[stop - 1][1]))
            if stop == len(offsets):
                break
        return result

    def embed(self, texts: list[str], query: bool = False) -> list[list[float]]:
        if not 1 <= len(texts) <= 4 or any(
            not t.strip() or len(t) > 8192 for t in texts
        ):
            raise ValueError("Expected one to four nonempty bounded texts")
        if query and len(texts) != 1:
            raise ValueError("Queries must be embedded individually")
        encoded = self.tokenizer.encode_batch(
            [QUERY_PREFIX + text if query else text for text in texts]
        )
        if any(len(item.ids) > 512 for item in encoded):
            raise ValueError("Text exceeds 512 tokens; split passages before embedding")
        length = max(len(item.ids) for item in encoded)
        ids = np.array(
            [e.ids + [0] * (length - len(e.ids)) for e in encoded], dtype=np.int64
        )
        mask = np.array(
            [[1] * len(e.ids) + [0] * (length - len(e.ids)) for e in encoded],
            dtype=np.int64,
        )
        inputs = {
            "input_ids": ids,
            "attention_mask": mask,
            "token_type_ids": np.zeros_like(ids),
        }
        output = self.session.run(
            None, {i.name: inputs[i.name] for i in self.session.get_inputs()}
        )
        # BGE uses the CLS token, not mean pooling; normalize for cosine retrieval.
        vectors = output[0][:, 0, :]
        if vectors.shape != (len(texts), 384) or not np.isfinite(vectors).all():
            raise ValueError("Invalid model output")
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        if not np.isfinite(norms).all() or (norms <= 0).any():
            raise ValueError("Invalid zero vector")
        return (vectors / norms).tolist()
