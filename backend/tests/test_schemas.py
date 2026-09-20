"""Focused tests for the initial API and domain schema contracts."""

import pytest
from pydantic import ValidationError

from backend.app.api.schemas import ResearchRequest
from backend.app.models.evidence import EvidenceStance
from backend.app.models.report import OverallAssessment


def test_research_request_strips_surrounding_whitespace() -> None:
    request = ResearchRequest(claim="  A factual claim.  ")

    assert request.claim == "A factual claim."


def test_research_request_rejects_a_blank_claim() -> None:
    with pytest.raises(ValidationError):
        ResearchRequest(claim="   ")


def test_documented_assessment_and_stance_values_are_available() -> None:
    assert OverallAssessment.INSUFFICIENT_EVIDENCE == "INSUFFICIENT_EVIDENCE"
    assert EvidenceStance.DOES_NOT_ADDRESS == "DOES_NOT_ADDRESS"
