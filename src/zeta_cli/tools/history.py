from __future__ import annotations

from dataclasses import dataclass

from zeta_cli.api.models import ToolCall
from zeta_cli.tools.fingerprinting import tool_fingerprint
from zeta_cli.tools.results import ToolResult


@dataclass(frozen=True)
class ToolHistoryEntry:
    call: ToolCall
    result: ToolResult
    fingerprint: str


class ToolHistory:
    """In-memory ordered history of dispatched tools."""

    def __init__(self) -> None:
        self._entries: list[ToolHistoryEntry] = []

    def record(
        self,
        call: ToolCall,
        result: ToolResult,
    ) -> None:
        self._entries.append(
            ToolHistoryEntry(
                call=call,
                result=result,
                fingerprint=tool_fingerprint(
                    call.name,
                    call.arguments,
                ),
            )
        )

    def entries(self) -> list[ToolHistoryEntry]:
        return list(self._entries)
