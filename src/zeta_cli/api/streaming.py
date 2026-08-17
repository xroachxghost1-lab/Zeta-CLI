from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from zeta_cli.api.models import ToolCall


@dataclass(frozen=True)
class StreamEvent:
    """Provider-neutral representation of one streaming API event."""

    content: str = ""
    role: str | None = None
    finish_reason: str | None = None
    model: str | None = None
    reasoning_summary: str | None = None
    reasoning_status: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: Any = None
