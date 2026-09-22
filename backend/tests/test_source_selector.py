from datetime import UTC, datetime
from uuid import uuid4

from backend.app.models.search import SearchEngine, SearchQuery, SearchResult, SourceType
from backend.app.services.source_selector import SourceSelector


def make_result(
    *,
    title: str = "Example source",
    snippet: str | None = "Relevant search snippet.",
) -> SearchResult:
    query = SearchQuery(
        query_id=uuid4(),
        claim_id=uuid4(),
        atomic_claim_id=uuid4(),
        query="test query",
        engine=SearchEngine.GOOGLE,
    )

    return SearchResult(
        search_result_id=uuid4(),
        query_id=query.query_id,
        position=1,
        title=title,
        url="https://example.org/source",
        canonical_url="https://example.org/source",
        source_domain="example.org",
        snippet=snippet,
        source_type=SourceType.WEB_GENERAL,
        publication_date=None,
        retrieved_at=datetime.now(UTC),
        engine=SearchEngine.GOOGLE,
        engine_metadata={},
    )


def test_selects_results_with_usable_snippets():
    results = [
        make_result(title="First source"),
        make_result(title="Second source"),
    ]

    selected = SourceSelector().select(results)

    assert len(selected) == 2
    assert selected == results


def test_skips_results_without_snippets():
    results = [
        make_result(title="No snippet", snippet=None),
        make_result(title="Usable source"),
    ]

    selected = SourceSelector().select(results)

    assert len(selected) == 1
    assert selected[0].title == "Usable source"


def test_skips_blank_snippets():
    results = [
        make_result(title="Blank snippet", snippet="   "),
        make_result(title="Usable source"),
    ]

    selected = SourceSelector().select(results)

    assert len(selected) == 1
    assert selected[0].title == "Usable source"


def test_respects_limit():
    results = [
        make_result(title="First"),
        make_result(title="Second"),
        make_result(title="Third"),
    ]

    selected = SourceSelector().select(results, limit=2)

    assert len(selected) == 2
    assert [result.title for result in selected] == ["First", "Second"]


def test_zero_or_negative_limit_returns_empty():
    results = [make_result()]

    assert SourceSelector().select(results, limit=0) == []
    assert SourceSelector().select(results, limit=-1) == []


def test_preserves_input_order():
    results = [
        make_result(title="Third"),
        make_result(title="First"),
        make_result(title="Second"),
    ]

    selected = SourceSelector().select(results)

    assert [result.title for result in selected] == [
        "Third",
        "First",
        "Second",
    ]


def test_does_not_select_duplicate_result_ids():
    result = make_result()

    selected = SourceSelector().select([result, result])

    assert len(selected) == 1
    assert selected[0] is result