from __future__ import annotations

from unittest.mock import MagicMock

from zeta_cli.api.models import ToolCall
from zeta_cli.api.retry import RetryPolicy
from zeta_cli.tools.dispatcher import ToolDispatcher
from zeta_cli.tools.registry import ToolRegistry


def make_call(name: str = "read_file") -> ToolCall:
    return ToolCall(
        id="call-1",
        name=name,
        arguments={"path": "README.md"},
    )


def test_dispatcher_does_not_retry_successful_tool():
    tool = MagicMock(return_value="contents")

    registry = MagicMock()
    registry.get.return_value = tool

    dispatcher = ToolDispatcher(
        registry,
        retry_policy=RetryPolicy(max_attempts=3),
    )

    result = dispatcher.dispatch(make_call())

    assert result.ok is True
    assert result.value == "contents"
    assert tool.call_count == 1


def test_dispatcher_retries_failed_tool_until_success():
    tool = MagicMock(
        side_effect=[
            RuntimeError("temporary failure"),
            RuntimeError("temporary failure"),
            "contents",
        ]
    )

    registry = MagicMock()
    registry.get.return_value = tool

    dispatcher = ToolDispatcher(
        registry,
        retry_policy=RetryPolicy(
            max_attempts=3,
            base_delay=0,
            jitter=0,
        ),
    )

    result = dispatcher.dispatch(make_call())

    assert result.ok is True
    assert result.value == "contents"
    assert tool.call_count == 3


def test_dispatcher_stops_after_retry_limit():
    tool = MagicMock(
        side_effect=RuntimeError("persistent failure")
    )

    registry = MagicMock()
    registry.get.return_value = tool

    dispatcher = ToolDispatcher(
        registry,
        retry_policy=RetryPolicy(
            max_attempts=3,
            base_delay=0,
            jitter=0,
        ),
    )

    result = dispatcher.dispatch(make_call())

    assert result.ok is False
    assert result.error == "persistent failure"
    assert tool.call_count == 3


def test_dispatcher_applies_retry_backoff():
    tool = MagicMock(
        side_effect=[
            RuntimeError("temporary failure"),
            "contents",
        ]
    )

    registry = MagicMock()
    registry.get.return_value = tool

    sleep = MagicMock()

    dispatcher = ToolDispatcher(
        registry,
        retry_policy=RetryPolicy(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            jitter=0,
        ),
        sleep=sleep,
    )

    result = dispatcher.dispatch(make_call())

    assert result.ok is True
    assert result.value == "contents"
    sleep.assert_called_once_with(1.0)
