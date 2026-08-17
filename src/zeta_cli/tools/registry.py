from __future__ import annotations

from collections.abc import Callable
from typing import Any


class ToolRegistry:
    """Registry of executable Zeta tools."""

    def __init__(self) -> None:
        self._tools: dict[str, Callable[[dict[str, Any]], Any]] = {}

    def register(
        self,
        name: str,
        tool: Callable[[dict[str, Any]], Any],
    ) -> None:
        if name in self._tools:
            raise ValueError(f"tool already registered: {name!r}")

        self._tools[name] = tool

    def get(
        self,
        name: str,
    ) -> Callable[[dict[str, Any]], Any] | None:
        return self._tools.get(name)

    def names(self) -> tuple[str, ...]:
        return tuple(self._tools)
