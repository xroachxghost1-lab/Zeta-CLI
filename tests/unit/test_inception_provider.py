from unittest.mock import MagicMock

import inceptionai

import pytest

from zeta_cli.api.inception import InceptionProvider
from zeta_cli.api.models import Message
from zeta_cli.config import Settings
from zeta_cli.errors import APIError
from zeta_cli.api.errors import (
    AuthenticationError,
    NetworkError,
    RateLimitError,
    TimeoutError,
)


def test_provider_requires_api_key(monkeypatch):
    monkeypatch.delenv("INCEPTION_API_KEY", raising=False)

    with pytest.raises(APIError):
        InceptionProvider(Settings(api_key=None))


def test_provider_creates_sdk_client():
    provider = InceptionProvider(Settings(api_key="test-key"))

    assert provider.settings.api_key == "test-key"
    assert provider.client is not None


def test_complete_maps_messages_and_options():
    provider = InceptionProvider(Settings(api_key="test-key"))

    response = MagicMock()
    response.model = "mercury-2"
    response.choices = []
    response.usage = None

    provider.client.chat.completions.create = MagicMock(
        return_value=response
    )

    result = provider.complete(
        [
            Message(role="system", content="You are Zeta."),
            Message(role="user", content="Hello"),
        ],
        model="mercury-2",
        reasoning_effort="high",
    )

    provider.client.chat.completions.create.assert_called_once()

    kwargs = provider.client.chat.completions.create.call_args.kwargs

    assert kwargs["model"] == "mercury-2"
    assert kwargs["reasoning_effort"] == "high"
    assert kwargs["messages"] == [
        {"role": "system", "content": "You are Zeta."},
        {"role": "user", "content": "Hello"},
    ]

    assert result.model == "mercury-2"


def test_models_maps_model_list():
    provider = InceptionProvider(Settings(api_key="test-key"))

    model = MagicMock()
    model.id = "mercury-2"
    model.owned_by = "inception"

    response = MagicMock()
    response.data = [model]

    provider.client.models.list = MagicMock(return_value=response)

    result = provider.models()

    assert len(result) == 1
    assert result[0].id == "mercury-2"
    assert result[0].owned_by == "inception"


def test_complete_maps_text_response_and_metadata():
    provider = InceptionProvider(Settings(api_key="test-key"))

    message = MagicMock()
    message.content = "Hello from Mercury."
    message.tool_calls = []

    choice = MagicMock()
    choice.message = message
    choice.finish_reason = "stop"

    response = MagicMock()
    response.model = "mercury-2"
    response.choices = [choice]
    response.usage = MagicMock()
    response.usage.model_dump.return_value = {
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15,
    }

    provider.client.chat.completions.create = MagicMock(
        return_value=response
    )

    result = provider.complete(
        [Message(role="user", content="Hello")]
    )

    assert result.content == "Hello from Mercury."
    assert result.tool_calls == []
    assert result.finish_reason == "stop"
    assert result.model == "mercury-2"
    assert result.usage == {
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15,
    }


def test_complete_maps_tool_calls():
    provider = InceptionProvider(Settings(api_key="test-key"))

    function = MagicMock()
    function.name = "shell"
    function.arguments = '{"command": "pwd"}'

    tool_call = MagicMock()
    tool_call.id = "call-123"
    tool_call.function = function

    message = MagicMock()
    message.content = ""
    message.tool_calls = [tool_call]

    choice = MagicMock()
    choice.message = message
    choice.finish_reason = "tool_calls"

    response = MagicMock()
    response.model = "mercury-2"
    response.choices = [choice]
    response.usage = None

    provider.client.chat.completions.create = MagicMock(
        return_value=response
    )

    result = provider.complete(
        [Message(role="user", content="run pwd")]
    )

    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].id == "call-123"
    assert result.tool_calls[0].name == "shell"
    assert result.tool_calls[0].arguments == {
        "command": "pwd"
    }
    assert result.finish_reason == "tool_calls"


