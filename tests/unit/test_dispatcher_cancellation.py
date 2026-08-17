from __future__ import annotations

from threading import Event
from unittest.mock import MagicMock

from zeta_cli.api.models import ToolCall
from zeta_cli.tools.dispatcher import ToolDispatcher
from zeta_cli.tools.registry import ToolRegistry


def make_call(name: str = "read_file") -> ToolCall:
    return ToolCall(
        id="call-1",
        name=name,
        arguments={"path": "README.md"},
    )


def test_dispatcher_executes_when_not_cancelled():
    tool = MagicMock(return_value="contents")

    registry = MagicMock()
    registry.get.return_value = tool

    dispatcher = ToolDispatcher(registry)
    cancellation = Event()

    result = dispatcher.dispatch(
        make_call(),
        cancellation=cancellation,
    )

    assert result.ok is True
    assert result.value == "contents"
    tool.assert_called_once_with({"path": "README.md"})


def test_dispatcher_does_not_execute_cancelled_tool():
    tool = MagicMock(return_value="contents")

    registry = MagicMock()
    registry.get.return_value = tool

    dispatcher = ToolDispatcher(registry)

    cancellation = Event()
    cancellation.set()

    result = dispatcher.dispatch(
        make_call(),
        cancellation=cancellation,
    )

    assert result.ok is False
    assert result.value is None
    assert result.error is not None
    assert "cancel" in result.error.lower()
    tool.assert_not_called()


def test_dispatcher_without_cancellation_preserves_existing_behavior():
    registry = MagicMock()
    registry.get.return_value = lambda arguments: "contents"

    dispatcher = ToolDispatcher(registry)

    result = dispatcher.dispatch(make_call())

    assert result.ok is True
    assert result.value == "contents"
