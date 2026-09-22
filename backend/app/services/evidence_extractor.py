"""Extract snippet-based evidence from selected search results."""

from datetime import datetime, timezone
from uuid import UUID

from backend.app.models.evidence import Evidence, EvidenceStance, ExcerptKind
from backend.app.models.search import SearchResult


class EvidenceExtractor:
    """Convert selected SearchResult objects into traceable Evidence objects."""

    def extract(
        self,
        result: SearchResult,
        *,
        claim_id: UUID,
        atomic_claim_id: UUID,
        stance: EvidenceStance = EvidenceStance.DOES_NOT_ADDRESS,
    ) -> Evidence | None:
        """Create evidence from a search-result snippet without fetching the source."""

        if not result.snippet or not result.snippet.strip():
            return None

        return Evidence(
            claim_id=claim_id,
            atomic_claim_id=atomic_claim_id,
            query_id=result.query_id,
            search_result_id=result.search_result_id,
            source_title=result.title,
            source_url=result.canonical_url,
            source_domain=result.source_domain,
            source_type=result.source_type,
            publication_date=result.publication_date,
            retrieved_at=result.retrieved_at,
            excerpt=result.snippet.strip(),
            excerpt_kind=ExcerptKind.SEARCH_RESULT_SNIPPET,
            stance=stance,
        )