def test_complete_forwards_tools():
    provider = InceptionProvider(Settings(api_key="test-key"))

    response = MagicMock()
    response.model = "mercury-2"
    response.choices = []
    response.usage = None

    provider.client.chat.completions.create = MagicMock(
        return_value=response
    )

    tools = [
        {
            "type": "function",
            "function": {
                "name": "shell",
                "description": "Run a shell command",
            },
        }
    ]

    provider.complete(
        [Message(role="user", content="hello")],
        tools=tools,
    )

    kwargs = provider.client.chat.completions.create.call_args.kwargs

    assert kwargs["tools"] == tools


def test_complete_handles_malformed_tool_arguments():
    provider = InceptionProvider(Settings(api_key="test-key"))

    function = MagicMock()
    function.name = "shell"
    function.arguments = "{not-valid-json"

    tool_call = MagicMock()
    tool_call.id = "call-bad"
    tool_call.function = function

    message = MagicMock()
    message.content = ""
    message.tool_calls = [tool_call]

    choice = MagicMock()
    choice.message = message
    choice.finish_reason = "tool_calls"

    response = MagicMock()
    response.model = "mercury-2"
    response.choices = [choice]
    response.usage = None

    provider.client.chat.completions.create = MagicMock(
        return_value=response
    )

    result = provider.complete(
        [Message(role="user", content="hello")]
    )

    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].arguments == {}


def test_complete_handles_empty_choices():
    provider = InceptionProvider(Settings(api_key="test-key"))

    response = MagicMock()
    response.model = "mercury-2"
    response.choices = []
    response.usage = None

    provider.client.chat.completions.create = MagicMock(
        return_value=response
    )

    result = provider.complete(
        [Message(role="user", content="hello")]
    )

    assert result.content == ""
    assert result.tool_calls == []
    assert result.finish_reason is None
    assert result.model == "mercury-2"
    assert result.usage == {}


def test_authentication_error_is_normalized():
    provider = InceptionProvider(Settings(api_key="test-key"))

    provider.client.chat.completions.create = MagicMock(
        side_effect=inceptionai.AuthenticationError(
            message="unauthorized",
            response=MagicMock(),
            body=None,
        )
    )

    with pytest.raises(AuthenticationError):
        provider.complete(
            [Message(role="user", content="hello")]
        )


def test_rate_limit_error_is_normalized():
    provider = InceptionProvider(Settings(api_key="test-key"))

    response = MagicMock()
    response.headers = {"retry-after": "3.5"}

    provider.client.chat.completions.create = MagicMock(
        side_effect=inceptionai.RateLimitError(
            "rate limited",
            response=response,
            body=None,
        )
    )

    with pytest.raises(RateLimitError) as exc_info:
        provider.complete(
            [Message(role="user", content="hello")]
        )

    assert exc_info.value.status_code == 429
    assert exc_info.value.retry_after == 3.5


def test_timeout_error_is_normalized():
    provider = InceptionProvider(Settings(api_key="test-key"))

    request = MagicMock()

    provider.client.chat.completions.create = MagicMock(
        side_effect=inceptionai.APITimeoutError(request=request)
    )

    with pytest.raises(TimeoutError):
        provider.complete(
            [Message(role="user", content="hello")]
        )


def test_connection_error_is_normalized():
    provider = InceptionProvider(Settings(api_key="test-key"))

    request = MagicMock()

    provider.client.chat.completions.create = MagicMock(
        side_effect=inceptionai.APIConnectionError(request=request)
    )

    with pytest.raises(NetworkError):
        provider.complete(
            [Message(role="user", content="hello")]
        )


def test_complete_normalizes_authentication_error():
    provider = InceptionProvider(Settings(api_key="test-key"))

    provider.client.chat.completions.create = MagicMock(
        side_effect=inceptionai.AuthenticationError(
            message="unauthorized",
            response=MagicMock(status_code=401),
            body=None,
        )
    )

    with pytest.raises(AuthenticationError):
        provider.complete(
            [Message(role="user", content="hello")]
        )


def test_complete_normalizes_rate_limit_error():
    provider = InceptionProvider(Settings(api_key="test-key"))

    response = MagicMock()
    response.headers = {"retry-after": "3.5"}

    provider.client.chat.completions.create = MagicMock(
        side_effect=inceptionai.RateLimitError(
            message="rate limited",
            response=response,
            body=None,
        )
    )

    with pytest.raises(RateLimitError) as exc_info:
        provider.complete(
            [Message(role="user", content="hello")]
        )

    assert exc_info.value.retry_after == 3.5
    assert exc_info.value.status_code == 429


