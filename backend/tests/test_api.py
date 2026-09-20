"""API tests that do not require external services."""

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "application": "TruthLens"}


def test_research_accepts_a_valid_claim_without_external_services() -> None:
    response = client.post(
        "/api/v1/research",
        json={"claim": "Electric vehicles are cheaper to own than petrol cars."},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "not_implemented",
        "detail": "Research execution has not yet been implemented.",
    }


def test_research_rejects_an_empty_claim() -> None:
    response = client.post("/api/v1/research", json={"claim": ""})

    assert response.status_code == 422


def test_research_rejects_a_whitespace_only_claim() -> None:
    response = client.post("/api/v1/research", json={"claim": "   "})

    assert response.status_code == 422
