"""Persistence/orchestration for filings. The pure RAG engine has no I/O."""

import hashlib
from datetime import UTC, datetime

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.data.sec import SecClient, SecError, UnsupportedIssuer
from app.engines.rag.passages import PARSER_VERSION, extract_passages
from app.models import Filing, FilingPassage, FilingSync


def progress(session: Session, job: FilingSync, stage: str) -> None:
    job.stage = stage
    job.updated_at = datetime.now(UTC)
    session.commit()


def ingest(session: Session, job: FilingSync, provider: SecClient) -> None:
    job.status = "running"
    job.completed = job.total = 0
    job.message = None
    progress(session, job, "Finding company")
    try:
        cik, company = provider.issuer(job.ticker)
        job.cik, job.company = cik, company
        progress(session, job, "Finding filings")
        refs = provider.recent_filings(cik)
        job.total = len(refs)
        if not refs:
            raise UnsupportedIssuer("No 10-K, 10-Q or 8-K appears in the recent submissions list.")
        failures = 0
        for ref in refs:
            cached = session.get(Filing, ref.accession)
            if cached is not None and cached.cik != cik:
                raise SecError("Filing issuer does not match the selected company.")
            if cached is not None and cached.parser_version == PARSER_VERSION:
                job.completed += 1
                progress(session, job, "Using indexed filing")
                continue
            try:
                progress(session, job, f"Downloading {ref.form}")
                html = provider.document(ref)
                progress(session, job, f"Indexing {ref.form}")
                text, passages = extract_passages(html)
                if cached is None:
                    cached = Filing(accession=ref.accession)
                    session.add(cached)
                cached.cik, cached.form, cached.filed_on = cik, ref.form, ref.filed_on
                cached.source_url, cached.text = ref.source_url, text
                cached.text_sha256 = hashlib.sha256(text.encode()).hexdigest()
                cached.parser_version = PARSER_VERSION
                cached.passage_count = len(passages)
                cached.indexed_at = datetime.now(UTC)
                session.flush()
                session.execute(
                    delete(FilingPassage).where(FilingPassage.accession == ref.accession)
                )
                for p in passages:
                    session.add(
                        FilingPassage(
                            accession=ref.accession,
                            ordinal=p.ordinal,
                            section=p.section,
                            start_offset=p.start,
                            end_offset=p.end,
                            text=p.text,
                        )
                    )
                job.completed += 1
                progress(session, job, "Indexed filing")
            except (SecError, ValueError):
                session.rollback()
                failures += 1
        missing = sorted({"10-K", "10-Q", "8-K"} - {r.form for r in refs})
        job.status = "partial" if failures else "ready"
        if failures == len(refs):
            job.status = "failed"
        messages = []
        if failures:
            messages.append(f"{failures} selected filing(s) could not be indexed; retry later.")
        if missing:
            messages.append(f"Not present in recent submissions: {', '.join(missing)}.")
        job.message = " ".join(messages) or None
        progress(session, job, "Finished")
    except UnsupportedIssuer as exc:
        job.status, job.message = "unsupported", str(exc)
        progress(session, job, "Unavailable")
    except SecError as exc:
        job.status, job.message = "failed", str(exc)
        progress(session, job, "Stopped")
