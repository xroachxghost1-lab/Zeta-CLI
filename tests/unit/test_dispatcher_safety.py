from unittest.mock import MagicMock

import pytest

from zeta_cli.api.models import ToolCall
from zeta_cli.errors import ToolError
from zeta_cli.tools.dispatcher import ToolDispatcher
from zeta_cli.tools.safety import ToolSafety


def test_dispatcher_allows_tool_approved_by_safety():
    tool = MagicMock(return_value="ok")

    registry = MagicMock()
    registry.get.return_value = tool

    safety = ToolSafety({"read_file"})
    dispatcher = ToolDispatcher(registry, safety)

    result = dispatcher.dispatch(
        ToolCall(
            id="call-1",
            name="read_file",
            arguments={"path": "README.md"},
        )
    )

    assert result.ok is True
    assert result.value == "ok"
    tool.assert_called_once_with({"path": "README.md"})


def test_dispatcher_rejects_unapproved_tool():
    tool = MagicMock(return_value="should not run")

    registry = MagicMock()
    registry.get.return_value = tool

    safety = ToolSafety({"read_file"})
    dispatcher = ToolDispatcher(registry, safety)

    with pytest.raises(ToolError):
        dispatcher.dispatch(
            ToolCall(
                id="call-1",
                name="shell",
                arguments={"command": "echo hello"},
            )
        )

    tool.assert_not_called()


def test_dispatcher_rejects_explicitly_denied_tool():
    tool = MagicMock(return_value="should not run")

    registry = MagicMock()
    registry.get.return_value = tool

    safety = ToolSafety(
        {"read_file", "shell"},
        denied={"shell"},
    )
    dispatcher = ToolDispatcher(registry, safety)

    with pytest.raises(ToolError):
        dispatcher.dispatch(
            ToolCall(
                id="call-1",
                name="shell",
                arguments={"command": "echo hello"},
            )
        )

    tool.assert_not_called()
