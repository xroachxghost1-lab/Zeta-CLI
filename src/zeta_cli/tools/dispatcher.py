from __future__ import annotations

from zeta_cli.api.models import ToolCall
from zeta_cli.errors import ToolError
from zeta_cli.tools.results import ToolResult
from zeta_cli.tools.safety import ToolSafety


class ToolDispatcher:
    """Dispatch registered tools through an optional safety policy."""

    def __init__(
        self,
        registry,
        safety: ToolSafety | None = None,
    ) -> None:
        self.registry = registry
        self.safety = safety

    def dispatch(self, call: ToolCall) -> ToolResult:
        tool = self.registry.get(call.name)

        if tool is None:
            raise ToolError(f"unknown tool: {call.name!r}")

        if self.safety is not None and not self.safety.is_allowed(call.name):
            raise ToolError(f"tool is not allowed: {call.name!r}")

        try:
            return ToolResult.from_value(tool(call.arguments))
        except Exception as error:
            return ToolResult.from_exception(error)
