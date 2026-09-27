"""Pure, fail-closed answer validation. No provider, database or network access."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class EvidenceReference(StrictModel):
    passage_id: int = Field(gt=0)
    quote: str = Field(min_length=20, max_length=1800)


class AnswerClaim(StrictModel):
    text: str = Field(min_length=1, max_length=800)
    evidence: list[EvidenceReference] = Field(min_length=1, max_length=3)


class AnswerDraft(StrictModel):
    status: Literal["answered", "insufficient_evidence"]
    claims: list[AnswerClaim] = Field(max_length=6)

    @model_validator(mode="after")
    def consistent_status(self) -> "AnswerDraft":
        if (self.status == "answered") != bool(self.claims):
            raise ValueError("Only an answered response may contain claims.")
        return self


class ClaimVerdict(StrictModel):
    claim_index: int = Field(ge=0, lt=6)
    supported: bool


class GroundingVerdict(StrictModel):
    answers_question: bool
    claims: list[ClaimVerdict] = Field(max_length=6)


@dataclass(frozen=True)
class Evidence:
    passage_id: int
    text: str
    source_label: str = ""


def citations_match(draft: AnswerDraft, passages: Sequence[Evidence]) -> bool:
    """Check every quote against the supplied evidence, never model-created sources.

    This proves provenance, not entailment. A separate support check must also pass.
    Exact substrings preserve passage offsets and avoid silently repairing quotations.
    """
    by_id = {p.passage_id: p.text for p in passages}
    if len(by_id) != len(passages):
        return False
    return draft.status == "answered" and all(
        claim.text.strip()
        and all(
            ref.quote.strip() and ref.passage_id in by_id and ref.quote in by_id[ref.passage_id]
            for ref in claim.evidence
        )
        for claim in draft.claims
    )


def support_passes(draft: AnswerDraft, verdict: GroundingVerdict) -> bool:
    """Require a complete, unique verdict for every claim; partial approval fails."""
    expected = set(range(len(draft.claims)))
    actual = [claim.claim_index for claim in verdict.claims]
    return (
        draft.status == "answered"
        and verdict.answers_question
        and len(actual) == len(expected)
        and set(actual) == expected
        and all(claim.supported for claim in verdict.claims)
    )
