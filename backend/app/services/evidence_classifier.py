"""Classify evidence against an atomic claim through a provider-agnostic boundary."""

from __future__ import annotations

from backend.app.models.evidence import Evidence
from backend.app.services.llm import LLMClassificationProvider


class EvidenceClassifier:
    """Assign an evidence stance using an injected classification provider."""

    def __init__(self, adapter: LLMClassificationProvider) -> None:
        self._adapter = adapter

    def classify(
        self,
        evidence: Evidence,
        *,
        atomic_claim: str,
    ) -> Evidence:
        """Return a copy of evidence with its classified stance."""

        stance = self._adapter.classify_evidence(
            atomic_claim=atomic_claim,
            evidence_excerpt=evidence.excerpt,
        )

        return evidence.model_copy(update={"stance": stance})