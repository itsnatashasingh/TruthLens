"""API request and response schemas independent of research execution."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class HealthResponse(BaseModel):
    """Minimal API health response."""

    status: Literal["ok"] = "ok"
    application: str


class ResearchRequest(BaseModel):
    """The minimal public contract for submitting a factual claim."""

    claim: str = Field(min_length=1, max_length=2_000)

    @field_validator("claim")
    @classmethod
    def claim_must_not_be_blank(cls, value: str) -> str:
        """Reject whitespace-only requests and normalize accepted claims."""

        normalized_claim = value.strip()
        if not normalized_claim:
            raise ValueError("claim must not be empty")
        return normalized_claim


class ResearchNotImplementedResponse(BaseModel):
    """Explicit placeholder returned until research execution is implemented."""

    status: Literal["not_implemented"] = "not_implemented"
    detail: str = "Research execution has not yet been implemented."
