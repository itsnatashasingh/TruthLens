"""Models for SerpApi search planning and normalized search results."""

from datetime import date, datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl


class SearchEngine(StrEnum):
    """Supported SerpApi engines for the MVP."""

    GOOGLE = "google"
    GOOGLE_NEWS = "google_news"
    GOOGLE_SCHOLAR = "google_scholar"


class SourceType(StrEnum):
    """Retrieval categories, not source credibility rankings."""

    WEB_GENERAL = "web/general"
    NEWS = "news"
    ACADEMIC = "academic"


class SearchQuery(BaseModel):
    """A planned query linked to a specific atomic claim."""

    query_id: UUID = Field(default_factory=uuid4)
    claim_id: UUID
    atomic_claim_id: UUID
    query: str = Field(min_length=1, max_length=500)
    engine: SearchEngine


class SearchResult(BaseModel):
    """A normalized SerpApi result before it is treated as evidence."""

    search_result_id: UUID = Field(default_factory=uuid4)
    query_id: UUID
    position: int | None = Field(default=None, ge=1)
    title: str = Field(min_length=1)
    url: HttpUrl
    canonical_url: HttpUrl | None = None
    source_domain: str = Field(min_length=1)
    snippet: str | None = None
    source_type: SourceType
    publication_date: date | None = None
    author: str | None = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    engine: SearchEngine
    engine_metadata: dict[str, Any] = Field(default_factory=dict)
