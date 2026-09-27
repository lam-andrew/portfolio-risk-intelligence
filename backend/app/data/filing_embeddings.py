"""Durable, resumable embedding preparation and issuer-filtered retrieval."""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.data.filing_schedule import tracked_tickers
from app.data.model_budget import ModelLimitError, pause, reserve
from app.data.question_provider import ModelError, QuestionProvider
from app.engines.rag.grounding import Evidence
from app.models import Filing, FilingPassage, FilingSync, PassageEmbedding


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


def coverage(session: Session, cik: str, version: str) -> tuple[int, int]:
    total, ready = session.execute(
        select(func.count(FilingPassage.id), func.count(PassageEmbedding.passage_id))
        .join(Filing, Filing.accession == FilingPassage.accession)
        .outerjoin(
            PassageEmbedding,
            and_(
                PassageEmbedding.passage_id == FilingPassage.id, PassageEmbedding.version == version
            ),
        )
        .where(Filing.cik == cik)
    ).one()
    return total, ready


def prepare_batch(session: Session, provider: QuestionProvider) -> int:
    """One batch; missing rows are the queue. Called only by the lock-owning worker."""
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
    session: Session, cik: str, version: str, vector: Sequence[float]
) -> list[SourcePassage]:
    """Rank only this issuer/version. Exact cosine ranking avoids ANN filtering losses."""
    query = (
        select(FilingPassage, Filing)
        .join(Filing, Filing.accession == FilingPassage.accession)
        .join(PassageEmbedding, PassageEmbedding.passage_id == FilingPassage.id)
        .where(Filing.cik == cik, PassageEmbedding.version == version)
    )
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
