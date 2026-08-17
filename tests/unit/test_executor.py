from unittest.mock import MagicMock

import pytest

from zeta_cli.agent.executor import Executor
from zeta_cli.api.models import CompletionResult, ToolCall
from zeta_cli.tools.results import ToolResult


def make_call(name: str = "read_file") -> ToolCall:
    return ToolCall(
        id="call-1",
        name=name,
        arguments={"path": "README.md"},
    )


def test_executor_dispatches_planned_tool_call():
    dispatcher = MagicMock()
    dispatcher.dispatch.return_value = ToolResult.from_value(
        "README contents"
    )

    executor = Executor(dispatcher)
    call = make_call()

    result = executor.execute(
        CompletionResult(tool_calls=[call])
    )

    assert result.ok is True
    assert result.value == "README contents"
    dispatcher.dispatch.assert_called_once_with(call)


def test_executor_rejects_planning_result_without_tool_call():
    dispatcher = MagicMock()
    executor = Executor(dispatcher)

    with pytest.raises(ValueError, match="no tool call"):
        executor.execute(CompletionResult())

    dispatcher.dispatch.assert_not_called()


def test_executor_preserves_tool_failure():
    dispatcher = MagicMock()
    dispatcher.dispatch.return_value = ToolResult.from_exception(
        RuntimeError("read failed")
    )

    executor = Executor(dispatcher)

    result = executor.execute(
        CompletionResult(tool_calls=[make_call()])
    )

    assert result.ok is False
    assert result.error == "read failed"


def test_executor_uses_first_tool_call():
    dispatcher = MagicMock()
    dispatcher.dispatch.return_value = ToolResult.from_value("ok")

    executor = Executor(dispatcher)

    first = make_call("read_file")
    second = make_call("write_file")

    executor.execute(
        CompletionResult(tool_calls=[first, second])
    )

    dispatcher.dispatch.assert_called_once_with(first)
