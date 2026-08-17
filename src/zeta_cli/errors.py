from __future__ import annotations


class ZetaError(Exception):
    """Base exception for all Zeta-CLI errors."""


class ConfigurationError(ZetaError):
    """Invalid or incomplete Zeta configuration."""


class APIError(ZetaError):
    """Error communicating with an external API."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code


class ToolError(ZetaError):
    """Tool execution or dispatch failure."""


class VerificationError(ZetaError):
    """Verification failure."""


class RecoveryError(ZetaError):
    """Failure while attempting recovery."""
