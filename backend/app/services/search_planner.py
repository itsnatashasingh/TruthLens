from __future__ import annotations

from backend.app.models.claim import AtomicClaim
from backend.app.models.search import SearchEngine, SearchQuery


MAX_QUERIES_PER_CLAIM = 2


class SearchPlanner:
    """Creates targeted search queries for atomic claims."""

    def plan(self, claim: AtomicClaim) -> list[SearchQuery]:
        text = claim.text.strip()
        lowered = text.lower()

        engines: list[SearchEngine] = []

        academic_terms = (
            "study",
            "studies",
            "research",
            "scientific",
            "science",
            "paper",
            "journal",
            "academic",
            "clinical",
            "experiment",
            "scholar",
        )

        news_terms = (
            "today",
            "latest",
            "recent",
            "currently",
            "current",
            "announced",
            "announcement",
            "2026",
            "this year",
            "newly",
        )

        if any(term in lowered for term in academic_terms):
            engines.append(SearchEngine.GOOGLE_SCHOLAR)

        if any(term in lowered for term in news_terms):
            engines.append(SearchEngine.GOOGLE_NEWS)

        if not engines:
            engines.append(SearchEngine.GOOGLE)

        engines = engines[:MAX_QUERIES_PER_CLAIM]

        return [
            SearchQuery(
                claim_id=claim.claim_id,
                atomic_claim_id=claim.atomic_claim_id,
                query=self._targeted_query(claim.text, engine),
                engine=engine,
            )
            for engine in engines
        ]

    @staticmethod
    def _targeted_query(text: str, engine: SearchEngine) -> str:
        if engine == SearchEngine.GOOGLE_SCHOLAR:
            return f'"{text}" evidence research study'

        if engine == SearchEngine.GOOGLE_NEWS:
            return f'"{text}" latest news'

        return f'"{text}" evidence'