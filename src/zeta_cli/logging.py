from __future__ import annotations

import re


_API_KEY_PATTERN = re.compile(
    r"(?i)(INCEPTION_API_KEY\s*[=:]\s*)([^\s\"']+)"
)

_BEARER_PATTERN = re.compile(
    r"(?i)(Authorization\s*:\s*Bearer\s+)([^\s]+)"
)


def redact(text: str) -> str:
    """Redact API keys and bearer tokens from log-safe text."""

    text = _API_KEY_PATTERN.sub(r"\1[REDACTED]", text)
    text = _BEARER_PATTERN.sub(r"\1[REDACTED]", text)

    return text
