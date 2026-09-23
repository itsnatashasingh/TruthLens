from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from backend.app.models.evidence import (
    Evidence,
    EvidenceStance,
    ExcerptKind,
)
from backend.app.models.report import (
    AtomicClaimAssessment,
    OverallAssessment,
)
from backend.app.models.search import SourceType
from backend.app.services.assessment_aggregator import AssessmentAggregator


def make_evidence(
    atomic_claim_id: UUID,
    stance: EvidenceStance,
) -> Evidence:
    """Create a minimal evidence item for assessment tests."""

    return Evidence(
        claim_id=uuid4(),
        atomic_claim_id=atomic_claim_id,
        query_id=uuid4(),
        search_result_id=uuid4(),
        source_title="Example source",
        source_url="https://example.org/source",
        source_domain="example.org",
        source_type=SourceType.WEB_GENERAL,
        retrieved_at=datetime(2025, 1, 20, tzinfo=UTC),
        excerpt="Relevant evidence.",
        excerpt_kind=ExcerptKind.SEARCH_RESULT_SNIPPET,
        stance=stance,
    )


def test_no_evidence_is_insufficient() -> None:
    atomic_claim_id = uuid4()

    result = AssessmentAggregator().assess_atomic_claim(
        atomic_claim_id,
        [],
    )

    assert result.assessment is OverallAssessment.INSUFFICIENT_EVIDENCE


def test_supporting_evidence_is_supported() -> None:
    atomic_claim_id = uuid4()

    evidence = [
        make_evidence(
            atomic_claim_id,
            EvidenceStance.SUPPORTS,
        ),
    ]

    result = AssessmentAggregator().assess_atomic_claim(
        atomic_claim_id,
        evidence,
    )

    assert result.assessment is OverallAssessment.SUPPORTED


def test_contradicting_evidence_is_contradicted() -> None:
    atomic_claim_id = uuid4()

    evidence = [
        make_evidence(
            atomic_claim_id,
            EvidenceStance.CONTRADICTS,
        ),
    ]

    result = AssessmentAggregator().assess_atomic_claim(
        atomic_claim_id,
        evidence,
    )

    assert result.assessment is OverallAssessment.CONTRADICTED


def test_both_supporting_and_contradicting_evidence_is_mixed() -> None:
    atomic_claim_id = uuid4()

    evidence = [
        make_evidence(
            atomic_claim_id,
            EvidenceStance.SUPPORTS,
        ),
        make_evidence(
            atomic_claim_id,
            EvidenceStance.CONTRADICTS,
        ),
    ]

    result = AssessmentAggregator().assess_atomic_claim(
        atomic_claim_id,
        evidence,
    )

    assert result.assessment is OverallAssessment.MIXED


@pytest.mark.parametrize(
    "stances",
    [
        [EvidenceStance.DOES_NOT_ADDRESS],
        [EvidenceStance.CONTEXTUALIZES],
        [
            EvidenceStance.DOES_NOT_ADDRESS,
            EvidenceStance.CONTEXTUALIZES,
        ],
    ],
)
def test_non_decisive_evidence_is_insufficient(
    stances: list[EvidenceStance],
) -> None:
    atomic_claim_id = uuid4()

    evidence = [
        make_evidence(
            atomic_claim_id,
            stance,
        )
        for stance in stances
    ]

    result = AssessmentAggregator().assess_atomic_claim(
        atomic_claim_id,
        evidence,
    )

    assert result.assessment is OverallAssessment.INSUFFICIENT_EVIDENCE


def test_ignores_evidence_for_other_atomic_claims() -> None:
    atomic_claim_id = uuid4()
    other_atomic_claim_id = uuid4()

    evidence = [
        make_evidence(
            other_atomic_claim_id,
            EvidenceStance.SUPPORTS,
        ),
    ]

    result = AssessmentAggregator().assess_atomic_claim(
        atomic_claim_id,
        evidence,
    )

    assert result.assessment is OverallAssessment.INSUFFICIENT_EVIDENCE


def make_assessment(
    assessment: OverallAssessment,
) -> AtomicClaimAssessment:
    """Create a minimal atomic assessment for overall aggregation tests."""

    return AtomicClaimAssessment(
        atomic_claim_id=uuid4(),
        assessment=assessment,
    )


def test_all_supported_is_supported() -> None:
    assessments = [
        make_assessment(OverallAssessment.SUPPORTED),
        make_assessment(OverallAssessment.SUPPORTED),
    ]

    result = AssessmentAggregator().assess_overall(assessments)

    assert result is OverallAssessment.SUPPORTED


def test_all_contradicted_is_contradicted() -> None:
    assessments = [
        make_assessment(OverallAssessment.CONTRADICTED),
        make_assessment(OverallAssessment.CONTRADICTED),
    ]

    result = AssessmentAggregator().assess_overall(assessments)

    assert result is OverallAssessment.CONTRADICTED


def test_supported_and_contradicted_is_mixed() -> None:
    assessments = [
        make_assessment(OverallAssessment.SUPPORTED),
        make_assessment(OverallAssessment.CONTRADICTED),
    ]

    result = AssessmentAggregator().assess_overall(assessments)

    assert result is OverallAssessment.MIXED


def test_mixed_atomic_assessment_is_mixed() -> None:
    assessments = [
        make_assessment(OverallAssessment.MIXED),
        make_assessment(OverallAssessment.SUPPORTED),
    ]

    result = AssessmentAggregator().assess_overall(assessments)

    assert result is OverallAssessment.MIXED


def test_insufficient_evidence_takes_precedence() -> None:
    assessments = [
        make_assessment(OverallAssessment.SUPPORTED),
        make_assessment(OverallAssessment.INSUFFICIENT_EVIDENCE),
    ]

    result = AssessmentAggregator().assess_overall(assessments)

    assert result is OverallAssessment.INSUFFICIENT_EVIDENCE


def test_insufficient_evidence_takes_precedence_over_mixed() -> None:
    assessments = [
        make_assessment(OverallAssessment.MIXED),
        make_assessment(OverallAssessment.INSUFFICIENT_EVIDENCE),
    ]

    result = AssessmentAggregator().assess_overall(assessments)

    assert result is OverallAssessment.INSUFFICIENT_EVIDENCE


def test_empty_atomic_assessments_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="At least one atomic assessment",
    ):
        AssessmentAggregator().assess_overall([])