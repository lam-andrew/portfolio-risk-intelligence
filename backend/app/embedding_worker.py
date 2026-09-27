"""Container entry point for model preparation; independent of the SEC worker."""

import time

from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.data.filing_embeddings import prepare_batch
from app.data.model_budget import ModelLimitError
from app.data.question_factory import create_provider
from app.data.question_provider import ModelError

LOCK_ID = 8940012


def main() -> None:
    if not settings.qa_configured:
        print("Filing questions are disabled until a free-tier provider is configured.", flush=True)
        while True:
            time.sleep(30)
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as lock:
        if not lock.scalar(text("SELECT pg_try_advisory_lock(:key)"), {"key": LOCK_ID}):
            raise RuntimeError("Another embedding worker owns this database.")
        provider = create_provider()
        try:
            while True:
                lock.execute(text("SELECT 1"))
                try:
                    with SessionLocal() as session:
                        prepare_batch(session, provider)
                except (ModelError, ModelLimitError) as exc:
                    print(str(exc), flush=True)  # Sanitized messages only; never question/key.
                    time.sleep(60)
                time.sleep(30)
        finally:
            provider.close()


if __name__ == "__main__":
    main()
