"""Models for original and atomic claims."""

from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class OriginalClaim(BaseModel):
    """A factual claim submitted by a user."""

    claim_id: UUID = Field(default_factory=uuid4)
    text: str = Field(min_length=1, max_length=2_000)


class AtomicClaim(BaseModel):
    """A researchable component of an original claim."""

    atomic_claim_id: UUID = Field(default_factory=uuid4)
    claim_id: UUID
    text: str = Field(min_length=1, max_length=2_000)
