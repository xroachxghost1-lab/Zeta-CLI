from __future__ import annotations

from zeta_cli.errors import APIError


class AuthenticationError(APIError):
    """API authentication or authorization failure."""


class RateLimitError(APIError):
    """API rate-limit response."""

    def __init__(
        self,
        message: str = "rate limited",
        *,
        status_code: int | None = 429,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code)
        self.retry_after = retry_after


class InvalidRequestError(APIError):
    """Invalid request sent to the API."""


class ModelNotFoundError(APIError):
    """Requested model does not exist or is unavailable."""


class ServerError(APIError):
    """Remote API server failure."""


class NetworkError(APIError):
    """Network, connection, or transport failure."""


class TimeoutError(APIError):
    """API request timed out."""


def is_retryable(error: APIError) -> bool:
    """Return whether an API error is normally safe to retry."""

    # Explicit HTTP status codes always take precedence.
    if error.status_code is not None:
        return error.status_code in {408, 429, 500, 502, 503, 504}

    return isinstance(
        error,
        (
            RateLimitError,
            ServerError,
            NetworkError,
            TimeoutError,
        ),
    )