def test_complete_normalizes_timeout_error():
    provider = InceptionProvider(Settings(api_key="test-key"))

    request = MagicMock()

    provider.client.chat.completions.create = MagicMock(
        side_effect=inceptionai.APITimeoutError(
            request=request,
        )
    )

    with pytest.raises(TimeoutError):
        provider.complete(
            [Message(role="user", content="hello")]
        )


def test_complete_normalizes_connection_error():
    provider = InceptionProvider(Settings(api_key="test-key"))

    request = MagicMock()

    provider.client.chat.completions.create = MagicMock(
        side_effect=inceptionai.APIConnectionError(
            message="connection failed",
            request=request,
        )
    )

    with pytest.raises(NetworkError):
        provider.complete(
            [Message(role="user", content="hello")]
        )


def test_edit_uses_dedicated_edit_endpoint():
    provider = InceptionProvider(Settings(api_key="test-key"))

    response = MagicMock()
    response.model = "mercury-edit-2"
    response.choices = []
    response.usage = None

    provider.client.edit.completions.create = MagicMock(
        return_value=response
    )

    messages = [
        Message(
            role="user",
            content="<|code_to_edit|>\nprint('hello')\n<|cursor|>",
        )
    ]

    result = provider.edit(
        messages,
        model="mercury-edit-2",
        max_tokens=200,
        temperature=0.2,
        top_p=0.9,
        presence_penalty=0.1,
    )

    provider.client.edit.completions.create.assert_called_once()

    kwargs = provider.client.edit.completions.create.call_args.kwargs

    assert kwargs["messages"] == [
        {
            "role": "user",
            "content": "<|code_to_edit|>\nprint('hello')\n<|cursor|>",
        }
    ]
    assert kwargs["model"] == "mercury-edit-2"
    assert kwargs["max_tokens"] == 200
    assert kwargs["temperature"] == 0.2
    assert kwargs["top_p"] == 0.9
    assert kwargs["presence_penalty"] == 0.1
    assert result.model == "mercury-edit-2"


def test_fim_uses_dedicated_fim_endpoint():
    provider = InceptionProvider(Settings(api_key="test-key"))

    response = MagicMock()
    response.model = "mercury-2"
    response.choices = []
    response.usage = None

    provider.client.fim.completions.create = MagicMock(
        return_value=response
    )

    result = provider.fim(
        model="mercury-2",
        prompt="def hello():\n    ",
        suffix="\nreturn hello",
        max_tokens=100,
        top_p=0.8,
    )

    provider.client.fim.completions.create.assert_called_once()

    kwargs = provider.client.fim.completions.create.call_args.kwargs

    assert kwargs["model"] == "mercury-2"
    assert kwargs["prompt"] == "def hello():\n    "
    assert kwargs["suffix"] == "\nreturn hello"
    assert kwargs["max_tokens"] == 100
    assert kwargs["top_p"] == 0.8
    assert result.model == "mercury-2"


def test_stream_yields_text_deltas_and_finish_reason():
    provider = InceptionProvider(Settings(api_key="test-key"))

    chunks = [
        MagicMock(
            id="chunk-1",
            model="mercury-2",
            choices=[
                MagicMock(
                    index=0,
                    finish_reason=None,
                    delta=MagicMock(
                        role="assistant",
                        content="Hello",
                        tool_calls=None,
                    ),
                )
            ],
            reasoning_summary=None,
        ),
        MagicMock(
            id="chunk-2",
            model="mercury-2",
            choices=[
                MagicMock(
                    index=0,
                    finish_reason=None,
                    delta=MagicMock(
                        role=None,
                        content=" world",
                        tool_calls=None,
                    ),
                )
            ],
            reasoning_summary=None,
        ),
        MagicMock(
            id="chunk-3",
            model="mercury-2",
            choices=[
                MagicMock(
                    index=0,
                    finish_reason="stop",
                    delta=MagicMock(
                        role=None,
                        content=None,
                        tool_calls=None,
                    ),
                )
            ],
            reasoning_summary=None,
        ),
    ]

    provider.client.chat.completions.create = MagicMock(
        return_value=iter(chunks)
    )

    events = list(
        provider.stream(
            [Message(role="user", content="hello")],
            model="mercury-2",
        )
    )

    assert [event.content for event in events] == [
        "Hello",
        " world",
        "",
    ]

    assert events[-1].finish_reason == "stop"
    assert all(event.model == "mercury-2" for event in events)

    provider.client.chat.completions.create.assert_called_once_with(
        messages=[
            {
                "role": "user",
                "content": "hello",
            }
        ],
        model="mercury-2",
        stream=True,
            diffusing=False,
    )


