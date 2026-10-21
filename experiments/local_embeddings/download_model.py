"""Provision a pinned, checksum-verified public model; never run during inference."""

import hashlib
import os
from pathlib import Path
from urllib.request import urlopen

REVISION = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
MODEL = "BAAI/bge-small-en-v1.5"
FILES = {
    "onnx/model.onnx": (
        133093490,
        "828e1496d7fabb79cfa4dcd84fa38625c0d3d21da474a00f08db0f559940cf35",
    ),
    "tokenizer.json": (
        711396,
        "d241a60d5e8f04cc1b2b3e9ef7a4921b27bf526d9f6050ab90f9267a1f9e5c66",
    ),
}


def verify(path: Path, size: int, digest: str) -> bool:
    if not path.is_file() or path.stat().st_size != size:
        return False
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest() == digest


def provision(root: Path) -> None:
    for name, (size, digest) in FILES.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if verify(target, size, digest):
            continue
        temporary = target.with_suffix(".partial")
        try:
            with (
                urlopen(
                    f"https://huggingface.co/{MODEL}/resolve/{REVISION}/{name}",
                    timeout=60,
                ) as response,
                temporary.open("wb") as output,
            ):
                written = 0
                while chunk := response.read(1024 * 1024):
                    written += len(chunk)
                    if written > size:
                        raise ValueError("Model artifact exceeded expected size")
                    output.write(chunk)
            if not verify(temporary, size, digest):
                raise ValueError("Model artifact failed checksum verification")
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    print(f"Verified {MODEL}@{REVISION}", flush=True)


if __name__ == "__main__":
    provision(Path(os.environ.get("MODEL_PATH", "/models")))
