from datetime import UTC, datetime
from uuid import uuid4

import pytest

from backend.app.models.search import SearchEngine, SearchQuery, SourceType
from backend.app.services.exceptions import SerpApiMalformedResponseError
from backend.app.services.result_normalizer import (
    canonicalize_url,
    normalize_search_results,
)


def make_query(engine: SearchEngine = SearchEngine.GOOGLE) -> SearchQuery:
    return SearchQuery(
        query_id=uuid4(),
        claim_id=uuid4(),
        atomic_claim_id=uuid4(),
        query="electric vehicle maintenance costs",
        engine=engine,
    )


def test_google_results_are_normalized():
    query = make_query()

    payload = {
        "organic_results": [
            {
                "position": 1,
                "title": "EV maintenance study",
                "link": "https://example.org/study?utm_source=search",
                "snippet": "Maintenance costs were lower.",
                "date": "2025-01-15",
            }
        ]
    }

    results = normalize_search_results(
        query,
        payload,
        retrieved_at=datetime(2025, 1, 20, tzinfo=UTC),
    )

    assert len(results) == 1
    assert results[0].title == "EV maintenance study"
    assert results[0].source_type is SourceType.WEB_GENERAL
    assert results[0].position == 1
    assert results[0].snippet == "Maintenance costs were lower."
    assert results[0].publication_date.isoformat() == "2025-01-15"
    assert results[0].retrieved_at == datetime(2025, 1, 20, tzinfo=UTC)


def test_google_news_uses_news_source_type_and_metadata():
    query = make_query(SearchEngine.GOOGLE_NEWS)

    payload = {
        "news_results": [
            {
                "position": 1,
                "title": "EV costs in the news",
                "link": "https://news.example.com/ev-costs",
                "snippet": "A current cost comparison.",
                "published_at": "Jan 20, 2025",
                "author": {"name": "Example Reporter"},
                "source": "Example News",
            }
        ]
    }

    result = normalize_search_results(query, payload)[0]

    assert result.source_type is SourceType.NEWS
    assert result.author == "Example Reporter"
    assert result.publication_date.isoformat() == "2025-01-20"
    assert result.engine_metadata["source"] == "Example News"


def test_google_scholar_authors_are_normalized():
    query = make_query(SearchEngine.GOOGLE_SCHOLAR)

    payload = {
        "organic_results": [
            {
                "position": 1,
                "title": "Academic EV study",
                "link": "https://doi.org/10.1000/example",
                "snippet": "A scholarly comparison.",
                "publication_info": {
                    "authors": [
                        {"name": "Ada Example"},
                        {"name": "Sam Scholar"},
                    ]
                },
            }
        ]
    }

    result = normalize_search_results(query, payload)[0]

    assert result.source_type is SourceType.ACADEMIC
    assert result.author == "Ada Example, Sam Scholar"
    assert result.engine_metadata["publication_info"] == (
        payload["organic_results"][0]["publication_info"]
    )


def test_duplicate_urls_are_removed_after_canonicalization():
    query = make_query()

    payload = {
        "organic_results": [
            {
                "title": "Original",
                "link": "https://example.org/page?utm_source=search#section",
            },
            {
                "title": "Duplicate",
                "link": "https://example.org/page",
            },
            {
                "title": "Distinct edition",
                "link": "https://example.org/page?edition=india",
            },
        ]
    }

    results = normalize_search_results(query, payload)

    assert [result.title for result in results] == [
        "Original",
        "Distinct edition",
    ]


def test_canonicalization_removes_tracking_parameters():
    assert (
        canonicalize_url(
            "HTTPS://EXAMPLE.ORG/page"
            "?utm_source=x&utm_campaign=test&gclid=abc#intro"
        )
        == "https://example.org/page"
    )


def test_canonicalization_preserves_non_tracking_query_parameters():
    assert (
        canonicalize_url(
            "https://example.org/page?edition=india&utm_source=search"
        )
        == "https://example.org/page?edition=india"
    )


def test_invalid_urls_are_skipped():
    query = make_query()

    payload = {
        "organic_results": [
            {
                "title": "Invalid",
                "link": "not-a-valid-url",
            },
            {
                "title": "Valid",
                "link": "https://example.org/valid",
            },
        ]
    }

    results = normalize_search_results(query, payload)

    assert len(results) == 1
    assert results[0].title == "Valid"


def test_missing_optional_fields_are_allowed():
    query = make_query()

    payload = {
        "organic_results": [
            {
                "title": "Minimal result",
                "link": "https://example.org/minimal",
            }
        ]
    }

    result = normalize_search_results(query, payload)[0]

    assert result.position is None
    assert result.snippet is None
    assert result.publication_date is None
    assert result.author is None
    assert result.engine_metadata == {}


def test_malformed_result_collection_raises_error():
    query = make_query()

    payload = {
        "organic_results": "not-a-list",
    }

    with pytest.raises(SerpApiMalformedResponseError):
        normalize_search_results(query, payload)


def test_malformed_result_entry_raises_error():
    query = make_query()

    payload = {
        "organic_results": [
            "not-a-result-object",
        ]
    }

    with pytest.raises(SerpApiMalformedResponseError):
        normalize_search_results(query, payload)


def test_result_ids_are_stable_for_same_input():
    query = make_query()

    payload = {
        "organic_results": [
            {
                "position": 1,
                "title": "Stable result",
                "link": "https://example.org/stable",
            }
        ]
    }

    first = normalize_search_results(query, payload)[0]
    second = normalize_search_results(query, payload)[0]

    assert first.search_result_id == second.search_result_id