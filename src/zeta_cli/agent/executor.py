from __future__ import annotations

from zeta_cli.api.models import CompletionResult
from zeta_cli.tools.results import ToolResult


class Executor:
    """Execute tool calls produced by the planner."""

    def __init__(self, dispatcher) -> None:
        self.dispatcher = dispatcher

    def execute(self, planning_result: CompletionResult) -> ToolResult:
        if not planning_result.tool_calls:
            raise ValueError("no tool call in planning result")

        return self.dispatcher.dispatch(
            planning_result.tool_calls[0]
        )
