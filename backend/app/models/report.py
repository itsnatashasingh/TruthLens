"""Models for an auditable research report."""

from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from backend.app.models.claim import AtomicClaim, OriginalClaim
from backend.app.models.evidence import Evidence


class OverallAssessment(StrEnum):
    """Allowed final assessment labels."""

    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    MIXED = "MIXED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class AtomicClaimAssessment(BaseModel):
    """The deterministic assessment recorded for one atomic claim."""

    atomic_claim_id: UUID
    assessment: OverallAssessment


class EvidenceTrailEntry(BaseModel):
    """Links one evidence item to its research provenance."""

    evidence_trail_id: UUID = Field(default_factory=uuid4)
    claim_id: UUID
    atomic_claim_id: UUID
    query_id: UUID
    search_result_id: UUID
    evidence_id: UUID


class ResearchReport(BaseModel):
    """The future completed output of the bounded research workflow."""

    original_claim: OriginalClaim
    assessment: OverallAssessment
    summary: str
    atomic_claims: list[AtomicClaim] = Field(default_factory=list)
    atomic_claim_assessments: list[AtomicClaimAssessment] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    evidence_trail: list[EvidenceTrailEntry] = Field(default_factory=list)
