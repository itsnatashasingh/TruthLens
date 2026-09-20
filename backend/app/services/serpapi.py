"""A narrow application-owned client for SerpApi JSON search responses."""

from collections.abc import Mapping
from typing import Any, Protocol

import httpx

from backend.app.config import settings
from backend.app.models.search import SearchQuery
from backend.app.services.exceptions import (
    SerpApiConfigurationError,
    SerpApiInvalidRequestError,
    SerpApiMalformedResponseError,
    SerpApiUpstreamError,
)

SERPAPI_SEARCH_URL = "https://serpapi.com/search.json"


class JsonHttpClient(Protocol):
    """The minimal HTTP boundary required by the SerpApi client."""

    def get(self, url: str, *, params: Mapping[str, str]) -> httpx.Response:
        """Perform one GET request and return its HTTP response."""


class SerpApiClient:
    """Convert one internal SearchQuery into one SerpApi request."""

    def __init__(
        self,
        api_key: str | None = None,
        http_client: JsonHttpClient | None = None,
    ) -> None:
        self._api_key = settings.serpapi_api_key if api_key is None else api_key
        self._http_client = http_client or httpx.Client(timeout=15.0)

    def search(self, query: SearchQuery) -> dict[str, Any]:
        """Submit exactly one SerpApi request and return its JSON object."""

        if not self._api_key or not self._api_key.strip():
            raise SerpApiConfigurationError("SerpApi API key is not configured.")
        if not query.query.strip():
            raise SerpApiInvalidRequestError("Search query must not be blank.")

        parameters = {
            "api_key": self._api_key,
            "engine": query.engine.value,
            "q": query.query,
        }

        try:
            response = self._http_client.get(SERPAPI_SEARCH_URL, params=parameters)
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise SerpApiUpstreamError(
                f"SerpApi returned HTTP status {error.response.status_code}."
            ) from error
        except httpx.RequestError as error:
            raise SerpApiUpstreamError("SerpApi request failed.") from error

        try:
            payload = response.json()
        except ValueError as error:
            raise SerpApiMalformedResponseError("SerpApi response was not valid JSON.") from error

        if not isinstance(payload, dict):
            raise SerpApiMalformedResponseError("SerpApi response must be a JSON object.")
        if isinstance(payload.get("error"), str):
            raise SerpApiUpstreamError("SerpApi reported an API error.")

        return payload
