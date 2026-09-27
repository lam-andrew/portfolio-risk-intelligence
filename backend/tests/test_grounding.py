"""US-12 provenance and complete-claim support checks, independent of any LLM."""

import pytest
from pydantic import ValidationError

from app.engines.rag.grounding import (
    AnswerDraft,
    Evidence,
    GroundingVerdict,
    citations_match,
    support_passes,
)

QUOTE = "We rely on a single supplier for certain components."


def draft(**overrides) -> AnswerDraft:
    return AnswerDraft.model_validate(
        {
            "status": "answered",
            "claims": [
                {
                    "text": "The company has supplier concentration risk.",
                    "evidence": [{"passage_id": 11, "quote": QUOTE}],
                }
            ],
            **overrides,
        }
    )


def test_exact_quote_resolves_only_within_retrieved_passages() -> None:
    answer = draft()
    assert citations_match(answer, [Evidence(11, "Item 1A. " + QUOTE)])
    assert not citations_match(answer, [Evidence(12, QUOTE)])
    assert not citations_match(answer, [Evidence(11, QUOTE.replace("single", "multiple"))])
    assert not citations_match(answer, [])
    assert not citations_match(answer, [Evidence(11, QUOTE), Evidence(11, QUOTE)])


def test_one_invalid_reference_withholds_the_whole_answer() -> None:
    answer = draft()
    answer.claims.append(answer.claims[0].model_copy(update={"text": "Another claim."}))
    answer.claims[1] = answer.claims[1].model_copy(
        update={"evidence": [answer.claims[1].evidence[0].model_copy(update={"passage_id": 99})]}
    )
    assert not citations_match(answer, [Evidence(11, QUOTE)])


@pytest.mark.parametrize(
    "changes",
    [
        {"status": "answered", "claims": []},
        {"status": "insufficient_evidence"},
        {"source_url": "https://invented.example"},
    ],
)
def test_invalid_output_contract_rejected(changes) -> None:
    with pytest.raises(ValidationError):
        draft(**changes)


def test_abstention_never_contains_claims() -> None:
    answer = draft(status="insufficient_evidence", claims=[])
    assert not citations_match(answer, [Evidence(11, QUOTE)])
    assert not support_passes(answer, GroundingVerdict(answers_question=True, claims=[]))


@pytest.mark.parametrize(
    "indices,supported,relevant,accepted",
    [
        ([0, 1], True, True, True),
        ([1, 0], True, True, True),
        ([0], True, True, False),
        ([0, 0], True, True, False),
        ([0, 2], True, True, False),
        ([0, 1], False, True, False),
        ([0, 1], True, False, False),
    ],
)
def test_support_requires_all_unique_claims(indices, supported, relevant, accepted) -> None:
    answer = draft()
    answer.claims.append(answer.claims[0])
    verdict = GroundingVerdict.model_validate(
        {
            "answers_question": relevant,
            "claims": [{"claim_index": i, "supported": supported} for i in indices],
        }
    )
    assert support_passes(answer, verdict) is accepted


def test_whitespace_and_coerced_identifiers_are_rejected() -> None:
    answer = draft()
    answer.claims[0].text = " "
    assert not citations_match(answer, [Evidence(11, QUOTE)])
    with pytest.raises(ValidationError):
        draft(claims=[{"text": "Claim", "evidence": [{"passage_id": "11", "quote": QUOTE}]}])
