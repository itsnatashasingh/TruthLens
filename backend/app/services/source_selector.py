from __future__ import annotations

from backend.app.models.search import SearchResult


class SourceSelector:
    """Select usable search results for snippet-based evidence extraction."""

    def select(
        self,
        results: list[SearchResult],
        *,
        limit: int = 5,
    ) -> list[SearchResult]:
        """Return deterministic evidence candidates from normalized results."""

        if limit <= 0:
            return []

        selected: list[SearchResult] = []
        seen_result_ids: set[str] = set()

        for result in results:
            result_id = str(result.search_result_id)

            if result_id in seen_result_ids:
                continue

            if not result.title.strip():
                continue

            if not result.canonical_url:
                continue

            if not result.snippet or not result.snippet.strip():
                continue

            seen_result_ids.add(result_id)
            selected.append(result)

            if len(selected) >= limit:
                break

        return selected