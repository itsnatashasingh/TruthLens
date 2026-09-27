"""Provider-agnostic LLM boundary for TruthLens."""

from __future__ import annotations

from typing import Protocol

from backend.app.models.evidence import EvidenceStance


class LLMClassificationProvider(Protocol):
    """Interface required by the evidence classification service."""

    def classify_evidence(
        self,
        *,
        atomic_claim: str,
        evidence_excerpt: str,
    ) -> EvidenceStance:
        """Classify the relationship between evidence and an atomic claim."""