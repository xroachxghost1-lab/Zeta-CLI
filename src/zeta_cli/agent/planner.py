from __future__ import annotations

from typing import Any

from zeta_cli.api.client import APIClient
from zeta_cli.api.models import CompletionResult, Message
from zeta_cli.config import Settings


class Planner:
    """Build planning prompts and delegate planning to the API client."""

    def __init__(self, api: APIClient, settings: Settings) -> None:
        self.api = api
        self.settings = settings

    def plan(
        self,
        goal: str,
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> CompletionResult:
        messages = [
            Message(
                role="system",
                content=(
                    "You are the planning component of Zeta-CLI. "
                    "Analyze the user's coding goal and determine the "
                    "next actions required to accomplish it. "
                    "Do not claim work has been completed unless it has "
                    "actually been verified."
                ),
            ),
            Message(
                role="user",
                content=goal,
            ),
        ]

        return self.api.complete(
            messages,
            model=self.settings.model,
            reasoning_effort=self.settings.reasoning_effort,
            tools=tools,
        )
