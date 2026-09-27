"""API routes for the TruthLens research workflow."""

from fastapi import APIRouter, Depends

from backend.app.api.schemas import (
    HealthResponse,
    ResearchRequest,
)
from backend.app.config import settings
from backend.app.models.claim import OriginalClaim
from backend.app.models.report import ResearchReport
from backend.app.services.assessment_aggregator import AssessmentAggregator
from backend.app.services.claim_analyzer import ClaimAnalyzer
from backend.app.services.evidence_classifier import EvidenceClassifier
from backend.app.services.evidence_extractor import EvidenceExtractor
from backend.app.services.research_orchestrator import ResearchOrchestrator
from backend.app.services.serpapi import SerpApiClient
from backend.app.services.source_selector import SourceSelector


router = APIRouter(prefix="/api/v1", tags=["api"])


class UnconfiguredEvidenceClassificationAdapter:
    """Placeholder provider until an LLM implementation is configured."""

    def classify_evidence(
        self,
        *,
        atomic_claim: str,
        evidence_excerpt: str,
    ):
        raise NotImplementedError(
            "LLM classification provider is not configured."
        )


def get_research_orchestrator() -> ResearchOrchestrator:
    """Build the research orchestrator and its application services."""

    evidence_classifier = EvidenceClassifier(
        adapter=UnconfiguredEvidenceClassificationAdapter()
    )

    return ResearchOrchestrator(
        claim_analyzer=ClaimAnalyzer(),
        serpapi_client=SerpApiClient(),
        source_selector=SourceSelector(),
        evidence_extractor=EvidenceExtractor(),
        evidence_classifier=evidence_classifier,
        assessment_aggregator=AssessmentAggregator(),
    )


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return a minimal response proving that the API is running."""

    return HealthResponse(application=settings.app_name)


@router.post("/research", response_model=ResearchReport)
def research(
    request: ResearchRequest,
    orchestrator: ResearchOrchestrator = Depends(
        get_research_orchestrator
    ),
) -> ResearchReport:
    """Research a submitted factual claim."""

    claim = OriginalClaim(text=request.claim)

    return orchestrator.research(claim)