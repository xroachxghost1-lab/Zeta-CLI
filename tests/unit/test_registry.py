from unittest.mock import MagicMock

import pytest

from zeta_cli.tools.registry import ToolRegistry


def test_registry_registers_and_gets_tool():
    registry = ToolRegistry()
    tool = MagicMock()

    registry.register("read_file", tool)

    assert registry.get("read_file") is tool


def test_registry_returns_none_for_unknown_tool():
    registry = ToolRegistry()

    assert registry.get("missing") is None


def test_registry_rejects_duplicate_tool_names():
    registry = ToolRegistry()

    registry.register("read_file", MagicMock())

    with pytest.raises(ValueError):
        registry.register("read_file", MagicMock())


def test_registry_lists_registered_tool_names():
    registry = ToolRegistry()

    registry.register("read_file", MagicMock())
    registry.register("write_file", MagicMock())

    assert registry.names() == ("read_file", "write_file")
