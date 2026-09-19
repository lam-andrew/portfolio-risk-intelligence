"""Run one durable SEC worker: python -m app.filing_worker (ADR 0019)."""

import time

from sqlalchemy import text, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.data.filing_ingestion import ingest
from app.data.filing_schedule import next_job, schedule_due
from app.data.sec import SecClient
from app.models import FilingSync

LOCK_ID = 8940011


def recover_interrupted(session: Session) -> None:
    """Called only after the process acquires the deployment-wide advisory lock."""
    session.execute(
        update(FilingSync)
        .where(FilingSync.status == "running")
        .values(status="queued", stage="Resuming after restart")
    )
    session.commit()


def main() -> None:
    if not settings.sec_configured:
        print("SEC ingestion is disabled until APP_SEC_CONTACT_EMAIL is configured.", flush=True)
        # Stay idle so an unconfigured app continues to boot normally.
        while True:
            time.sleep(30)
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as lock:
        if not lock.scalar(text("SELECT pg_try_advisory_lock(:key)"), {"key": LOCK_ID}):
            raise RuntimeError("Another filing worker already owns this database queue.")

        def check_lock() -> None:
            # A broken connection raises; do not reconnect and continue without the lock.
            lock.execute(text("SELECT 1"))

        provider = SecClient(settings.sec_contact_email, before_request=check_lock)
        try:
            with SessionLocal() as session:
                recover_interrupted(session)
            next_scan = 0.0
            while True:
                check_lock()
                with SessionLocal() as session:
                    if time.monotonic() >= next_scan:
                        schedule_due(session)
                        next_scan = time.monotonic() + 30
                    job = next_job(session)
                    if job is not None:
                        ingest(session, job, provider)
                time.sleep(2)
        finally:
            provider.close()


if __name__ == "__main__":
    main()