def test_stream_preserves_reasoning_summary():
    provider = InceptionProvider(Settings(api_key="test-key"))

    chunk = MagicMock(
        id="chunk-1",
        model="mercury-2",
        choices=[],
        reasoning_summary=MagicMock(
            content="Reasoning summary",
            status="complete",
        ),
    )

    provider.client.chat.completions.create = MagicMock(
        return_value=iter([chunk])
    )

    events = list(
        provider.stream(
            [Message(role="user", content="hello")],
            model="mercury-2",
        )
    )

    assert len(events) == 1
    assert events[0].reasoning_summary == "Reasoning summary"
    assert events[0].reasoning_status == "complete"


def test_stream_normalizes_api_errors():
    provider = InceptionProvider(Settings(api_key="test-key"))

    provider.client.chat.completions.create = MagicMock(
        side_effect=inceptionai.APIConnectionError(request=MagicMock())
    )

    with pytest.raises(NetworkError):
        list(
            provider.stream(
                [Message(role="user", content="hello")],
                model="mercury-2",
            )
        )


def test_stream_preserves_tool_call_deltas():
    provider = InceptionProvider(Settings(api_key="test-key"))

    chunks = [
        MagicMock(
            id="chunk-1",
            model="mercury-2",
            choices=[
                MagicMock(
                    index=0,
                    finish_reason=None,
                    delta=MagicMock(
                        role="assistant",
                        content=None,
                        tool_calls=[
                            MagicMock(
                                index=0,
                                id="call-1",
                                type="function",
                                function=MagicMock(
                                    arguments='{"path":',
                                ),
                            )
                        ],
                    ),
                )
            ],
            reasoning_summary=None,
        ),
        MagicMock(
            id="chunk-2",
            model="mercury-2",
            choices=[
                MagicMock(
                    index=0,
                    finish_reason=None,
                    delta=MagicMock(
                        role=None,
                        content=None,
                        tool_calls=[
                            MagicMock(
                                index=0,
                                id=None,
                                type=None,
                                function=MagicMock(
                                    arguments='"test.py"}',
                                ),
                            )
                        ],
                    ),
                )
            ],
            reasoning_summary=None,
        ),
    ]

    chunks[0].choices[0].delta.tool_calls[0].function.name = "read_file"
    chunks[1].choices[0].delta.tool_calls[0].function.name = None

    provider.client.chat.completions.create = MagicMock(
        return_value=iter(chunks)
    )

    events = list(
        provider.stream(
            [Message(role="user", content="read the file")],
            model="mercury-2",
        )
    )

    assert len(events) == 2

    assert events[0].tool_calls[0].id == "call-1"
    assert events[0].tool_calls[0].name == "read_file"
    assert events[0].tool_calls[0].arguments == '{"path":'

    assert events[1].tool_calls[0].arguments == '"test.py"}'


def test_stream_forwards_diffusing():
    provider = InceptionProvider(Settings(api_key="test-key"))

    provider.client.chat.completions.create = MagicMock(
        return_value=iter([])
    )

    list(
        provider.stream(
            [Message(role="user", content="hello")],
            model="mercury-2",
            diffusing=True,
        )
    )

    kwargs = provider.client.chat.completions.create.call_args.kwargs

    assert kwargs["model"] == "mercury-2"
    assert kwargs["stream"] is True
    assert kwargs["diffusing"] is True
