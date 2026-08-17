from unittest.mock import MagicMock

from zeta_cli.agent.planner import Planner
from zeta_cli.api.models import CompletionResult, Message, ToolCall
from zeta_cli.config import Settings


def test_planner_sends_goal_to_model():
    api = MagicMock()
    api.complete.return_value = CompletionResult(
        content="I need to inspect the repository first.",
        model="mercury-2",
    )

    planner = Planner(
        api,
        Settings(api_key="test-key"),
    )

    result = planner.plan("Implement the authentication system")

    api.complete.assert_called_once()

    messages = api.complete.call_args.args[0]

    assert isinstance(messages, list)
    assert all(isinstance(message, Message) for message in messages)
    assert any(
        "Implement the authentication system" in message.content
        for message in messages
    )

    assert result.content == "I need to inspect the repository first."


def test_planner_uses_configured_model_and_reasoning_effort():
    api = MagicMock()
    api.complete.return_value = CompletionResult(
        content="plan",
        model="mercury-2",
    )

    settings = Settings(
        api_key="test-key",
        model="mercury-2",
        reasoning_effort="high",
    )

    planner = Planner(api, settings)

    planner.plan("Build the agent")

    kwargs = api.complete.call_args.kwargs

    assert kwargs["model"] == "mercury-2"
    assert kwargs["reasoning_effort"] == "high"


def test_planner_preserves_tool_calls():
    api = MagicMock()

    expected_call = ToolCall(
        id="call-1",
        name="read_file",
        arguments={"path": "README.md"},
    )

    api.complete.return_value = CompletionResult(
        tool_calls=[expected_call],
        model="mercury-2",
    )

    planner = Planner(
        api,
        Settings(api_key="test-key"),
    )

    result = planner.plan("Inspect the README")

    assert result.tool_calls == [expected_call]


def test_planner_accepts_tool_schemas():
    api = MagicMock()
    api.complete.return_value = CompletionResult(content="plan")

    planner = Planner(
        api,
        Settings(api_key="test-key"),
    )

    tools = [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read a file",
            },
        }
    ]

    planner.plan("Inspect the repository", tools=tools)

    assert api.complete.call_args.kwargs["tools"] == tools
