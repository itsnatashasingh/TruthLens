from __future__ import annotations

import re

from backend.app.models.claim import AtomicClaim, OriginalClaim
from backend.app.models.search import SearchEngine, SearchQuery


MAX_ATOMIC_CLAIMS = 5
MAX_QUERIES_PER_CLAIM = 2


class ClaimAnalyzer:
    """Deterministically decomposes a user claim and creates search queries."""

    def analyze(self, claim: OriginalClaim) -> tuple[list[AtomicClaim], list[SearchQuery]]:
        atomic_claims = self._decompose_claim(claim)
        search_queries = [
            query
            for atomic_claim in atomic_claims
            for query in self._build_queries(atomic_claim, claim.claim_id)
        ]

        return atomic_claims, search_queries

    def _decompose_claim(self, claim: OriginalClaim) -> list[AtomicClaim]:
        text = claim.text.strip()

        parts = [
            part.strip()
            for part in re.split(
                r"\s+(?:and|but|while|because|although)\s+",
                text,
                flags=re.IGNORECASE,
            )
            if part.strip()
        ]

        if not parts:
            parts = [text]

        parts = parts[:MAX_ATOMIC_CLAIMS]

        return [
            AtomicClaim(
                claim_id=claim.claim_id,
                text=part,
            )
            for part in parts
        ]

    def _build_queries(
        self,
        claim: AtomicClaim,
        original_claim_id,
    ) -> list[SearchQuery]:
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

        queries: list[SearchQuery] = []

        for engine in engines:
            query_text = self._targeted_query(text, engine)

            queries.append(
                SearchQuery(
                    claim_id=original_claim_id,
                    atomic_claim_id=claim.atomic_claim_id,
                    query=query_text,
                    engine=engine,
                )
            )

        return queries

    @staticmethod
    def _targeted_query(text: str, engine: SearchEngine) -> str:
        if engine == SearchEngine.GOOGLE_SCHOLAR:
            return f'"{text}" evidence research study'

        if engine == SearchEngine.GOOGLE_NEWS:
            return f'"{text}" latest news'

        return f'"{text}" evidence'