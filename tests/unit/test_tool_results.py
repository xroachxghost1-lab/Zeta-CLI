from zeta_cli.tools.registry import ToolRegistry
from zeta_cli.tools.dispatcher import ToolDispatcher
from zeta_cli.tools.results import ToolResult


def test_tool_result_normalizes_string():
    result = ToolResult.from_value("hello")

    assert result.ok is True
    assert result.value == "hello"
    assert result.error is None


def test_tool_result_normalizes_mapping():
    value = {"ok": True, "path": "README.md"}

    result = ToolResult.from_value(value)

    assert result.ok is True
    assert result.value == value
    assert result.error is None


def test_tool_result_normalizes_none():
    result = ToolResult.from_value(None)

    assert result.ok is True
    assert result.value is None
    assert result.error is None


def test_tool_result_normalizes_exception():
    result = ToolResult.from_exception(RuntimeError("boom"))

    assert result.ok is False
    assert result.value is None
    assert result.error == "boom"
