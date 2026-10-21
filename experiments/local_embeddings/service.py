"""Private encoder: one inference at a time, one bounded priority-query waiter."""

import os
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from threading import Condition

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, StrictBool, field_validator

from model import VERSION, Encoder


class InferenceGate:
    def __init__(self):
        self.condition = Condition()
        self.active = False
        self.query_waiting = False

    @contextmanager
    def claim(self, query=False, timeout=10):
        with self.condition:
            if self.query_waiting or (self.active and not query):
                raise HTTPException(
                    503, "Embedding service is busy", headers={"Retry-After": "1"}
                )
            if self.active:
                self.query_waiting = True
                try:
                    if not self.condition.wait_for(
                        lambda: not self.active, timeout=timeout
                    ):
                        raise HTTPException(
                            503,
                            "Embedding service is busy",
                            headers={"Retry-After": "1"},
                        )
                finally:
                    self.query_waiting = False
            self.active = True
        try:
            yield
        finally:
            with self.condition:
                self.active = False
                self.condition.notify_all()


class Request(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=4)
    query: StrictBool = False

    @field_validator("texts")
    @classmethod
    def bounded_texts(cls, texts: list[str]) -> list[str]:
        if any(not t.strip() or len(t) > 8192 for t in texts):
            raise ValueError("Expected nonempty texts of at most 8192 characters")
        return texts


class WindowRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8192)


def create_app(encoder=None) -> FastAPI:
    gate = InferenceGate()

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
        with gate.claim(query=body.query):
            try:
                vectors = app.state.encoder.embed(body.texts, body.query)
                return {"version": VERSION, "vectors": vectors}
            except ValueError as exc:
                raise HTTPException(422, "Input exceeds embedding limits") from exc

    @app.post("/windows")
    def windows(body: WindowRequest):
        with gate.claim():
            try:
                return {
                    "version": VERSION,
                    "windows": app.state.encoder.windows(body.text),
                }
            except ValueError as exc:
                raise HTTPException(422, "Input exceeds embedding limits") from exc

    return app


app = create_app()
