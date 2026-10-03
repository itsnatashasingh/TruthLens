"""Detect evidence conflicts and gaps for TruthLens atomic claims."""

from __future__ import annotations

from backend.app.models.claim import AtomicClaim
from backend.app.models.evidence import Evidence, EvidenceStance


class ConflictGapDetector:
    """Deterministically identify conflicts and evidence gaps."""

    def detect_conflicts(
        self,
        atomic_claims: list[AtomicClaim],
        evidence: list[Evidence],
    ) -> list[AtomicClaim]:
        """Return atomic claims for which supporting and contradicting
        evidence both exist.
        """

        conflicts: list[AtomicClaim] = []

        for atomic_claim in atomic_claims:
            claim_evidence = [
                item
                for item in evidence
                if item.atomic_claim_id == atomic_claim.atomic_claim_id
            ]

            has_supporting = any(
                item.stance is EvidenceStance.SUPPORTS
                for item in claim_evidence
            )
            has_contradicting = any(
                item.stance is EvidenceStance.CONTRADICTS
                for item in claim_evidence
            )

            if has_supporting and has_contradicting:
                conflicts.append(atomic_claim)

        return conflicts

    def detect_gaps(
        self,
        atomic_claims: list[AtomicClaim],
        evidence: list[Evidence],
    ) -> list[AtomicClaim]:
        """Return atomic claims that lack substantive supporting or
        contradicting evidence.
        """

        gaps: list[AtomicClaim] = []

        for atomic_claim in atomic_claims:
            claim_evidence = [
                item
                for item in evidence
                if item.atomic_claim_id == atomic_claim.atomic_claim_id
            ]

            has_substantive_evidence = any(
                item.stance in {
                    EvidenceStance.SUPPORTS,
                    EvidenceStance.CONTRADICTS,
                }
                for item in claim_evidence
            )

            if not has_substantive_evidence:
                gaps.append(atomic_claim)

        return gaps