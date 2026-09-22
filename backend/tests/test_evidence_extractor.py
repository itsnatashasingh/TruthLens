from datetime import UTC, datetime
from uuid import uuid4

from backend.app.models.evidence import EvidenceStance, ExcerptKind
from backend.app.models.search import SearchEngine, SearchQuery, SearchResult, SourceType
from backend.app.services.evidence_extractor import EvidenceExtractor


def make_result(snippet: str | None = "Relevant search snippet.") -> SearchResult:
    query = SearchQuery(
        query_id=uuid4(),
        claim_id=uuid4(),
        atomic_claim_id=uuid4(),
        query="electric vehicle maintenance costs",
        engine=SearchEngine.GOOGLE,
    )

    return SearchResult(
        search_result_id=uuid4(),
        query_id=query.query_id,
        position=1,
        title="EV maintenance study",
        url="https://example.org/study",
        canonical_url="https://example.org/study",
        source_domain="example.org",
        snippet=snippet,
        source_type=SourceType.WEB_GENERAL,
        publication_date=None,
        retrieved_at=datetime(2025, 1, 20, tzinfo=UTC),
        engine=SearchEngine.GOOGLE,
        engine_metadata={},
    )


def test_extracts_snippet_as_evidence() -> None:
    result = make_result("Maintenance costs were lower.")

    claim_id = uuid4()
    atomic_claim_id = uuid4()

    evidence = EvidenceExtractor().extract(
        result,
        claim_id=claim_id,
        atomic_claim_id=atomic_claim_id,
    )

    assert evidence is not None
    assert evidence.claim_id == claim_id
    assert evidence.atomic_claim_id == atomic_claim_id
    assert evidence.query_id == result.query_id
    assert evidence.search_result_id == result.search_result_id
    assert evidence.source_title == result.title
    assert str(evidence.source_url) == str(result.canonical_url)
    assert evidence.source_domain == result.source_domain
    assert evidence.source_type is result.source_type
    assert evidence.excerpt == "Maintenance costs were lower."
    assert evidence.excerpt_kind is ExcerptKind.SEARCH_RESULT_SNIPPET


def test_preserves_result_provenance() -> None:
    result = make_result()

    evidence = EvidenceExtractor().extract(
        result,
        claim_id=uuid4(),
        atomic_claim_id=uuid4(),
    )

    assert evidence is not None
    assert evidence.query_id == result.query_id
    assert evidence.search_result_id == result.search_result_id
    assert evidence.retrieved_at == result.retrieved_at
    assert evidence.publication_date == result.publication_date


def test_defaults_to_does_not_address_stance() -> None:
    evidence = EvidenceExtractor().extract(
        make_result(),
        claim_id=uuid4(),
        atomic_claim_id=uuid4(),
    )

    assert evidence is not None
    assert evidence.stance is EvidenceStance.DOES_NOT_ADDRESS


def test_preserves_explicit_stance_when_provided() -> None:
    evidence = EvidenceExtractor().extract(
        make_result(),
        claim_id=uuid4(),
        atomic_claim_id=uuid4(),
        stance=EvidenceStance.CONTEXTUALIZES,
    )

    assert evidence is not None
    assert evidence.stance is EvidenceStance.CONTEXTUALIZES


def test_trims_surrounding_whitespace_from_snippet() -> None:
    evidence = EvidenceExtractor().extract(
        make_result("  Relevant snippet.  "),
        claim_id=uuid4(),
        atomic_claim_id=uuid4(),
    )

    assert evidence is not None
    assert evidence.excerpt == "Relevant snippet."


def test_returns_none_when_snippet_is_missing() -> None:
    evidence = EvidenceExtractor().extract(
        make_result(None),
        claim_id=uuid4(),
        atomic_claim_id=uuid4(),
    )

    assert evidence is None


def test_returns_none_when_snippet_is_blank() -> None:
    evidence = EvidenceExtractor().extract(
        make_result("   "),
        claim_id=uuid4(),
        atomic_claim_id=uuid4(),
    )

    assert evidence is None