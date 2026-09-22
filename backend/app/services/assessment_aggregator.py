"""Deterministically aggregate classified evidence into atomic-claim assessments."""

from collections.abc import Iterable
from uuid import UUID

from backend.app.models.evidence import Evidence, EvidenceStance
from backend.app.models.report import AtomicClaimAssessment, OverallAssessment


class AssessmentAggregator:
    """Derive assessments without using an LLM or numeric truth score."""

    def assess_atomic_claim(
        self,
        atomic_claim_id: UUID,
        evidence: Iterable[Evidence],
    ) -> AtomicClaimAssessment:
        """Determine one atomic claim's assessment from its evidence stances."""

        stances = [
            item.stance
            for item in evidence
            if item.atomic_claim_id == atomic_claim_id
        ]

        if not stances:
            assessment = OverallAssessment.INSUFFICIENT_EVIDENCE
        elif EvidenceStance.SUPPORTS in stances and EvidenceStance.CONTRADICTS in stances:
            assessment = OverallAssessment.MIXED
        elif EvidenceStance.SUPPORTS in stances:
            assessment = OverallAssessment.SUPPORTED
        elif EvidenceStance.CONTRADICTS in stances:
            assessment = OverallAssessment.CONTRADICTED
        else:
            assessment = OverallAssessment.INSUFFICIENT_EVIDENCE

        return AtomicClaimAssessment(
            atomic_claim_id=atomic_claim_id,
            assessment=assessment,
        )