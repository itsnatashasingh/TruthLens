"""Models for snippet-based evidence and its provenance."""

from datetime import date, datetime, timezone
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl

from backend.app.models.search import SourceType


class EvidenceStance(StrEnum):
    """An evidence item's relationship to an atomic claim."""

    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    CONTEXTUALIZES = "CONTEXTUALIZES"
    DOES_NOT_ADDRESS = "DOES_NOT_ADDRESS"


class ExcerptKind(StrEnum):
    """How an evidence excerpt was represented from SerpApi result data."""

    SEARCH_RESULT_SNIPPET = "search_result_snippet"
    SNIPPET_PARAPHRASE = "snippet_paraphrase"


class Evidence(BaseModel):
    """Traceable evidence derived only from SerpApi search-result data."""

    evidence_id: UUID = Field(default_factory=uuid4)
    evidence_trail_id: UUID = Field(default_factory=uuid4)
    claim_id: UUID
    atomic_claim_id: UUID
    query_id: UUID
    search_result_id: UUID
    source_title: str = Field(min_length=1)
    source_url: HttpUrl
    source_domain: str = Field(min_length=1)
    source_type: SourceType
    publication_date: date | None = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    excerpt: str = Field(min_length=1)
    excerpt_kind: ExcerptKind
    stance: EvidenceStance
    relevance: float | None = Field(default=None, ge=0, le=1)
