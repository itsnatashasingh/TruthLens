from backend.app.models.claim import AtomicClaim
from backend.app.models.search import SearchEngine
from backend.app.services.search_planner import (
    MAX_QUERIES_PER_CLAIM,
    SearchPlanner,
)


def make_claim(text: str) -> AtomicClaim:
    from backend.app.models.claim import OriginalClaim

    original_claim = OriginalClaim(text=text)

    return AtomicClaim(
        claim_id=original_claim.claim_id,
        text=text,
    )


def test_general_claim_uses_google():
    claim = make_claim("Water boils at 100 degrees Celsius")

    queries = SearchPlanner().plan(claim)

    assert len(queries) == 1
    assert queries[0].engine == SearchEngine.GOOGLE


def test_recent_claim_uses_google_news():
    claim = make_claim(
        "A recent government announcement changed the policy"
    )

    queries = SearchPlanner().plan(claim)

    assert len(queries) == 1
    assert queries[0].engine == SearchEngine.GOOGLE_NEWS


def test_academic_claim_uses_google_scholar():
    claim = make_claim(
        "A scientific study found that exercise improves sleep"
    )

    queries = SearchPlanner().plan(claim)

    assert len(queries) == 1
    assert queries[0].engine == SearchEngine.GOOGLE_SCHOLAR


def test_current_academic_claim_uses_at_most_two_queries():
    claim = make_claim(
        "A recent scientific study was announced in 2026"
    )

    queries = SearchPlanner().plan(claim)

    assert len(queries) == MAX_QUERIES_PER_CLAIM
    assert {query.engine for query in queries} == {
        SearchEngine.GOOGLE_SCHOLAR,
        SearchEngine.GOOGLE_NEWS,
    }


def test_queries_reference_atomic_claim():
    claim = make_claim("Solar energy is a renewable source")

    queries = SearchPlanner().plan(claim)

    assert len(queries) == 1
    assert queries[0].claim_id == claim.claim_id
    assert queries[0].atomic_claim_id == claim.atomic_claim_id


def test_query_ids_are_unique():
    claim = make_claim(
        "A recent scientific study was announced in 2026"
    )

    queries = SearchPlanner().plan(claim)

    assert len({query.query_id for query in queries}) == len(queries)


def test_queries_are_targeted():
    claim = make_claim("Solar energy is a renewable source")

    queries = SearchPlanner().plan(claim)

    assert queries[0].query != claim.text
    assert "evidence" in queries[0].query