from zeta_cli.errors import (
    ZetaError,
    ConfigurationError,
    APIError,
    ToolError,
    VerificationError,
    RecoveryError,
)


def test_all_errors_inherit_from_zeta_error():
    error_types = (
        ConfigurationError,
        APIError,
        ToolError,
        VerificationError,
        RecoveryError,
    )

    for error_type in error_types:
        assert issubclass(error_type, ZetaError)


def test_error_message_is_preserved():
    error = ConfigurationError("invalid configuration")

    assert str(error) == "invalid configuration"


def test_api_error_can_store_status_code():
    error = APIError("rate limited", status_code=429)

    assert str(error) == "rate limited"
    assert error.status_code == 429
