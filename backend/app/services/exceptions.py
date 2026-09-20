"""Application-level exceptions for the SerpApi integration."""


class SerpApiError(Exception):
    """Base exception for SerpApi integration failures."""


class SerpApiConfigurationError(SerpApiError):
    """Raised when required SerpApi configuration is absent."""


class SerpApiInvalidRequestError(SerpApiError):
    """Raised when an internal search request cannot be sent safely."""


class SerpApiUpstreamError(SerpApiError):
    """Raised when SerpApi cannot successfully serve a request."""


class SerpApiMalformedResponseError(SerpApiError):
    """Raised when a SerpApi response has an unexpected structure."""
