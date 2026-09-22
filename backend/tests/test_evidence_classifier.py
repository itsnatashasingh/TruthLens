from datetime import UTC, datetime
from uuid import uuid4

from backend.app.models.evidence import Evidence, EvidenceStance, ExcerptKind
from backend.app.models.search import SourceType
from backend.app.services.evidence_classifier import EvidenceClassifier


class StubClassificationAdapter:
    def __init__(self, stance: EvidenceStance) -> None:
        self.stance = stance
        self.calls: list[tuple[str, str]] = []

    def classify(
        self,
        *,
        atomic_claim: str,
        evidence_excerpt: str,
    ) -> EvidenceStance:
        self.calls.append((atomic_claim, evidence_excerpt))
        return self.stance


def make_evidence() -> Evidence:
    return Evidence(
        claim_id=uuid4(),
        atomic_claim_id=uuid4(),
        query_id=uuid4(),
        search_result_id=uuid4(),
        source_title="Example source",
        source_url="https://example.org/source",
        source_domain="example.org",
        source_type=SourceType.WEB_GENERAL,
        retrieved_at=datetime(2025, 1, 20, tzinfo=UTC),
        excerpt="Maintenance costs were lower.",
        excerpt_kind=ExcerptKind.SEARCH_RESULT_SNIPPET,
        stance=EvidenceStance.DOES_NOT_ADDRESS,
    )


def test_classifier_assigns_adapter_stance() -> None:
    evidence = make_evidence()
    adapter = StubClassificationAdapter(EvidenceStance.SUPPORTS)

    classified = EvidenceClassifier(adapter).classify(
        evidence,
        atomic_claim="Electric vehicles have lower maintenance costs.",
    )

    assert classified.stance is EvidenceStance.SUPPORTS


def test_classifier_preserves_evidence_provenance() -> None:
    evidence = make_evidence()
    adapter = StubClassificationAdapter(EvidenceStance.CONTRADICTS)

    classified = EvidenceClassifier(adapter).classify(
        evidence,
        atomic_claim="Electric vehicles have lower maintenance costs.",
    )

    assert classified.evidence_id == evidence.evidence_id
    assert classified.claim_id == evidence.claim_id
    assert classified.atomic_claim_id == evidence.atomic_claim_id
    assert classified.query_id == evidence.query_id
    assert classified.search_result_id == evidence.search_result_id
    assert classified.source_url == evidence.source_url
    assert classified.excerpt == evidence.excerpt


def test_classifier_passes_claim_and_excerpt_to_adapter() -> None:
    evidence = make_evidence()
    adapter = StubClassificationAdapter(EvidenceStance.CONTEXTUALIZES)

    EvidenceClassifier(adapter).classify(
        evidence,
        atomic_claim="Electric vehicles have lower maintenance costs.",
    )

    assert adapter.calls == [
        (
            "Electric vehicles have lower maintenance costs.",
            "Maintenance costs were lower.",
        )
    ]


def test_classifier_does_not_mutate_original_evidence() -> None:
    evidence = make_evidence()
    adapter = StubClassificationAdapter(EvidenceStance.SUPPORTS)

    classified = EvidenceClassifier(adapter).classify(
        evidence,
        atomic_claim="Electric vehicles have lower maintenance costs.",
    )

    assert evidence.stance is EvidenceStance.DOES_NOT_ADDRESS
    assert classified.stance is EvidenceStance.SUPPORTS
    assert classified is not evidence


def test_classifier_supports_each_allowed_stance() -> None:
    for stance in EvidenceStance:
        evidence = make_evidence()
        adapter = StubClassificationAdapter(stance)

        classified = EvidenceClassifier(adapter).classify(
            evidence,
            atomic_claim="Test atomic claim.",
        )

        assert classified.stance is stance