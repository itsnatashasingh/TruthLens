"""Unit tests for the isolated, mocked SerpApi boundary and normalizer."""

from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest

from backend.app.models.search import SearchEngine, SearchQuery, SourceType
from backend.app.services.exceptions import (
    SerpApiConfigurationError,
    SerpApiMalformedResponseError,
    SerpApiUpstreamError,
)
from backend.app.services.result_normalizer import (
    canonicalize_url,
    is_duplicate_url,
    normalize_search_results,
)
from backend.app.services.serpapi import SERPAPI_SEARCH_URL, SerpApiClient


def make_query(engine: SearchEngine = SearchEngine.GOOGLE) -> SearchQuery:
    return SearchQuery(
        query_id=uuid4(),
        claim_id=uuid4(),
        atomic_claim_id=uuid4(),
        query="electric vehicle maintenance costs",
        engine=engine,
    )


def test_normalizes_google_organic_results_and_preserves_positions() -> None:
    query = make_query()
    payload = {
        "organic_results": [
            {
                "position": 1,
                "title": "EV maintenance study",
                "link": "https://example.org/study?utm_source=search",
                "snippet": "Maintenance costs were lower.",
                "date": "2025-01-15",
                "author": "Research Team",
            },
            {
                "position": 2,
                "title": "Second source",
                "link": "https://example.net/report",
            },
        ]
    }

    results = normalize_search_results(
        query,
        payload,
        retrieved_at=datetime(2025, 1, 20, tzinfo=UTC),
    )

    assert [result.position for result in results] == [1, 2]
    assert str(results[0].canonical_url) == "https://example.org/study"
    assert results[0].source_type is SourceType.WEB_GENERAL
    assert results[0].publication_date.isoformat() == "2025-01-15"
    assert results[0].author == "Research Team"


def test_normalizes_google_news_results() -> None:
    query = make_query(SearchEngine.GOOGLE_NEWS)
    payload = {
        "news_results": [
            {
                "position": 3,
                "title": "EV costs in the news",
                "link": "https://news.example.com/ev-costs",
                "snippet": "A current cost comparison.",
                "date": "Jan 20, 2025",
                "source": "Example News",
            }
        ]
    }

    result = normalize_search_results(query, payload)[0]

    assert result.source_type is SourceType.NEWS
    assert result.position == 3
    assert result.publication_date.isoformat() == "2025-01-20"
    assert result.engine_metadata["source"] == "Example News"


def test_normalizes_google_scholar_results() -> None:
    query = make_query(SearchEngine.GOOGLE_SCHOLAR)
    payload = {
        "organic_results": [
            {
                "position": 1,
                "title": "Academic EV study",
                "link": "https://doi.org/10.1000/example",
                "snippet": "A scholarly comparison.",
                "publication_info": {
                    "authors": [{"name": "Ada Example"}, {"name": "Sam Scholar"}]
                },
            }
        ]
    }

    result = normalize_search_results(query, payload)[0]

    assert result.source_type is SourceType.ACADEMIC
    assert result.author == "Ada Example, Sam Scholar"
    assert result.engine_metadata["publication_info"] == payload["organic_results"][0]["publication_info"]


def test_normalizer_tolerates_missing_optional_fields() -> None:
    result = normalize_search_results(
        make_query(),
        {"organic_results": [{"title": "Minimal", "link": "https://example.org/minimal"}]},
    )[0]

    assert result.position is None
    assert result.snippet is None
    assert result.publication_date is None
    assert result.author is None


def test_url_canonicalization_and_deduplication_are_conservative() -> None:
    query = make_query()
    payload = {
        "organic_results": [
            {"title": "Original", "link": "https://example.org/page?utm_source=search#section"},
            {"title": "Duplicate", "link": "https://example.org/page"},
            {"title": "Distinct", "link": "https://example.org/page?edition=india"},
        ]
    }

    results = normalize_search_results(query, payload)

    assert canonicalize_url("HTTPS://EXAMPLE.ORG/page?utm_source=x#intro") == "https://example.org/page"
    assert is_duplicate_url("https://example.org/page", {"https://example.org/page"})
    assert [result.title for result in results] == ["Original", "Distinct"]


def test_client_requires_an_api_key_without_calling_http() -> None:
    client = SerpApiClient(api_key="")

    with pytest.raises(SerpApiConfigurationError):
        client.search(make_query())


def test_client_wraps_upstream_http_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, request=request, json={"error": "upstream failure"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        client = SerpApiClient(api_key="test-key", http_client=http_client)

        with pytest.raises(SerpApiUpstreamError):
            client.search(make_query())


def test_client_rejects_malformed_json_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, request=request, content=b"not-json")

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        client = SerpApiClient(api_key="test-key", http_client=http_client)

        with pytest.raises(SerpApiMalformedResponseError):
            client.search(make_query())


def test_one_internal_search_makes_one_mocked_external_request() -> None:
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        assert str(request.url).startswith(SERPAPI_SEARCH_URL)
        assert request.url.params["engine"] == "google"
        assert request.url.params["q"] == "electric vehicle maintenance costs"
        assert request.url.params["api_key"] == "test-key"
        return httpx.Response(200, request=request, json={"organic_results": []})

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        client = SerpApiClient(api_key="test-key", http_client=http_client)
        assert client.search(make_query()) == {"organic_results": []}

    assert request_count == 1
