"""Authenticated issuer questions and filing-scoped contextual research (ADR 0027)."""

import json
from collections.abc import Iterator
from datetime import date
from typing import Annotated, Literal
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.auth import COOKIE_NAME, CurrentUser, get_current_user
from app.api.filings import COVERAGE, SessionDep, authorize
from app.core.config import settings
from app.data.filing_embeddings import coverage, retrieve
from app.data.model_budget import ModelLimitError, check_available, pause, reserve
from app.data.question_factory import create_provider, embedding_version
from app.data.question_provider import ModelError, QuestionProvider
from app.engines.rag.grounding import citations_match, support_passes
from app.models import Filing, FilingPassage, FilingSync

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
    return _answer(ticker, body.question, body.question, user.id, session, provider)


def _answer(
    ticker: str,
    question: str,
    prompt: str,
    user_id: int,
    session: Session,
    provider: QuestionProvider,
    *,
    accession: str | None = None,
    query_text: str | None = None,
) -> QuestionAnswer:
    ticker = authorize(session, user_id, ticker)
    job = session.get(FilingSync, ticker)
    if job is None or not job.cik:
        raise HTTPException(
            status_code=409, detail="No company filings are ready for questions yet."
        )
    total, ready = coverage(session, job.cik, provider.embedding_version, accession=accession)
    if not total or ready != total:
        raise HTTPException(
            status_code=409, detail="Filings are still being prepared for questions."
        )
    try:
        # Reject known cooldown/exhaustion before spending local CPU or hosted embedding calls.
        check_available(session, f"questions:user:{user_id}", daily=10)
        check_available(session, "questions", daily=20)
        if not provider.local_embeddings:
            reserve(session, "embeddings", daily=200, seconds=0)
        try:
            vector = provider.embed([query_text or question], query=True)[0]
        except ModelLimitError:
            pause(session, "embeddings")
            raise
        passages = retrieve(
            session, job.cik, provider.embedding_version, vector, accession=accession
        )
        originals = [
            (p.passage.id, p.passage.text, p.passage.start_offset, p.passage.end_offset)
            for p in passages
        ]
        evidence = [p.evidence(ticker) for p in passages]
        # Preparation/search failures must not consume a user's question allowance.
        reserve(session, f"questions:user:{user_id}", daily=10, seconds=30)
        reserve(session, "questions", daily=20, seconds=15)
        result = QuestionAnswer(
            status="insufficient_evidence", question=question, message=ABSTENTION
        )
        if evidence:
            reserve(session, "generation", daily=40, seconds=0)
            try:
                draft = provider.answer(prompt, evidence)
                if citations_match(draft, evidence):
                    reserve(session, "generation", daily=40, seconds=0)
                    verdict = provider.verify(prompt, evidence, draft)
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
                            question=question,
                            claims=claims,
                            message="Answer from your filings",
                        )
            except ModelLimitError:
                pause(session, "generation")
                raise
        # A holding/watch can be removed while the provider is running.
        session.expire_all()
        authorize(session, user_id, ticker)
        if accession is not None:
            # The corpus can be replaced during provider I/O. Never return stale provenance.
            for passage_id, text, start, end in originals:
                current = session.get(FilingPassage, passage_id)
                if current is None or (
                    current.text,
                    current.start_offset,
                    current.end_offset,
                    current.accession,
                ) != (text, start, end, accession):
                    raise HTTPException(409, "The filing changed. Reopen it before asking again.")
            result.coverage = f"Selected filing only: {accession}."
            result.limitation = (
                "Answers use retrieved passages from this filing only; they may miss disclosures. "
                "Check every quoted passage and the original filing."
            )
        return result
    except ModelLimitError as exc:
        raise HTTPException(
            status_code=429, detail=str(exc), headers={"Retry-After": "60"}
        ) from exc
    except ModelError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


class ConversationTurn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    accession: str = Field(pattern=r"^\d{10}-\d{2}-\d{6}$")
    question: str = Field(min_length=5, max_length=1000)
    answer: str = Field(min_length=1, max_length=1500)


class DocumentQuestionInput(QuestionInput):
    revision: str = Field(pattern=r"^[a-f0-9]{64}$")
    history: list[ConversationTurn] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def bounded_context(self) -> "DocumentQuestionInput":
        if sum(len(t.question) + len(t.answer) for t in self.history) > 6000:
            raise ValueError("Conversation context exceeds 6000 characters.")
        return self


