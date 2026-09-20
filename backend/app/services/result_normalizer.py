"""Normalize supported SerpApi result structures into SearchResult objects."""

from collections.abc import Iterable
from datetime import date, datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import NAMESPACE_URL, UUID, uuid5

from backend.app.models.search import SearchEngine, SearchQuery, SearchResult, SourceType
from backend.app.services.exceptions import SerpApiMalformedResponseError

_TRACKING_PARAMETERS = {"fbclid", "gclid", "mc_cid", "mc_eid"}
_ENGINE_RESULT_KEYS: dict[SearchEngine, tuple[str, ...]] = {
    SearchEngine.GOOGLE: ("organic_results",),
    SearchEngine.GOOGLE_NEWS: ("news_results", "organic_results"),
    SearchEngine.GOOGLE_SCHOLAR: ("organic_results",),
}
_SOURCE_TYPES = {
    SearchEngine.GOOGLE: SourceType.WEB_GENERAL,
    SearchEngine.GOOGLE_NEWS: SourceType.NEWS,
    SearchEngine.GOOGLE_SCHOLAR: SourceType.ACADEMIC,
}


def canonicalize_url(url: str) -> str | None:
    """Conservatively normalize a URL for duplicate detection only."""

    parsed = urlsplit(url.strip())
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return None

    filtered_query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in _TRACKING_PARAMETERS
    ]
    return urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path,
            urlencode(filtered_query, doseq=True),
            "",
        )
    )


def is_duplicate_url(url: str, seen_canonical_urls: set[str]) -> bool:
    """Return whether a valid canonical URL has already been observed."""

    canonical_url = canonicalize_url(url)
    return canonical_url is not None and canonical_url in seen_canonical_urls


def normalize_search_results(
    query: SearchQuery,
    payload: dict[str, Any],
    *,
    retrieved_at: datetime | None = None,
) -> list[SearchResult]:
    """Normalize and URL-deduplicate results for one supported search engine."""

    raw_results = _result_collection(query.engine, payload)
    seen_canonical_urls: set[str] = set()
    normalized_results: list[SearchResult] = []
    result_retrieved_at = retrieved_at or datetime.now().astimezone()

    for raw_result in raw_results:
        if not isinstance(raw_result, dict):
            raise SerpApiMalformedResponseError("SerpApi result entries must be JSON objects.")

        result = _normalize_result(query, raw_result, result_retrieved_at)
        if result is None:
            continue
        canonical_url = str(result.canonical_url)
        if canonical_url in seen_canonical_urls:
            continue

        seen_canonical_urls.add(canonical_url)
        normalized_results.append(result)

    return normalized_results


def _result_collection(engine: SearchEngine, payload: dict[str, Any]) -> Iterable[dict[str, Any]]:
    for key in _ENGINE_RESULT_KEYS[engine]:
        if key not in payload:
            continue
        results = payload[key]
        if not isinstance(results, list):
            raise SerpApiMalformedResponseError(f"SerpApi '{key}' must be a list.")
        return results
    return []


def _normalize_result(
    query: SearchQuery,
    raw_result: dict[str, Any],
    retrieved_at: datetime,
) -> SearchResult | None:
    title = raw_result.get("title")
    link = raw_result.get("link")
    if not isinstance(title, str) or not title.strip() or not isinstance(link, str):
        return None

    canonical_url = canonicalize_url(link)
    if canonical_url is None:
        return None

    parsed_url = urlsplit(link)
    position = _position(raw_result.get("position"))
    result_id = uuid5(
        NAMESPACE_URL,
        f"{query.query_id}:{query.engine.value}:{canonical_url}:{position}",
    )
    return SearchResult(
        search_result_id=result_id,
        query_id=query.query_id,
        position=position,
        title=title.strip(),
        url=link,
        canonical_url=canonical_url,
        source_domain=parsed_url.netloc,
        snippet=_optional_text(raw_result.get("snippet")),
        source_type=_SOURCE_TYPES[query.engine],
        publication_date=_publication_date(raw_result),
        author=_author(raw_result),
        retrieved_at=retrieved_at,
        engine=query.engine,
        engine_metadata=_engine_metadata(query.engine, raw_result),
    )


def _position(value: object) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    if isinstance(value, str) and value.isdigit() and int(value) > 0:
        return int(value)
    return None


def _optional_text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _publication_date(raw_result: dict[str, Any]) -> date | None:
    value = raw_result.get(
    "publication_date",
    raw_result.get("published_at", raw_result.get("date")),
)

    if not isinstance(value, str):
        return None

    for date_format in ("%Y-%m-%d", "%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue

    return None


def _author(raw_result: dict[str, Any]) -> str | None:
    direct_author = raw_result.get("author")

    if isinstance(direct_author, str):
        return _optional_text(direct_author)

    if isinstance(direct_author, dict):
        author_name = direct_author.get("name")
        if isinstance(author_name, str):
            return _optional_text(author_name)

    publication_info = raw_result.get("publication_info")
    if not isinstance(publication_info, dict):
        return None

    authors = publication_info.get("authors")
    if not isinstance(authors, list):
        return None

    names = [
        author["name"].strip()
        for author in authors
        if isinstance(author, dict)
        and isinstance(author.get("name"), str)
        and author["name"].strip()
    ]

    return ", ".join(names) if names else None


def _engine_metadata(engine: SearchEngine, raw_result: dict[str, Any]) -> dict[str, Any]:
    keys_by_engine = {
        SearchEngine.GOOGLE: ("rich_snippet",),
        SearchEngine.GOOGLE_NEWS: ("source", "thumbnail"),
        SearchEngine.GOOGLE_SCHOLAR: ("publication_info", "inline_links"),
    }
    return {
        key: raw_result[key]
        for key in keys_by_engine[engine]
        if key in raw_result
    }
