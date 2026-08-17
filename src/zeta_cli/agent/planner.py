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

    def continue_task(
        self,
        goal: str,
        evidence: str,
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> CompletionResult:
        messages = [
            Message(
                role="system",
                content=(
                    "You are the autonomous coding component of Zeta-CLI. "
                    "Continue working on the user's goal. Inspect the "
                    "evidence from previous actions, determine what remains "
                    "to be done, and use tools to make actual progress. "
                    "Do not claim completion unless the goal has been "
                    "verified. If more work is required, emit the necessary "
                    "tool calls."
                ),
            ),
            Message(
                role="user",
                content=(
                    f"Original goal:\n{goal}\n\n"
                    f"Previous execution evidence:\n{evidence}\n\n"
                    "Continue the task."
                ),
            ),
        ]

        return self.api.complete(
            messages,
            model=self.settings.model,
            reasoning_effort=self.settings.reasoning_effort,
            tools=tools,
        )

    def finalize(self, goal: str, evidence: str) -> CompletionResult:
        messages = [
            Message(
                role="system",
                content=(
                    "You are the final response component of Zeta-CLI. "
                    "Answer the user's original request using only the "
                    "verified evidence provided. Be concise and directly "
                    "answer the user. Do not mention internal lifecycle "
                    "phases, tools, watchdogs, or implementation details."
                ),
            ),
            Message(
                role="user",
                content=(
                    f"Original request:\n{goal}\n\n"
                    f"Verified evidence:\n{evidence}"
                ),
            ),
        ]

        return self.api.complete(
            messages,
            model=self.settings.model,
            reasoning_effort=self.settings.reasoning_effort,
        )
