"""Internal experiment, separate from the application Compose stack."""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, StrictBool, field_validator

from model import VERSION, Encoder


class Request(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=4)
    query: StrictBool = False

    @field_validator("texts")
    @classmethod
    def bounded_texts(cls, texts: list[str]) -> list[str]:
        if any(not t.strip() or len(t) > 8192 for t in texts):
            raise ValueError("Expected nonempty texts of at most 8192 characters")
        return texts


def create_app(encoder=None) -> FastAPI:
    gate = Lock()

    @asynccontextmanager
    async def lifespan(app):
        app.state.encoder = encoder or Encoder(
            Path(os.environ.get("MODEL_PATH", "/models")),
            int(os.environ.get("EMBEDDING_THREADS", "1")),
        )
        yield

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/health")
    def health():
        return {"status": "ready", "version": VERSION, "dimensions": 384}

    @app.post("/embed")
    def embed(body: Request):
        if not gate.acquire(blocking=False):
            raise HTTPException(
                503, "Embedding service is busy", headers={"Retry-After": "1"}
            )
        try:
            vectors = app.state.encoder.embed(body.texts, body.query)
            return {"version": VERSION, "vectors": vectors}
        except ValueError as exc:
            raise HTTPException(422, "Input exceeds embedding limits") from exc
        finally:
            gate.release()

    return app


app = create_app()
