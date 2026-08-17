from unittest.mock import MagicMock

from zeta_cli.api.client import APIClient
from zeta_cli.api.models import CompletionResult, Message, ModelInfo
from zeta_cli.config import Settings


def test_client_stores_settings():
    settings = Settings(api_key="test-key")
    client = APIClient(settings)

    assert client.settings is settings
    assert client.provider is not None


def test_complete_delegates_to_provider():
    client = APIClient(Settings(api_key="test-key"))

    expected = CompletionResult(
        content="hello",
        model="mercury-2",
    )

    client.provider.complete = MagicMock(return_value=expected)

    messages = [Message(role="user", content="hello")]

    result = client.complete(
        messages,
        model="mercury-2",
        reasoning_effort="high",
    )

    client.provider.complete.assert_called_once_with(
        messages,
        model="mercury-2",
        reasoning_effort="high",
        tools=None,
    )

    assert result is expected


def test_edit_delegates_to_dedicated_provider():
    client = APIClient(Settings(api_key="test-key"))

    expected = CompletionResult(
        content="edited",
        model="mercury-edit-2",
    )

    client.provider.edit = MagicMock(return_value=expected)

    messages = [Message(role="user", content="edit this")]

    result = client.edit(
        messages,
        model="mercury-edit-2",
        max_tokens=200,
        temperature=0.2,
        top_p=0.9,
        presence_penalty=0.1,
    )

    client.provider.edit.assert_called_once_with(
        messages,
        model="mercury-edit-2",
        max_tokens=200,
        temperature=0.2,
        top_p=0.9,
        presence_penalty=0.1,
    )

    assert result is expected


def test_fim_delegates_to_dedicated_provider():
    client = APIClient(Settings(api_key="test-key"))

    expected = CompletionResult(
        content="completed",
        model="mercury-2",
    )

    client.provider.fim = MagicMock(return_value=expected)

    result = client.fim(
        model="mercury-2",
        prompt="def hello():\\n    ",
        suffix="\\nreturn hello",
        max_tokens=100,
        top_p=0.8,
        top_k=40,
        temperature=0.2,
        frequency_penalty=0.1,
        presence_penalty=0.2,
        repetition_penalty=1.1,
        stop=["\\n\\n"],
    )

    client.provider.fim.assert_called_once_with(
        model="mercury-2",
        prompt="def hello():\\n    ",
        suffix="\\nreturn hello",
        max_tokens=100,
        top_p=0.8,
        top_k=40,
        temperature=0.2,
        frequency_penalty=0.1,
        presence_penalty=0.2,
        repetition_penalty=1.1,
        stop=["\\n\\n"],
    )

    assert result is expected


def test_models_delegates_to_provider():
    client = APIClient(Settings(api_key="test-key"))

    expected = [
        ModelInfo(
            id="mercury-2",
            owned_by="inception",
        )
    ]

    client.provider.models = MagicMock(return_value=expected)

    result = client.models()

    client.provider.models.assert_called_once_with()

    assert result == expected


def test_stream_delegates_to_provider():
    client = APIClient(Settings(api_key="test-key"))

    expected = iter(["event-1", "event-2"])

    client.provider.stream = MagicMock(return_value=expected)

    messages = [Message(role="user", content="hello")]

    result = client.stream(
        messages,
        model="mercury-2",
        reasoning_effort="high",
        tools=[{"type": "function"}],
            diffusing=False,
    )

    client.provider.stream.assert_called_once_with(
        messages,
        model="mercury-2",
        reasoning_effort="high",
        tools=[{"type": "function"}],
            diffusing=False,
    )

    assert result is expected
