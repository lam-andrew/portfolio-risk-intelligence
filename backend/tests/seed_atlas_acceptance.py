"""Explicit synthetic corpus for browser testing; refuses any other database."""

from datetime import UTC, date, datetime
from hashlib import sha256

from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import engine
from app.data.gemini import EMBEDDING_VERSION
from app.engines.rag.passages import PARSER_VERSION, extract_passages
from app.models import Filing, FilingPassage, FilingSync, PassageEmbedding
from tests.test_questions import QUOTE, VECTOR


def seed_atlas():
    if make_url(settings.database_url).database != "orbit_acceptance":
        raise RuntimeError("Only the disposable orbit_acceptance database is allowed")
    html = f"""<h1>Acceptance fixture — synthetic filing text</h1>
    <p>This document is fabricated for interface and API acceptance tests. It is not a real
    company's disclosure and is not investment evidence.</p>
    <h2>Item 1. Business</h2>
    <p>The example company designs and sells computing components. Its operations depend on
    manufacturing partners and distribution channels. This text exists solely to exercise the
    filing reader with safe, normalized text.</p>
    <h2>Item 1A. Risk factors</h2>
    <p>{QUOTE} The supplier is not named in this disclosure. A disruption in manufacturing
    capacity could delay product deliveries. Qualifying additional sources may require time and
    expense. These statements are synthetic test inputs.</p>
    <p>Demand can fluctuate with customer purchasing cycles. Inventory commitments may exceed
    demand, and operational interruptions may affect the availability of key products. These
    illustrative disclosures do not describe any actual issuer.</p>
    <h2>Item 7. Management discussion</h2>
    <p>The example company evaluates operational capacity, customer concentration and liquidity.
    This acceptance fixture contains no audited financial results. Refer to an actual SEC source
    before making any real-world interpretation.</p>"""
    text, passages = extract_passages(html)
    with Session(engine) as session:
        session.merge(
            FilingSync(
                ticker="AAPL",
                cik="0000000001",
                company="Synthetic acceptance issuer",
                status="ready",
                stage="Finished",
                completed=1,
                total=1,
                updated_at=datetime.now(UTC),
            )
        )
        accession = "0000000001-26-000001"
        if session.get(Filing, accession):
            return
        session.add(
            Filing(
                accession=accession,
                cik="0000000001",
                form="10-K",
                filed_on=date(2026, 9, 1),
                source_url="https://www.sec.gov/Archives/edgar/data/1/000000000126000001/example.htm",
                text=text,
                text_sha256=sha256(text.encode()).hexdigest(),
                parser_version=PARSER_VERSION,
                passage_count=len(passages),
                indexed_at=datetime.now(UTC),
            )
        )
        session.flush()
        for p in passages:
            row = FilingPassage(
                accession=accession,
                ordinal=p.ordinal,
                section=p.section,
                text=p.text,
                start_offset=p.start,
                end_offset=p.end,
            )
            session.add(row)
            session.flush()
            session.add(
                PassageEmbedding(passage_id=row.id, version=EMBEDDING_VERSION, vector=VECTOR)
            )
        session.commit()


if __name__ == "__main__":
    seed_atlas()
