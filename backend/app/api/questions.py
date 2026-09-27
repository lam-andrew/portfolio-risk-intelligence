"""Authenticated, single-turn questions over the selected issuer's indexed filings."""

from collections.abc import Iterator
from datetime import date
from typing import Annotated, Literal
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.api.auth import CurrentUser
from app.api.filings import COVERAGE, SessionDep, authorize
from app.core.config import settings
from app.data.filing_embeddings import coverage, retrieve
from app.data.model_budget import ModelLimitError, pause, reserve
from app.data.question_factory import create_provider, embedding_version
from app.data.question_provider import ModelError, QuestionProvider
from app.engines.rag.grounding import citations_match, support_passes
from app.models import FilingSync

router = APIRouter(prefix="/filings", tags=["filing questions"])
ABSTENTION = "I couldn't find enough supporting evidence in the retrieved filing passages."
LIMITATION = (
    "Answers use a limited selection of indexed filings and may miss relevant disclosures. "
    "Check the quoted passages, filing dates and original sources."
)


class QuestionInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    question: str = Field(min_length=5, max_length=1000)


class QuestionStatus(BaseModel):
    configured: bool
    total_passages: int
    ready_passages: int
    ready: bool


class Citation(BaseModel):
    passage_id: int
    accession: str
    form: str
    filed_on: date
    section: str
    quote: str
    source_url: str
    start_offset: int
    end_offset: int


class CitedClaim(BaseModel):
    text: str
    citations: list[Citation]


class QuestionAnswer(BaseModel):
    status: Literal["answered", "insufficient_evidence"]
    question: str
    claims: list[CitedClaim] = Field(default_factory=list)
    message: str
    coverage: str = COVERAGE
    limitation: str = LIMITATION


def get_question_provider() -> Iterator[QuestionProvider]:
    if not settings.qa_configured:
        raise HTTPException(status_code=503, detail="Filing questions are not configured yet.")
    provider = create_provider()
    try:
        yield provider
    finally:
        provider.close()


@router.get("/{ticker}/questions/status", response_model=QuestionStatus)
def question_status(ticker: str, user: CurrentUser, session: SessionDep) -> QuestionStatus:
    ticker = authorize(session, user.id, ticker)
    job = session.get(FilingSync, ticker)
    total, ready = coverage(session, job.cik, embedding_version()) if job and job.cik else (0, 0)
    return QuestionStatus(
        configured=settings.qa_configured,
        total_passages=total,
        ready_passages=ready,
        ready=settings.qa_configured and total > 0 and total == ready,
    )


@router.post("/{ticker}/questions", response_model=QuestionAnswer)
def ask_question(
    ticker: str,
    body: QuestionInput,
    user: CurrentUser,
    session: SessionDep,
    provider: Annotated[QuestionProvider, Depends(get_question_provider)],
) -> QuestionAnswer:
    ticker = authorize(session, user.id, ticker)
    job = session.get(FilingSync, ticker)
    if job is None or not job.cik:
        raise HTTPException(
            status_code=409, detail="No company filings are ready for questions yet."
        )
    total, ready = coverage(session, job.cik, provider.embedding_version)
    if not total or ready != total:
        raise HTTPException(
            status_code=409, detail="Filings are still being prepared for questions."
        )
    try:
        reserve(session, f"questions:user:{user.id}", daily=10, seconds=30)
        reserve(session, "questions", daily=20, seconds=15)
        reserve(session, "embeddings", daily=200, seconds=0)
        try:
            vector = provider.embed([body.question], query=True)[0]
        except ModelLimitError:
            pause(session, "embeddings")
            raise
        passages = retrieve(session, job.cik, provider.embedding_version, vector)
        evidence = [p.evidence(ticker) for p in passages]
        result = QuestionAnswer(
            status="insufficient_evidence", question=body.question, message=ABSTENTION
        )
        if evidence:
            reserve(session, "generation", daily=40, seconds=0)
            try:
                draft = provider.answer(body.question, evidence)
                if citations_match(draft, evidence):
                    reserve(session, "generation", daily=40, seconds=0)
                    verdict = provider.verify(body.question, evidence, draft)
                    if support_passes(draft, verdict):
                        by_id = {p.passage.id: p for p in passages}
                        claims = []
                        for claim in draft.claims:
                            citations = []
                            for ref in claim.evidence:
                                source = by_id[ref.passage_id]
                                url = urlsplit(source.filing.source_url)
                                if (
                                    url.scheme != "https"
                                    or url.netloc != "www.sec.gov"
                                    or not url.path.startswith("/Archives/edgar/data/")
                                ):
                                    raise ModelError("A filing source could not be verified.")
                                offset = source.passage.start_offset + source.passage.text.index(
                                    ref.quote
                                )
                                citations.append(
                                    Citation(
                                        passage_id=ref.passage_id,
                                        accession=source.filing.accession,
                                        form=source.filing.form,
                                        filed_on=source.filing.filed_on,
                                        section=source.passage.section,
                                        quote=ref.quote,
                                        source_url=source.filing.source_url,
                                        start_offset=offset,
                                        end_offset=offset + len(ref.quote),
                                    )
                                )
                            claims.append(CitedClaim(text=claim.text, citations=citations))
                        result = QuestionAnswer(
                            status="answered",
                            question=body.question,
                            claims=claims,
                            message="Answer from your filings",
                        )
            except ModelLimitError:
                pause(session, "generation")
                raise
        # A holding/watch can be removed while the provider is running.
        session.expire_all()
        authorize(session, user.id, ticker)
        return result
    except ModelLimitError as exc:
        raise HTTPException(
            status_code=429, detail=str(exc), headers={"Retry-After": "60"}
        ) from exc
    except ModelError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
