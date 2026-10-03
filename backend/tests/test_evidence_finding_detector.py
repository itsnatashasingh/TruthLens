from uuid import uuid4

from backend.app.models.evidence import Evidence, EvidenceStance, ExcerptKind
from backend.app.models.search import SourceType
from backend.app.services.evidence_finding_detector import EvidenceFindingDetector


def make_evidence(
    *,
    atomic_claim_id=None,
    stance: EvidenceStance,
) -> Evidence:
    return Evidence(
        claim_id=uuid4(),
        atomic_claim_id=atomic_claim_id or uuid4(),
        query_id=uuid4(),
        search_result_id=uuid4(),
        source_title="Example source",
        source_url="https://example.org/source",
        source_domain="example.org",
        source_type=SourceType.WEB_GENERAL,
        excerpt="Example evidence.",
        excerpt_kind=ExcerptKind.SEARCH_RESULT_SNIPPET,
        stance=stance,
    )


def test_detects_conflicting_evidence() -> None:
    atomic_claim_id = uuid4()

    evidence = [
        make_evidence(
            atomic_claim_id=atomic_claim_id,
            stance=EvidenceStance.SUPPORTS,
        ),
        make_evidence(
            atomic_claim_id=atomic_claim_id,
            stance=EvidenceStance.CONTRADICTS,
        ),
    ]

    gaps, conflicts = EvidenceFindingDetector().detect(evidence)

    assert gaps == []
    assert len(conflicts) == 1
    assert str(atomic_claim_id) in conflicts[0]


def test_detects_gap_when_only_contextual_evidence_exists() -> None:
    atomic_claim_id = uuid4()

    evidence = [
        make_evidence(
            atomic_claim_id=atomic_claim_id,
            stance=EvidenceStance.CONTEXTUALIZES,
        ),
    ]

    gaps, conflicts = EvidenceFindingDetector().detect(evidence)

    assert len(gaps) == 1
    assert str(atomic_claim_id) in gaps[0]
    assert conflicts == []


def test_detects_gap_when_evidence_does_not_address_claim() -> None:
    atomic_claim_id = uuid4()

    evidence = [
        make_evidence(
            atomic_claim_id=atomic_claim_id,
            stance=EvidenceStance.DOES_NOT_ADDRESS,
        ),
    ]

    gaps, conflicts = EvidenceFindingDetector().detect(evidence)

    assert len(gaps) == 1
    assert conflicts == []


def test_no_finding_for_supporting_evidence() -> None:
    evidence = [
        make_evidence(
            stance=EvidenceStance.SUPPORTS,
        ),
    ]

    gaps, conflicts = EvidenceFindingDetector().detect(evidence)

    assert gaps == []
    assert conflicts == []


def test_no_finding_for_contradicting_evidence() -> None:
    evidence = [
        make_evidence(
            stance=EvidenceStance.CONTRADICTS,
        ),
    ]

    gaps, conflicts = EvidenceFindingDetector().detect(evidence)

    assert gaps == []
    assert conflicts == []


def test_detects_findings_per_atomic_claim() -> None:
    supporting_claim = uuid4()
    conflicting_claim = uuid4()

    evidence = [
        make_evidence(
            atomic_claim_id=supporting_claim,
            stance=EvidenceStance.SUPPORTS,
        ),
        make_evidence(
            atomic_claim_id=conflicting_claim,
            stance=EvidenceStance.SUPPORTS,
        ),
        make_evidence(
            atomic_claim_id=conflicting_claim,
            stance=EvidenceStance.CONTRADICTS,
        ),
    ]

    gaps, conflicts = EvidenceFindingDetector().detect(evidence)

    assert gaps == []
    assert len(conflicts) == 1
    assert str(conflicting_claim) in conflicts[0]