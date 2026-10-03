"""Detect deterministic evidence gaps and conflicts."""

from __future__ import annotations

from collections import defaultdict

from backend.app.models.evidence import Evidence, EvidenceStance


class EvidenceFindingDetector:
    """Identify gaps and conflicts from classified evidence."""

    def detect(
        self,
        evidence: list[Evidence],
    ) -> tuple[list[str], list[str]]:
        """Return deterministic gap and conflict descriptions."""

        evidence_by_claim: dict = defaultdict(list)

        for item in evidence:
            evidence_by_claim[item.atomic_claim_id].append(item)

        gaps: list[str] = []
        conflicts: list[str] = []

        for atomic_claim_id, claim_evidence in evidence_by_claim.items():
            stances = {item.stance for item in claim_evidence}

            if (
                EvidenceStance.SUPPORTS in stances
                and EvidenceStance.CONTRADICTS in stances
            ):
                conflicts.append(
                    f"Atomic claim {atomic_claim_id} has conflicting "
                    "supporting and contradicting evidence."
                )

            if not (
                EvidenceStance.SUPPORTS in stances
                or EvidenceStance.CONTRADICTS in stances
            ):
                gaps.append(
                    f"Atomic claim {atomic_claim_id} has no direct "
                    "supporting or contradicting evidence."
                )

        return gaps, conflicts