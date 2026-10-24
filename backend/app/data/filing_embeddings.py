"""Durable, resumable embedding preparation and issuer-filtered retrieval."""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.data.filing_schedule import tracked_tickers
from app.data.local_embeddings import LOCAL_VERSION
from app.data.model_budget import ModelLimitError, pause, reserve
from app.data.question_provider import EmbeddingProvider, ModelError, SourceRejected
from app.engines.rag.grounding import Evidence
from app.models import Filing, FilingPassage, FilingSync, LocalPassageWindow, PassageEmbedding


@dataclass(frozen=True)
class SourcePassage:
    passage: FilingPassage
    filing: Filing

    def evidence(self, ticker: str) -> Evidence:
        return Evidence(
            self.passage.id,
            self.passage.text,
            f"{ticker} / CIK {self.filing.cik}: {self.filing.form} "
            f"filed {self.filing.filed_on}: {self.passage.section}",
        )


def coverage(
    session: Session, cik: str, version: str, *, accession: str | None = None
) -> tuple[int, int]:
    if version == LOCAL_VERSION:
        total = (
            session.scalar(
                select(func.count(FilingPassage.id))
                .join(Filing)
                .where(Filing.cik == cik, *([Filing.accession == accession] if accession else []))
            )
            or 0
        )
        ready = (
            session.scalar(
                select(func.count(func.distinct(LocalPassageWindow.passage_id)))
                .join(FilingPassage)
                .join(Filing)
                .where(
                    Filing.cik == cik,
                    LocalPassageWindow.version == version,
                    *([Filing.accession == accession] if accession else []),
                )
            )
            or 0
        )
        return total, ready
    total, ready = session.execute(
        select(func.count(FilingPassage.id), func.count(PassageEmbedding.passage_id))
        .join(Filing, Filing.accession == FilingPassage.accession)
        .outerjoin(
            PassageEmbedding,
            and_(
                PassageEmbedding.passage_id == FilingPassage.id, PassageEmbedding.version == version
            ),
        )
        .where(Filing.cik == cik, *([Filing.accession == accession] if accession else []))
    ).one()
    return total, ready


def prepare_batch(
    session: Session, provider: EmbeddingProvider, *, skip: set[int] | None = None
) -> int:
    """One batch; missing rows are the queue. Called only by the lock-owning worker.

    `skip` holds passages whose own text was rejected during this worker run, so one bad
    passage cannot stall the queue behind it; a restart retries them.
    """
    if provider.local_embeddings:
        return prepare_local_passage(session, provider, skip=skip)
    tracked_ciks = select(FilingSync.cik).where(FilingSync.ticker.in_(tracked_tickers()))
    rows = list(
        session.scalars(
            select(FilingPassage)
            .join(Filing)
            .outerjoin(
                PassageEmbedding,
                and_(
                    PassageEmbedding.passage_id == FilingPassage.id,
                    PassageEmbedding.version == provider.embedding_version,
                ),
            )
            .where(Filing.cik.in_(tracked_ciks), PassageEmbedding.passage_id.is_(None))
            .order_by(Filing.filed_on.desc(), FilingPassage.id)
            .limit(16)
        )
    )
    if not rows:
        return 0
    originals = [(row.id, row.text) for row in rows]
    reserve(session, "embeddings", daily=200, seconds=0)
    try:
        vectors = provider.embed([row.text for row in rows])
    except ModelLimitError:
        pause(session, "embeddings")
        raise
    if len(vectors) != len(rows):
        raise ModelError("Embedding batch was incomplete.")
    # Recheck after remote I/O: ingestion can replace a parser-versioned passage meanwhile.
    for (passage_id, original_text), vector in zip(originals, vectors, strict=True):
        current = session.scalar(
            select(FilingPassage)
            .where(FilingPassage.id == passage_id)
            .execution_options(populate_existing=True)
            .with_for_update()
        )
        if current is not None and current.text == original_text:
            session.merge(
                PassageEmbedding(
                    passage_id=passage_id, version=provider.embedding_version, vector=vector
                )
            )
    session.commit()
    return len(rows)


