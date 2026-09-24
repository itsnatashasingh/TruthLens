"""Coordinate the bounded TruthLens research workflow."""

from __future__ import annotations

from backend.app.models.claim import AtomicClaim, OriginalClaim
from backend.app.models.report import (
    AtomicClaimAssessment,
    EvidenceTrailEntry,
    OverallAssessment,
    ResearchReport,
)
from backend.app.services.assessment_aggregator import AssessmentAggregator
from backend.app.services.claim_analyzer import ClaimAnalyzer
from backend.app.services.evidence_classifier import EvidenceClassifier
from backend.app.services.evidence_extractor import EvidenceExtractor
from backend.app.services.result_normalizer import normalize_search_results
from backend.app.services.serpapi import SerpApiClient
from backend.app.services.source_selector import SourceSelector


MAX_RESULTS_PER_QUERY = 5


class ResearchOrchestrator:
    """Coordinate claim analysis, search, evidence processing, and assessment."""

    def __init__(
        self,
        claim_analyzer: ClaimAnalyzer,
        serpapi_client: SerpApiClient,
        source_selector: SourceSelector,
        evidence_extractor: EvidenceExtractor,
        evidence_classifier: EvidenceClassifier,
        assessment_aggregator: AssessmentAggregator,
    ) -> None:
        self._claim_analyzer = claim_analyzer
        self._serpapi_client = serpapi_client
        self._source_selector = source_selector
        self._evidence_extractor = evidence_extractor
        self._evidence_classifier = evidence_classifier
        self._assessment_aggregator = assessment_aggregator

    def research(self, claim: OriginalClaim) -> ResearchReport:
        """Run the bounded research workflow for one original claim."""

        atomic_claims, search_queries = self._claim_analyzer.analyze(claim)

        atomic_claim_by_id = {
            atomic_claim.atomic_claim_id: atomic_claim
            for atomic_claim in atomic_claims
        }

        evidence = []
        evidence_trail = []

        for query in search_queries:
            payload = self._serpapi_client.search(query)

            results = normalize_search_results(
                query,
                payload,
            )

            selected_results = self._source_selector.select(
                results,
                limit=MAX_RESULTS_PER_QUERY,
            )

            atomic_claim = atomic_claim_by_id.get(query.atomic_claim_id)

            if atomic_claim is None:
                continue

            for result in selected_results:
                extracted_evidence = self._evidence_extractor.extract(
                    result,
                    claim_id=claim.claim_id,
                    atomic_claim_id=atomic_claim.atomic_claim_id,
                )

                if extracted_evidence is None:
                    continue

                classified_evidence = self._evidence_classifier.classify(
                    extracted_evidence,
                    atomic_claim=atomic_claim.text,
                )

                evidence.append(classified_evidence)

                evidence_trail.append(
                    EvidenceTrailEntry(
                        claim_id=claim.claim_id,
                        atomic_claim_id=atomic_claim.atomic_claim_id,
                        query_id=query.query_id,
                        search_result_id=result.search_result_id,
                        evidence_id=classified_evidence.evidence_id,
                    )
                )

        atomic_assessments = [
            self._assessment_aggregator.assess_atomic_claim(
                atomic_claim.atomic_claim_id,
                evidence,
            )
            for atomic_claim in atomic_claims
        ]

        overall_assessment = self._assessment_aggregator.assess_overall(
            atomic_assessments
        )

        summary = self._build_summary(
            overall_assessment,
            atomic_claims,
            atomic_assessments,
            evidence,
        )

        return ResearchReport(
            original_claim=claim,
            assessment=overall_assessment,
            summary=summary,
            atomic_claims=atomic_claims,
            atomic_claim_assessments=atomic_assessments,
            evidence=evidence,
            evidence_trail=evidence_trail,
        )

    @staticmethod
    def _build_summary(
        overall_assessment: OverallAssessment,
        atomic_claims: list[AtomicClaim],
        atomic_assessments: list[AtomicClaimAssessment],
        evidence,
    ) -> str:
        """Build a deterministic summary from the completed assessments."""

        assessment_by_id = {
            assessment.atomic_claim_id: assessment.assessment
            for assessment in atomic_assessments
        }

        evidence_count = len(evidence)

        lines = [
            f"Overall assessment: {overall_assessment.value}.",
            f"Evaluated {len(atomic_claims)} atomic claim(s) using "
            f"{evidence_count} evidence item(s).",
        ]

        for atomic_claim in atomic_claims:
            assessment = assessment_by_id[atomic_claim.atomic_claim_id]

            lines.append(
                f"Atomic claim: {atomic_claim.text} — "
                f"{assessment.value}."
            )

        return " ".join(lines)