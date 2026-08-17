from unittest.mock import MagicMock

import pytest

from zeta_cli.api.models import ToolCall
from zeta_cli.tools.dispatcher import ToolDispatcher


def test_dispatcher_executes_registered_tool():
    registry = MagicMock()
    registry.get.return_value = lambda arguments: {
        "ok": True,
        "value": arguments["path"],
    }

    dispatcher = ToolDispatcher(registry)

    call = ToolCall(
        id="call-1",
        name="read_file",
        arguments={"path": "README.md"},
    )

    result = dispatcher.dispatch(call)

    registry.get.assert_called_once_with("read_file")
    assert result.ok is True
    assert result.value == {
        "ok": True,
        "value": "README.md",
    }
    assert result.error is None


def test_dispatcher_rejects_unknown_tool():
    registry = MagicMock()
    registry.get.return_value = None

    dispatcher = ToolDispatcher(registry)

    call = ToolCall(
        id="call-1",
        name="missing",
    )

    with pytest.raises(Exception):
        dispatcher.dispatch(call)


def test_dispatcher_passes_arguments_unchanged():
    tool = MagicMock(return_value={"ok": True})

    registry = MagicMock()
    registry.get.return_value = tool

    dispatcher = ToolDispatcher(registry)

    arguments = {
        "path": "src/example.py",
        "start": 10,
        "end": 20,
    }

    dispatcher.dispatch(
        ToolCall(
            id="call-1",
            name="read_file",
            arguments=arguments,
        )
    )

    tool.assert_called_once_with(arguments)


def test_dispatcher_normalizes_successful_result():
    tool = MagicMock(return_value={"ok": True, "value": "README.md"})

    registry = MagicMock()
    registry.get.return_value = tool

    dispatcher = ToolDispatcher(registry)

    result = dispatcher.dispatch(
        ToolCall(
            id="call-1",
            name="read_file",
            arguments={"path": "README.md"},
        )
    )

    assert result.ok is True
    assert result.value == {"ok": True, "value": "README.md"}
    assert result.error is None


def test_dispatcher_normalizes_tool_exception():
    tool = MagicMock(side_effect=RuntimeError("read failed"))

    registry = MagicMock()
    registry.get.return_value = tool

    dispatcher = ToolDispatcher(registry)

    result = dispatcher.dispatch(
        ToolCall(
            id="call-1",
            name="read_file",
            arguments={"path": "README.md"},
        )
    )

    assert result.ok is False
    assert result.value is None
    assert result.error == "read failed"
