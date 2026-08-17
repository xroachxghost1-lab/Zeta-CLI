from zeta_cli.api.errors import (
    AuthenticationError,
    InvalidRequestError,
    ModelNotFoundError,
    NetworkError,
    RateLimitError,
    ServerError,
    TimeoutError,
    is_retryable,
)


def test_rate_limit_error_contains_retry_after():
    error = RateLimitError(
        retry_after=3.5,
    )

    assert error.status_code == 429
    assert error.retry_after == 3.5
    assert is_retryable(error)


def test_transient_errors_are_retryable():
    assert is_retryable(ServerError("server failure"))
    assert is_retryable(NetworkError("connection failed"))
    assert is_retryable(TimeoutError("timed out"))


def test_authentication_error_is_not_retryable():
    assert not is_retryable(AuthenticationError("unauthorized"))


def test_invalid_request_is_not_retryable():
    assert not is_retryable(InvalidRequestError("bad request"))


def test_model_not_found_is_not_retryable():
    assert not is_retryable(ModelNotFoundError("missing model"))


def test_status_code_can_determine_retryability():
    assert is_retryable(ServerError("temporary", status_code=503))
    assert is_retryable(ServerError("gateway", status_code=502))
    assert not is_retryable(ServerError("bad request", status_code=400))
