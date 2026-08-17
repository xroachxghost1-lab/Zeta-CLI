from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolResult:
    """Normalized result of a tool execution."""

    ok: bool
    value: Any = None
    error: str | None = None

    @classmethod
    def from_value(cls, value: Any) -> ToolResult:
        return cls(ok=True, value=value)

    @classmethod
    def from_exception(cls, error: Exception) -> ToolResult:
        return cls(ok=False, error=str(error))
