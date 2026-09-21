from backend.app.models.claim import OriginalClaim
from backend.app.models.search import SearchEngine
from backend.app.services.claim_analyzer import (
    MAX_ATOMIC_CLAIMS,
    MAX_QUERIES_PER_CLAIM,
    ClaimAnalyzer,
)


def test_decomposes_claim_and_preserves_parent_id():
    claim = OriginalClaim(
        text="Solar energy is renewable and reduces carbon emissions"
    )

    atomic_claims, _ = ClaimAnalyzer().analyze(claim)

    assert len(atomic_claims) == 2
    assert all(item.claim_id == claim.claim_id for item in atomic_claims)
    assert atomic_claims[0].text == "Solar energy is renewable"
    assert atomic_claims[1].text == "reduces carbon emissions"


def test_general_claim_uses_google():
    claim = OriginalClaim(text="Water boils at 100 degrees Celsius")

    atomic_claims, queries = ClaimAnalyzer().analyze(claim)

    assert len(atomic_claims) == 1
    assert len(queries) == 1
    assert queries[0].engine == SearchEngine.GOOGLE


def test_recent_claim_uses_google_news():
    claim = OriginalClaim(
        text="A recent government announcement changed the policy"
    )

    _, queries = ClaimAnalyzer().analyze(claim)

    assert queries[0].engine == SearchEngine.GOOGLE_NEWS


def test_academic_claim_uses_google_scholar():
    claim = OriginalClaim(
        text="A scientific study found that exercise improves sleep"
    )

    _, queries = ClaimAnalyzer().analyze(claim)

    assert queries[0].engine == SearchEngine.GOOGLE_SCHOLAR


def test_claim_with_current_and_academic_signals_uses_at_most_two_engines():
    claim = OriginalClaim(
        text="A recent scientific study was announced in 2026"
    )

    atomic_claims, queries = ClaimAnalyzer().analyze(claim)

    assert len(atomic_claims) == 1
    assert 1 <= len(queries) <= MAX_QUERIES_PER_CLAIM
    assert {query.engine for query in queries} == {
        SearchEngine.GOOGLE_SCHOLAR,
        SearchEngine.GOOGLE_NEWS,
    }


def test_atomic_claim_limit_is_enforced():
    claim = OriginalClaim(
        text="A and B and C and D and E and F and G"
    )

    atomic_claims, _ = ClaimAnalyzer().analyze(claim)

    assert len(atomic_claims) == MAX_ATOMIC_CLAIMS


def test_search_queries_are_linked_to_atomic_claims():
    claim = OriginalClaim(
        text="Solar energy is renewable and reduces carbon emissions"
    )

    atomic_claims, queries = ClaimAnalyzer().analyze(claim)

    assert len(atomic_claims) == 2
    assert len(queries) == 2

    for query in queries:
        assert query.claim_id == claim.claim_id
        assert query.atomic_claim_id in {
            atomic_claim.atomic_claim_id for atomic_claim in atomic_claims
        }


def test_search_query_ids_are_unique():
    claim = OriginalClaim(
        text="Solar energy is renewable and reduces carbon emissions"
    )

    _, queries = ClaimAnalyzer().analyze(claim)

    assert len({query.query_id for query in queries}) == len(queries)