class ReaderPassage(BaseModel):
    id: int
    ordinal: int
    section: str
    text: str
    start_offset: int
    end_offset: int


class FilingDocument(BaseModel):
    ticker: str
    accession: str
    form: str
    filed_on: date
    source_url: str
    revision: str
    content_kind: Literal["indexed_passages"] = "indexed_passages"
    total_passages: int
    offset: int
    next_offset: int | None
    passages: list[ReaderPassage]


def document_for(session: Session, user_id: int, ticker: str, accession: str) -> Filing:
    ticker = authorize(session, user_id, ticker)
    job = session.get(FilingSync, ticker)
    filing = session.get(Filing, accession)
    if not job or not job.cik or filing is None or filing.cik != job.cik:
        raise HTTPException(404, "This filing is not available for this company.")
    url = urlsplit(filing.source_url)
    if (
        url.scheme != "https"
        or url.netloc != "www.sec.gov"
        or not url.path.startswith("/Archives/edgar/data/")
    ):
        raise HTTPException(409, "The filing source could not be verified.")
    return filing


@router.get("/{ticker}/documents/{accession}", response_model=FilingDocument)
def read_document(
    ticker: str,
    accession: str,
    user: CurrentUser,
    session: SessionDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    passage_id: Annotated[int | None, Query(ge=1)] = None,
) -> FilingDocument:
    filing = document_for(session, user.id, ticker, accession)
    query = select(FilingPassage).where(FilingPassage.accession == accession)
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    if passage_id is not None:
        passage = session.get(FilingPassage, passage_id)
        if passage is None or passage.accession != accession:
            raise HTTPException(404, "Passage not found in this filing.")
        offset = (passage.ordinal // 40) * 40
    rows = session.scalars(query.order_by(FilingPassage.ordinal).offset(offset).limit(40)).all()
    return FilingDocument(
        ticker=ticker.upper(),
        accession=accession,
        form=filing.form,
        filed_on=filing.filed_on,
        source_url=filing.source_url,
        revision=filing.text_sha256,
        total_passages=total,
        offset=offset,
        next_offset=offset + len(rows) if offset + len(rows) < total else None,
        passages=[
            ReaderPassage(
                id=p.id,
                ordinal=p.ordinal,
                section=p.section,
                text=p.text,
                start_offset=p.start_offset,
                end_offset=p.end_offset,
            )
            for p in rows
        ],
    )


@router.get("/{ticker}/documents/{accession}/questions/status", response_model=QuestionStatus)
def document_question_status(
    ticker: str,
    accession: str,
    user: CurrentUser,
    session: SessionDep,
) -> QuestionStatus:
    filing = document_for(session, user.id, ticker, accession)
    total, ready = coverage(session, filing.cik, embedding_version(), accession=accession)
    return QuestionStatus(
        configured=settings.qa_configured,
        total_passages=total,
        ready_passages=ready,
        ready=settings.qa_configured and total > 0 and total == ready,
    )


@router.post("/{ticker}/documents/{accession}/questions", response_model=QuestionAnswer)
def ask_document_question(
    ticker: str,
    accession: str,
    body: DocumentQuestionInput,
    request: Request,
    user: CurrentUser,
    session: SessionDep,
    provider: Annotated[QuestionProvider, Depends(get_question_provider)],
) -> QuestionAnswer:
    filing = document_for(session, user.id, ticker, accession)
    if filing.text_sha256 != body.revision:
        raise HTTPException(409, "The filing changed. Reopen it before asking again.")
    if any(turn.accession != accession for turn in body.history):
        raise HTTPException(422, "Conversation context must belong to this filing only.")
    prompt = json.dumps(
        {
            "current_question": body.question,
            "untrusted_conversation_context": [t.model_dump() for t in body.history],
        }
    )
    # Stay within the adapter's 2200-character embedding limit. The current question is
    # never truncated; the latest user question resolves short references without a model call.
    query_text = body.question
    if body.history:
        query_text += "\nPrevious question: " + body.history[-1].question
        query_text += "\nPrevious answer (context only): " + body.history[-1].answer[:100]
    result = _answer(
        ticker,
        body.question,
        prompt,
        user.id,
        session,
        provider,
        accession=accession,
        query_text=query_text,
    )
    session.expire_all()
    get_current_user(session, request.cookies.get(COOKIE_NAME))
    current = document_for(session, user.id, ticker, accession)
    if current.text_sha256 != body.revision:
        raise HTTPException(409, "The filing changed. Reopen it before asking again.")
    return result
