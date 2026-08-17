from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from zeta_cli.tools.results import ToolResult


@dataclass(frozen=True)
class Assessment:
    """Assessment of a tool execution result."""

    passed: bool
    value: Any = None
    error: str | None = None


class Assessor:
    """Assess the outcome of a tool execution."""

    def assess(self, result: ToolResult) -> Assessment:
        if not isinstance(result, ToolResult):
            raise TypeError("assess expects a ToolResult")

        return Assessment(
            passed=result.ok,
            value=result.value,
            error=result.error,
        )
