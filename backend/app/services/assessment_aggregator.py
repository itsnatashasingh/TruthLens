"""Deterministic assessment aggregation for TruthLens."""

from uuid import UUID

from backend.app.models.evidence import Evidence, EvidenceStance
from backend.app.models.report import AtomicClaimAssessment, OverallAssessment


class AssessmentAggregator:
    """Deterministically aggregate evidence into claim assessments."""

    def assess_atomic_claim(
        self,
        atomic_claim_id: UUID,
        evidence: list[Evidence],
    ) -> AtomicClaimAssessment:
        """Assess one atomic claim from its unique evidence classifications."""

        atomic_evidence = [
            item
            for item in evidence
            if item.atomic_claim_id == atomic_claim_id
        ]

        stances = {
            item.stance
            for item in atomic_evidence
        }

        has_support = EvidenceStance.SUPPORTS in stances
        has_contradiction = EvidenceStance.CONTRADICTS in stances

        if has_support and has_contradiction:
            assessment = OverallAssessment.MIXED
        elif has_support:
            assessment = OverallAssessment.SUPPORTED
        elif has_contradiction:
            assessment = OverallAssessment.CONTRADICTED
        else:
            assessment = OverallAssessment.INSUFFICIENT_EVIDENCE

        return AtomicClaimAssessment(
            atomic_claim_id=atomic_claim_id,
            assessment=assessment,
        )

    def assess_overall(
        self,
        assessments: list[AtomicClaimAssessment],
    ) -> OverallAssessment:
        """Deterministically aggregate atomic assessments into one final assessment."""

        if not assessments:
            raise ValueError("At least one atomic assessment is required.")

        labels = {
            assessment.assessment
            for assessment in assessments
        }

        # Any insufficiently addressed atomic claim makes
        # the overall assessment insufficient.
        if OverallAssessment.INSUFFICIENT_EVIDENCE in labels:
            return OverallAssessment.INSUFFICIENT_EVIDENCE

        # Any mixed atomic claim makes the overall assessment mixed.
        if OverallAssessment.MIXED in labels:
            return OverallAssessment.MIXED

        has_supported = OverallAssessment.SUPPORTED in labels
        has_contradicted = OverallAssessment.CONTRADICTED in labels

        # A combination of supported and contradicted atomic claims
        # produces a mixed overall assessment.
        if has_supported and has_contradicted:
            return OverallAssessment.MIXED

        if has_supported:
            return OverallAssessment.SUPPORTED

        if has_contradicted:
            return OverallAssessment.CONTRADICTED

        return OverallAssessment.INSUFFICIENT_EVIDENCE