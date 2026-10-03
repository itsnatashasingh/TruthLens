from uuid import uuid4

from backend.app.models.claim import AtomicClaim
from backend.app.models.evidence import Evidence, EvidenceStance, ExcerptKind
from backend.app.models.search import SourceType
from backend.app.services.conflict_gap_detector import ConflictGapDetector


def make_atomic_claim(text: str = "The Earth is round") -> AtomicClaim:
    return AtomicClaim(
        claim_id=uuid4(),
        text=text,
    )

def make_evidence(
    atomic_claim_id,
    stance: EvidenceStance,
) -> Evidence:
    return Evidence(
        claim_id=uuid4(),
        atomic_claim_id=atomic_claim_id,
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
    atomic_claim = make_atomic_claim()

    evidence = [
        make_evidence(
            atomic_claim.atomic_claim_id,
            EvidenceStance.SUPPORTS,
        ),
        make_evidence(
            atomic_claim.atomic_claim_id,
            EvidenceStance.CONTRADICTS,
        ),
    ]

    conflicts = ConflictGapDetector().detect_conflicts(
        [atomic_claim],
        evidence,
    )

    assert conflicts == [atomic_claim]


def test_does_not_report_conflict_when_only_supporting_evidence_exists() -> None:
    atomic_claim = make_atomic_claim()

    evidence = [
        make_evidence(
            atomic_claim.atomic_claim_id,
            EvidenceStance.SUPPORTS,
        ),
    ]

    conflicts = ConflictGapDetector().detect_conflicts(
        [atomic_claim],
        evidence,
    )

    assert conflicts == []


def test_does_not_report_conflict_when_only_contradicting_evidence_exists() -> None:
    atomic_claim = make_atomic_claim()

    evidence = [
        make_evidence(
            atomic_claim.atomic_claim_id,
            EvidenceStance.CONTRADICTS,
        ),
    ]

    conflicts = ConflictGapDetector().detect_conflicts(
        [atomic_claim],
        evidence,
    )

    assert conflicts == []


def test_detects_gap_when_no_evidence_exists() -> None:
    atomic_claim = make_atomic_claim()

    gaps = ConflictGapDetector().detect_gaps(
        [atomic_claim],
        [],
    )

    assert gaps == [atomic_claim]


def test_detects_gap_when_evidence_does_not_address_claim() -> None:
    atomic_claim = make_atomic_claim()

    evidence = [
        make_evidence(
            atomic_claim.atomic_claim_id,
            EvidenceStance.DOES_NOT_ADDRESS,
        ),
        make_evidence(
            atomic_claim.atomic_claim_id,
            EvidenceStance.CONTEXTUALIZES,
        ),
    ]

    gaps = ConflictGapDetector().detect_gaps(
        [atomic_claim],
        evidence,
    )

    assert gaps == [atomic_claim]


def test_does_not_report_gap_when_supporting_evidence_exists() -> None:
    atomic_claim = make_atomic_claim()

    evidence = [
        make_evidence(
            atomic_claim.atomic_claim_id,
            EvidenceStance.SUPPORTS,
        ),
    ]

    gaps = ConflictGapDetector().detect_gaps(
        [atomic_claim],
        evidence,
    )

    assert gaps == []


def test_does_not_report_gap_when_contradicting_evidence_exists() -> None:
    atomic_claim = make_atomic_claim()

    evidence = [
        make_evidence(
            atomic_claim.atomic_claim_id,
            EvidenceStance.CONTRADICTS,
        ),
    ]

    gaps = ConflictGapDetector().detect_gaps(
        [atomic_claim],
        evidence,
    )

    assert gaps == []


def test_ignores_evidence_belonging_to_other_atomic_claims() -> None:
    atomic_claim = make_atomic_claim()
    other_claim = make_atomic_claim("Water freezes at 0 degrees Celsius.")

    evidence = [
        make_evidence(
            other_claim.atomic_claim_id,
            EvidenceStance.SUPPORTS,
        ),
    ]

    gaps = ConflictGapDetector().detect_gaps(
        [atomic_claim],
        evidence,
    )

    assert gaps == [atomic_claim]


def test_handles_multiple_atomic_claims_independently() -> None:
    supporting_claim = make_atomic_claim()
    conflicting_claim = make_atomic_claim("The Moon is made of cheese.")
    gap_claim = make_atomic_claim("Mars has oceans of liquid water.")

    evidence = [
        make_evidence(
            supporting_claim.atomic_claim_id,
            EvidenceStance.SUPPORTS,
        ),
        make_evidence(
            conflicting_claim.atomic_claim_id,
            EvidenceStance.SUPPORTS,
        ),
        make_evidence(
            conflicting_claim.atomic_claim_id,
            EvidenceStance.CONTRADICTS,
        ),
    ]

    detector = ConflictGapDetector()

    conflicts = detector.detect_conflicts(
        [supporting_claim, conflicting_claim, gap_claim],
        evidence,
    )
    gaps = detector.detect_gaps(
        [supporting_claim, conflicting_claim, gap_claim],
        evidence,
    )

    assert conflicts == [conflicting_claim]
    assert gaps == [gap_claim]