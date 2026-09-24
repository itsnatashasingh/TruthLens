from backend.app.models.claim import OriginalClaim
from backend.app.models.evidence import EvidenceStance
from backend.app.models.report import OverallAssessment
from backend.app.services.assessment_aggregator import AssessmentAggregator
from backend.app.services.claim_analyzer import ClaimAnalyzer
from backend.app.services.evidence_classifier import EvidenceClassifier
from backend.app.services.evidence_extractor import EvidenceExtractor
from backend.app.services.research_orchestrator import ResearchOrchestrator
from backend.app.services.source_selector import SourceSelector


class FakeSerpApiClient:
    """Return deterministic SerpApi payloads without network access."""

    def search(self, query):
        return {
            "organic_results": [
                {
                    "position": 1,
                    "title": "Example evidence source",
                    "link": "https://example.org/evidence",
                    "snippet": "The evidence supports the claim.",
                }
            ]
        }

class TwoResultSerpApiClient:
    """Return two deterministic results for mixed-evidence testing."""

    def search(self, query):
        return {
            "organic_results": [
                {
                    "position": 1,
                    "title": "Supporting source",
                    "link": "https://example.org/supporting",
                    "snippet": "The evidence supports the claim.",
                },
                {
                    "position": 2,
                    "title": "Contradicting source",
                    "link": "https://example.org/contradicting",
                    "snippet": "The evidence contradicts the claim.",
                },
            ]
        }

class SupportingClassificationAdapter:
    """Classify every evidence item as supporting."""

    def classify(
        self,
        *,
        atomic_claim: str,
        evidence_excerpt: str,
    ) -> EvidenceStance:
        return EvidenceStance.SUPPORTS


class ContradictingClassificationAdapter:
    """Classify every evidence item as contradicting."""

    def classify(
        self,
        *,
        atomic_claim: str,
        evidence_excerpt: str,
    ) -> EvidenceStance:
        return EvidenceStance.CONTRADICTS


class MixedClassificationAdapter:
    """Return support and contradiction across successive evidence items."""

    def __init__(self) -> None:
        self._calls = 0

    def classify(
        self,
        *,
        atomic_claim: str,
        evidence_excerpt: str,
    ) -> EvidenceStance:
        self._calls += 1

        if self._calls % 2 == 1:
            return EvidenceStance.SUPPORTS

        return EvidenceStance.CONTRADICTS


def make_orchestrator(adapter, serpapi_client=None) -> ResearchOrchestrator:
    return ResearchOrchestrator(
        claim_analyzer=ClaimAnalyzer(),
        serpapi_client=serpapi_client or FakeSerpApiClient(),
        source_selector=SourceSelector(),
        evidence_extractor=EvidenceExtractor(),
        evidence_classifier=EvidenceClassifier(adapter),
        assessment_aggregator=AssessmentAggregator(),
    )


def test_research_returns_report() -> None:
    claim = OriginalClaim(
        text="The Earth is round",
    )

    report = make_orchestrator(
        SupportingClassificationAdapter()
    ).research(claim)

    assert report.original_claim.claim_id == claim.claim_id
    assert report.original_claim.text == claim.text
    assert report.assessment is OverallAssessment.SUPPORTED


def test_research_creates_atomic_claims() -> None:
    claim = OriginalClaim(
        text="The Earth is round and water freezes at 0 degrees Celsius",
    )

    report = make_orchestrator(
        SupportingClassificationAdapter()
    ).research(claim)

    assert len(report.atomic_claims) == 2
    assert len(report.atomic_claim_assessments) == 2


def test_research_extracts_and_classifies_evidence() -> None:
    claim = OriginalClaim(
        text="The Earth is round",
    )

    report = make_orchestrator(
        SupportingClassificationAdapter()
    ).research(claim)

    assert len(report.evidence) == 1
    assert report.evidence[0].stance is EvidenceStance.SUPPORTS
    assert report.evidence[0].claim_id == claim.claim_id


def test_research_creates_evidence_trail() -> None:
    claim = OriginalClaim(
        text="The Earth is round",
    )

    report = make_orchestrator(
        SupportingClassificationAdapter()
    ).research(claim)

    assert len(report.evidence_trail) == 1

    trail = report.evidence_trail[0]
    evidence = report.evidence[0]

    assert trail.claim_id == claim.claim_id
    assert trail.atomic_claim_id == evidence.atomic_claim_id
    assert trail.query_id == evidence.query_id
    assert trail.search_result_id == evidence.search_result_id
    assert trail.evidence_id == evidence.evidence_id


def test_supporting_evidence_produces_supported_report() -> None:
    claim = OriginalClaim(
        text="The Earth is round",
    )

    report = make_orchestrator(
        SupportingClassificationAdapter()
    ).research(claim)

    assert report.assessment is OverallAssessment.SUPPORTED
    assert (
        report.atomic_claim_assessments[0].assessment
        is OverallAssessment.SUPPORTED
    )


def test_contradicting_evidence_produces_contradicted_report() -> None:
    claim = OriginalClaim(
        text="The Earth is round",
    )

    report = make_orchestrator(
        ContradictingClassificationAdapter()
    ).research(claim)

    assert report.assessment is OverallAssessment.CONTRADICTED
    assert (
        report.atomic_claim_assessments[0].assessment
        is OverallAssessment.CONTRADICTED
    )


def test_mixed_evidence_produces_mixed_report() -> None:
    claim = OriginalClaim(
        text="The Earth is round",
    )

    report = make_orchestrator(
        MixedClassificationAdapter(),
        TwoResultSerpApiClient(),
    ).research(claim)

    assert report.assessment is OverallAssessment.MIXED
    assert (
        report.atomic_claim_assessments[0].assessment
        is OverallAssessment.MIXED
    )


def test_summary_contains_overall_assessment() -> None:
    claim = OriginalClaim(
        text="The Earth is round",
    )

    report = make_orchestrator(
        SupportingClassificationAdapter()
    ).research(claim)

    assert "Overall assessment: SUPPORTED." in report.summary
    assert "1 evidence item(s)" in report.summary


def test_research_uses_search_query_engine() -> None:
    claim = OriginalClaim(
        text="A scientific study supports this claim",
    )

    report = make_orchestrator(
        SupportingClassificationAdapter()
    ).research(claim)

    assert len(report.evidence) == 1
    assert report.evidence[0].source_type.value == "academic"


def test_report_preserves_provenance_ids() -> None:
    claim = OriginalClaim(
        text="The Earth is round",
    )

    report = make_orchestrator(
        SupportingClassificationAdapter()
    ).research(claim)

    evidence = report.evidence[0]
    trail = report.evidence_trail[0]

    assert evidence.query_id == trail.query_id
    assert evidence.search_result_id == trail.search_result_id
    assert evidence.evidence_id == trail.evidence_id