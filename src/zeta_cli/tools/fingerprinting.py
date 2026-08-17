from __future__ import annotations

import hashlib
import json
from typing import Any


def tool_fingerprint(name: str, arguments: dict[str, Any]) -> str:
    payload = {
        "name": name,
        "arguments": arguments,
    }

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def tool_result_fingerprint(result: "ToolResult") -> str:
    """Return a stable fingerprint for a normalized tool result."""
    from zeta_cli.tools.results import ToolResult

    if not isinstance(result, ToolResult):
        raise TypeError("tool_result_fingerprint expects a ToolResult")

    payload = {
        "ok": result.ok,
        "value": result.value,
        "error": result.error,
    }

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()
