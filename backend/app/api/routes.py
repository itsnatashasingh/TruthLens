"""API routes available during the project-foundation milestone."""

from fastapi import APIRouter

from backend.app.api.schemas import (
    HealthResponse,
    ResearchNotImplementedResponse,
    ResearchRequest,
)
from backend.app.config import settings

router = APIRouter(prefix="/api/v1", tags=["api"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return a minimal response proving that the API is running."""

    return HealthResponse(application=settings.app_name)


@router.post("/research", response_model=ResearchNotImplementedResponse)
def research(_: ResearchRequest) -> ResearchNotImplementedResponse:
    """Validate a claim without invoking research services in this milestone."""

    return ResearchNotImplementedResponse()
