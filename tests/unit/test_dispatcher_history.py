from unittest.mock import MagicMock

from zeta_cli.api.models import ToolCall
from zeta_cli.tools.dispatcher import ToolDispatcher
from zeta_cli.tools.history import ToolHistory


def make_call(name: str = "read_file") -> ToolCall:
    return ToolCall(
        id="call-1",
        name=name,
        arguments={"path": "README.md"},
    )


def test_dispatcher_records_successful_tool_in_history():
    tool = MagicMock(return_value="contents")

    registry = MagicMock()
    registry.get.return_value = tool

    history = ToolHistory()
    dispatcher = ToolDispatcher(registry, history=history)

    result = dispatcher.dispatch(make_call())

    assert result.ok is True
    assert len(history.entries()) == 1
    assert history.entries()[0].result == result


def test_dispatcher_records_failed_tool_in_history():
    tool = MagicMock(side_effect=RuntimeError("read failed"))

    registry = MagicMock()
    registry.get.return_value = tool

    history = ToolHistory()
    dispatcher = ToolDispatcher(registry, history=history)

    result = dispatcher.dispatch(make_call())

    assert result.ok is False
    assert result.error == "read failed"
    assert len(history.entries()) == 1
    assert history.entries()[0].result == result


def test_dispatcher_without_history_preserves_existing_behavior():
    tool = MagicMock(return_value="contents")

    registry = MagicMock()
    registry.get.return_value = tool

    dispatcher = ToolDispatcher(registry)

    result = dispatcher.dispatch(make_call())

    assert result.ok is True
    assert result.value == "contents"
