from __future__ import annotations

from typing import Any, Iterable, Iterator

import inceptionai

from zeta_cli.api.errors import (
    AuthenticationError,
    InvalidRequestError,
    ModelNotFoundError,
    NetworkError,
    RateLimitError,
    ServerError,
    TimeoutError,
)
from zeta_cli.api.models import CompletionResult, Message, ModelInfo, ToolCall
from zeta_cli.api.streaming import StreamEvent
from zeta_cli.config import Settings


class InceptionProvider:
    """Adapter between Zeta-CLI and the inceptionai SDK."""

    def __init__(self, settings: Settings) -> None:
        if not settings.api_key:
            raise AuthenticationError("INCEPTION_API_KEY is not configured")

        self.settings = settings
        self.client = inceptionai.Client(
            api_key=settings.api_key,
            base_url=settings.api_base,
        )

    def complete(
        self,
        messages: Iterable[Message],
        *,
        model: str | None = None,
        reasoning_effort: str | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> CompletionResult:
        payload = [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in messages
        ]

        kwargs: dict[str, Any] = {
            "messages": payload,
            "model": model or self.settings.model,
        }

        if reasoning_effort is not None:
            kwargs["reasoning_effort"] = reasoning_effort

        if tools:
            kwargs["tools"] = tools

        try:
            response = self.client.chat.completions.create(**kwargs)
        except inceptionai.AuthenticationError as exc:
            raise AuthenticationError(str(exc)) from exc
        except inceptionai.RateLimitError as exc:
            retry_after = None
            response_obj = getattr(exc, "response", None)

            if response_obj is not None:
                retry_after_header = response_obj.headers.get("retry-after")
                if retry_after_header:
                    try:
                        retry_after = float(retry_after_header)
                    except ValueError:
                        pass

            raise RateLimitError(
                str(exc),
                retry_after=retry_after,
            ) from exc
        except inceptionai.APITimeoutError as exc:
            raise TimeoutError(str(exc)) from exc
        except inceptionai.APIConnectionError as exc:
            raise NetworkError(str(exc)) from exc
        except inceptionai.BadRequestError as exc:
            raise InvalidRequestError(str(exc)) from exc
        except inceptionai.NotFoundError as exc:
            raise ModelNotFoundError(str(exc)) from exc
        except inceptionai.InternalServerError as exc:
            raise ServerError(str(exc)) from exc
        except inceptionai.APIStatusError as exc:
            status_code = getattr(exc.response, "status_code", None)
            raise ServerError(
                str(exc),
                status_code=status_code,
            ) from exc

        return self._completion_result(response)

    def stream(
        self,
        messages: Iterable[Message],
        *,
        model: str | None = None,
        reasoning_effort: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        diffusing: bool = False,
    ) -> Iterator[StreamEvent]:
        """Stream chat completion events from the Inception API."""

        payload = [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in messages
        ]

        kwargs: dict[str, Any] = {
            "messages": payload,
            "model": model or self.settings.model,
            "stream": True,
            "diffusing": diffusing,
        }

        if reasoning_effort is not None:
            kwargs["reasoning_effort"] = reasoning_effort

        if tools:
            kwargs["tools"] = tools

        try:
            response_stream = self.client.chat.completions.create(**kwargs)
        except inceptionai.AuthenticationError as exc:
            raise AuthenticationError(str(exc)) from exc
        except inceptionai.RateLimitError as exc:
            retry_after = None
            response_obj = getattr(exc, "response", None)

            if response_obj is not None:
                retry_after_header = response_obj.headers.get("retry-after")
                if retry_after_header:
                    try:
                        retry_after = float(retry_after_header)
                    except ValueError:
                        pass

            raise RateLimitError(
                str(exc),
                retry_after=retry_after,
            ) from exc
        except inceptionai.APITimeoutError as exc:
            raise TimeoutError(str(exc)) from exc
        except inceptionai.APIConnectionError as exc:
            raise NetworkError(str(exc)) from exc
        except inceptionai.BadRequestError as exc:
            raise InvalidRequestError(str(exc)) from exc
        except inceptionai.NotFoundError as exc:
            raise ModelNotFoundError(str(exc)) from exc
        except inceptionai.InternalServerError as exc:
            raise ServerError(str(exc)) from exc
        except inceptionai.APIStatusError as exc:
            status_code = getattr(exc.response, "status_code", None)
            raise ServerError(
                str(exc),
                status_code=status_code,
            ) from exc

        for chunk in response_stream:
            choices = getattr(chunk, "choices", None) or []

            reasoning_summary = getattr(
                getattr(chunk, "reasoning_summary", None),
                "content",
                None,
            )
            reasoning_status = getattr(
                getattr(chunk, "reasoning_summary", None),
                "status",
                None,
            )

            if not choices:
                yield StreamEvent(
                    model=getattr(chunk, "model", None),
                    reasoning_summary=reasoning_summary,
                    reasoning_status=reasoning_status,
                    raw=chunk,
                )
                continue

            for choice in choices:
                delta = getattr(choice, "delta", None)
                tool_calls: list[ToolCall] = []

                for call in getattr(delta, "tool_calls", None) or []:
                    function = getattr(call, "function", None)

                    arguments = getattr(function, "arguments", None) or "{}"

                    tool_calls.append(
                        ToolCall(
                            id=getattr(call, "id", None) or "",
                            name=getattr(function, "name", None) or "",
                            arguments=arguments,
                        )
                    )

                yield StreamEvent(
                    content=getattr(delta, "content", None) or "",
                    role=getattr(delta, "role", None),
                    finish_reason=getattr(choice, "finish_reason", None),
                    model=getattr(chunk, "model", None),
                    reasoning_summary=reasoning_summary,
                    reasoning_status=reasoning_status,
                    tool_calls=tool_calls,
                    raw=chunk,
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
        """Generate a code edit using the dedicated Inception edit endpoint."""

        payload = [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in messages
        ]

        kwargs: dict[str, Any] = {
            "messages": payload,
            "model": model or self.settings.edit_model,
        }

        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        if temperature is not None:
            kwargs["temperature"] = temperature

        if top_p is not None:
            kwargs["top_p"] = top_p

        if presence_penalty is not None:
            kwargs["presence_penalty"] = presence_penalty

        try:
            response = self.client.edit.completions.create(**kwargs)
        except inceptionai.AuthenticationError as exc:
            raise AuthenticationError(str(exc)) from exc
        except inceptionai.RateLimitError as exc:
            retry_after = None
            response_obj = getattr(exc, "response", None)

            if response_obj is not None:
                retry_after_header = response_obj.headers.get("retry-after")
                if retry_after_header:
                    try:
                        retry_after = float(retry_after_header)
                    except ValueError:
                        pass

            raise RateLimitError(
                str(exc),
                retry_after=retry_after,
            ) from exc
        except inceptionai.APITimeoutError as exc:
            raise TimeoutError(str(exc)) from exc
        except inceptionai.APIConnectionError as exc:
            raise NetworkError(str(exc)) from exc
        except inceptionai.BadRequestError as exc:
            raise InvalidRequestError(str(exc)) from exc
        except inceptionai.NotFoundError as exc:
            raise ModelNotFoundError(str(exc)) from exc
        except inceptionai.InternalServerError as exc:
            raise ServerError(str(exc)) from exc
        except inceptionai.APIStatusError as exc:
            status_code = getattr(exc.response, "status_code", None)
            raise ServerError(
                str(exc),
                status_code=status_code,
            ) from exc

        return self._edit_result(response)

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
        """Generate a fill-in-the-middle completion."""

        kwargs: dict[str, Any] = {
            "model": model or self.settings.model,
            "prompt": prompt,
        }

        if suffix is not None:
            kwargs["suffix"] = suffix

        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        if top_p is not None:
            kwargs["top_p"] = top_p

        if top_k is not None:
            kwargs["top_k"] = top_k

        if temperature is not None:
            kwargs["temperature"] = temperature

        if frequency_penalty is not None:
            kwargs["frequency_penalty"] = frequency_penalty

        if presence_penalty is not None:
            kwargs["presence_penalty"] = presence_penalty

        if repetition_penalty is not None:
            kwargs["repetition_penalty"] = repetition_penalty

        if stop is not None:
            kwargs["stop"] = stop

        try:
            response = self.client.fim.completions.create(**kwargs)
        except inceptionai.AuthenticationError as exc:
            raise AuthenticationError(str(exc)) from exc
        except inceptionai.RateLimitError as exc:
            retry_after = None
            response_obj = getattr(exc, "response", None)

            if response_obj is not None:
                retry_after_header = response_obj.headers.get("retry-after")
                if retry_after_header:
                    try:
                        retry_after = float(retry_after_header)
                    except ValueError:
                        pass

            raise RateLimitError(
                str(exc),
                retry_after=retry_after,
            ) from exc
        except inceptionai.APITimeoutError as exc:
            raise TimeoutError(str(exc)) from exc
        except inceptionai.APIConnectionError as exc:
            raise NetworkError(str(exc)) from exc
        except inceptionai.BadRequestError as exc:
            raise InvalidRequestError(str(exc)) from exc
        except inceptionai.NotFoundError as exc:
            raise ModelNotFoundError(str(exc)) from exc
        except inceptionai.InternalServerError as exc:
            raise ServerError(str(exc)) from exc
        except inceptionai.APIStatusError as exc:
            status_code = getattr(exc.response, "status_code", None)
            raise ServerError(
                str(exc),
                status_code=status_code,
            ) from exc

        return self._fim_result(response)

    @staticmethod
    def _edit_result(response: Any) -> CompletionResult:
        choices = getattr(response, "choices", None) or []

        if not choices:
            return CompletionResult(
                model=getattr(response, "model", None),
                usage=_usage_dict(response),
                raw=response,
            )

        choice = choices[0]
        message = getattr(choice, "message", None)

        return CompletionResult(
            content=getattr(message, "content", None) or "",
            finish_reason=getattr(choice, "finish_reason", None),
            model=getattr(response, "model", None),
            usage=_usage_dict(response),
            raw=response,
        )

    @staticmethod
    def _fim_result(response: Any) -> CompletionResult:
        choices = getattr(response, "choices", None) or []

        if not choices:
            return CompletionResult(
                model=getattr(response, "model", None),
                usage=_usage_dict(response),
                raw=response,
            )

        choice = choices[0]

        return CompletionResult(
            content=getattr(choice, "text", None) or "",
            finish_reason=getattr(choice, "finish_reason", None),
            model=getattr(response, "model", None),
            usage=_usage_dict(response),
            raw=response,
        )

    def models(self) -> list[ModelInfo]:
        try:
            response = self.client.models.list()
        except inceptionai.AuthenticationError as exc:
            raise AuthenticationError(str(exc)) from exc
        except inceptionai.APIConnectionError as exc:
            raise NetworkError(str(exc)) from exc
        except inceptionai.APITimeoutError as exc:
            raise TimeoutError(str(exc)) from exc
        except inceptionai.APIStatusError as exc:
            status_code = getattr(exc.response, "status_code", None)
            raise ServerError(
                str(exc),
                status_code=status_code,
            ) from exc

        result: list[ModelInfo] = []

        for model in response.data:
            result.append(
                ModelInfo(
                    id=model.id,
                    owned_by=getattr(model, "owned_by", None),
                )
            )

        return result

    @staticmethod
    def _completion_result(response: Any) -> CompletionResult:
        choices = getattr(response, "choices", None) or []

        if not choices:
            return CompletionResult(
                model=getattr(response, "model", None),
                usage=_usage_dict(response),
                raw=response,
            )

        choice = choices[0]
        message = getattr(choice, "message", None)

        content = ""
        tool_calls: list[ToolCall] = []

        if message is not None:
            content = getattr(message, "content", None) or ""

            for call in getattr(message, "tool_calls", None) or []:
                arguments = getattr(call.function, "arguments", "{}")

                if isinstance(arguments, str):
                    try:
                        import json

                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        arguments = {}

                tool_calls.append(
                    ToolCall(
                        id=getattr(call, "id", ""),
                        name=getattr(call.function, "name", ""),
                        arguments=arguments,
                    )
                )

        return CompletionResult(
            content=content,
            tool_calls=tool_calls,
            finish_reason=getattr(choice, "finish_reason", None),
            model=getattr(response, "model", None),
            usage=_usage_dict(response),
            raw=response,
        )


def _usage_dict(response: Any) -> dict[str, Any]:
    usage = getattr(response, "usage", None)

    if usage is None:
        return {}

    if hasattr(usage, "model_dump"):
        return usage.model_dump()

    if hasattr(usage, "__dict__"):
        return dict(usage.__dict__)

    return {}