def retrieve(
    session: Session,
    cik: str,
    version: str,
    vector: Sequence[float],
    *,
    accession: str | None = None,
) -> list[SourcePassage]:
    """Rank only this issuer/version. Exact cosine ranking avoids ANN filtering losses."""
    if version == LOCAL_VERSION:
        return retrieve_local(session, cik, version, vector, accession=accession)
    query = (
        select(FilingPassage, Filing)
        .join(Filing, Filing.accession == FilingPassage.accession)
        .join(PassageEmbedding, PassageEmbedding.passage_id == FilingPassage.id)
        .where(Filing.cik == cik, PassageEmbedding.version == version)
    )
    if accession is not None:
        query = query.where(Filing.accession == accession)
    if session.get_bind().dialect.name == "postgresql":
        rows = session.execute(
            query.order_by(
                PassageEmbedding.vector.cosine_distance(list(vector)),
                Filing.filed_on.desc(),
                FilingPassage.id,
            ).limit(8)
        ).all()
        return [SourcePassage(p, f) for p, f in rows]
    # Offline SQLite tests only. The integration suite executes native pgvector above.
    rows_with_vectors = session.execute(query.add_columns(PassageEmbedding.vector)).all()
    q = np.asarray(vector)
    ranked = sorted(
        rows_with_vectors,
        key=lambda row: (
            -float(np.dot(q, row[2]) / (np.linalg.norm(q) * np.linalg.norm(row[2]))),
            -row[1].filed_on.toordinal(),
            row[0].id,
        ),
    )
    return [SourcePassage(p, f) for p, f, _ in ranked[:8]]


def prepare_local_passage(
    session: Session, provider: EmbeddingProvider, *, skip: set[int] | None = None
) -> int:
    """One bounded passage, all windows atomic; a restart resumes at the next missing row."""
    tracked_ciks = select(FilingSync.cik).where(FilingSync.ticker.in_(tracked_tickers()))
    already_prepared = select(LocalPassageWindow.passage_id).where(
        LocalPassageWindow.version == provider.embedding_version
    )
    passage = session.scalar(
        select(FilingPassage)
        .join(Filing)
        .where(
            Filing.cik.in_(tracked_ciks),
            FilingPassage.id.not_in(already_prepared),
            *([FilingPassage.id.not_in(skip)] if skip else []),
        )
        .order_by(Filing.filed_on.desc(), FilingPassage.id)
        .limit(1)
    )
    if passage is None:
        return 0
    passage_id, original_text = passage.id, passage.text
    # Release read transaction before CPU/HTTP work. No hosted budget or API key is needed.
    session.rollback()
    try:
        windows = provider.embed_passage(original_text)
    except SourceRejected as exc:
        if skip is None:
            raise
        skip.add(passage_id)
        raise SourceRejected(f"{exc} Passage {passage_id} set aside until restart.") from exc
    if not windows:
        raise ModelError("Local filing search returned no source windows.")
    current = session.scalar(
        select(FilingPassage)
        .join(Filing)
        .where(FilingPassage.id == passage_id, Filing.cik.in_(tracked_ciks))
        .execution_options(populate_existing=True)
        .with_for_update(of=FilingPassage)
    )
    if current is not None and current.text == original_text:
        session.add_all(
            [
                LocalPassageWindow(
                    passage_id=passage_id,
                    version=provider.embedding_version,
                    ordinal=i,
                    start_offset=window.start,
                    end_offset=window.end,
                    vector=window.vector,
                )
                for i, window in enumerate(windows)
            ]
        )
    session.commit()
    return 1


def retrieve_local(
    session: Session,
    cik: str,
    version: str,
    vector: Sequence[float],
    *,
    accession: str | None = None,
) -> list[SourcePassage]:
    """Rank each parent passage by its best window; return original source IDs and offsets."""
    if session.get_bind().dialect.name == "postgresql":
        ranked = (
            select(
                LocalPassageWindow.passage_id,
                func.min(LocalPassageWindow.vector.cosine_distance(list(vector))).label("distance"),
            )
            .join(FilingPassage)
            .join(Filing)
            .where(
                Filing.cik == cik,
                LocalPassageWindow.version == version,
                *([Filing.accession == accession] if accession else []),
            )
            .group_by(LocalPassageWindow.passage_id)
            .subquery()
        )
        rows = session.execute(
            select(FilingPassage, Filing)
            .join(Filing)
            .join(ranked, ranked.c.passage_id == FilingPassage.id)
            .order_by(ranked.c.distance, Filing.filed_on.desc(), FilingPassage.id)
            .limit(8)
        ).all()
        return [SourcePassage(p, f) for p, f in rows]
    rows_with_vectors = session.execute(
        select(FilingPassage, Filing, LocalPassageWindow.vector)
        .join(Filing)
        .join(LocalPassageWindow, LocalPassageWindow.passage_id == FilingPassage.id)
        .where(
            Filing.cik == cik,
            LocalPassageWindow.version == version,
            *([Filing.accession == accession] if accession else []),
        )
    ).all()
    q = np.asarray(vector)
    best: dict[int, tuple[float, FilingPassage, Filing]] = {}
    for passage, filing, values in rows_with_vectors:
        distance = -float(np.dot(q, values) / (np.linalg.norm(q) * np.linalg.norm(values)))
        if passage.id not in best or distance < best[passage.id][0]:
            best[passage.id] = (distance, passage, filing)
    ordered = sorted(
        best.values(), key=lambda row: (row[0], -row[2].filed_on.toordinal(), row[1].id)
    )
    return [SourcePassage(p, f) for _, p, f in ordered[:8]]
