"""API tests that do not require external services."""

from fastapi.testclient import TestClient

from backend.app.api.routes import get_research_orchestrator
from backend.app.main import app
from backend.app.models.claim import OriginalClaim
from backend.app.models.report import (
    OverallAssessment,
    ResearchReport,
)


class FakeResearchOrchestrator:
    """Return a deterministic research report without external services."""

    def research(self, claim: OriginalClaim) -> ResearchReport:
        return ResearchReport(
            original_claim=claim,
            assessment=OverallAssessment.MIXED,
            summary=(
                "Overall assessment: MIXED. "
                "Evaluated 0 atomic claim(s) using 0 evidence item(s)."
            ),
            atomic_claims=[],
            atomic_claim_assessments=[],
            evidence=[],
            evidence_trail=[],
        )


fake_orchestrator = FakeResearchOrchestrator()

app.dependency_overrides[get_research_orchestrator] = (
    lambda: fake_orchestrator
)

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "application": "TruthLens",
    }


def test_research_accepts_a_valid_claim_without_external_services() -> None:
    response = client.post(
        "/api/v1/research",
        json={
            "claim": "Electric vehicles are cheaper to own than petrol cars."
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["original_claim"]["text"] == (
        "Electric vehicles are cheaper to own than petrol cars."
    )
    assert body["assessment"] == "MIXED"
    assert body["evidence"] == []
    assert body["evidence_trail"] == []


def test_research_rejects_an_empty_claim() -> None:
    response = client.post(
        "/api/v1/research",
        json={"claim": ""},
    )

    assert response.status_code == 422


def test_research_rejects_a_whitespace_only_claim() -> None:
    response = client.post(
        "/api/v1/research",
        json={"claim": "   "},
    )

    assert response.status_code == 422