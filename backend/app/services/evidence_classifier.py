"""Classify evidence against an atomic claim through a provider-agnostic boundary."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from backend.app.models.evidence import Evidence, EvidenceStance


class EvidenceClassificationAdapter(Protocol):
    """Provider-agnostic boundary for semantic evidence classification."""

    def classify(
        self,
        *,
        atomic_claim: str,
        evidence_excerpt: str,
    ) -> EvidenceStance:
        """Return the stance of evidence toward an atomic claim."""


class EvidenceClassifier:
    """Assign an evidence stance using an injected classification adapter."""

    def __init__(self, adapter: EvidenceClassificationAdapter) -> None:
        self._adapter = adapter

    def classify(
        self,
        evidence: Evidence,
        *,
        atomic_claim: str,
    ) -> Evidence:
        """Return a copy of evidence with its classified stance."""

        stance = self._adapter.classify(
            atomic_claim=atomic_claim,
            evidence_excerpt=evidence.excerpt,
        )

        return evidence.model_copy(update={"stance": stance})