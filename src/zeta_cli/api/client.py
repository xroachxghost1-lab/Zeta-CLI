from __future__ import annotations

from typing import Any, Iterable

from zeta_cli.api.inception import InceptionProvider
from zeta_cli.api.models import CompletionResult, Message, ModelInfo
from zeta_cli.config import Settings


class APIClient:
    """Provider-neutral API boundary for Zeta-CLI."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.provider = InceptionProvider(settings)

    def complete(
        self,
        messages: Iterable[Message],
        *,
        model: str | None = None,
        reasoning_effort: str | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> CompletionResult:
        return self.provider.complete(
            messages,
            model=model,
            reasoning_effort=reasoning_effort,
            tools=tools,
        )

    def edit(
        self,
        messages: Iterable[Message],
        *,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        presence_penalty: float | None = None,
    ) -> CompletionResult:
        return self.provider.edit(
            messages,
            model=model or self.settings.edit_model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            presence_penalty=presence_penalty,
        )

    def stream(
        self,
        messages: Iterable[Message],
        *,
        model: str | None = None,
        reasoning_effort: str | None = None,
        tools: list[dict[str, Any]] | None = None,
    ):
        return self.provider.stream(
            messages,
            model=model or self.settings.model,
            reasoning_effort=reasoning_effort,
            tools=tools,
        )

    def fim(
        self,
        *,
        model: str | None = None,
        prompt: str,
        suffix: str | None = None,
        max_tokens: int | None = None,
        top_p: float | None = None,
        top_k: int | None = None,
        temperature: float | None = None,
        frequency_penalty: float | None = None,
        presence_penalty: float | None = None,
        repetition_penalty: float | None = None,
        stop: list[str] | None = None,
    ) -> CompletionResult:
        return self.provider.fim(
            model=model or self.settings.model,
            prompt=prompt,
            suffix=suffix,
            max_tokens=max_tokens,
            top_p=top_p,
            top_k=top_k,
            temperature=temperature,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            repetition_penalty=repetition_penalty,
            stop=stop,
        )

    def models(self) -> list[ModelInfo]:
        return self.provider.models()
