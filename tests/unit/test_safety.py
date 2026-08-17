import pytest

from zeta_cli.tools.safety import ToolSafety


def test_safety_allows_explicitly_allowed_tool():
    safety = ToolSafety({"read_file"})

    assert safety.is_allowed("read_file") is True


def test_safety_denies_unapproved_tool():
    safety = ToolSafety({"read_file"})

    assert safety.is_allowed("shell") is False


def test_safety_rejects_denied_tool():
    safety = ToolSafety({"read_file"}, denied={"read_file"})

    assert safety.is_allowed("read_file") is False


def test_safety_rejects_unknown_tool():
    safety = ToolSafety()

    with pytest.raises(ValueError):
        safety.require_allowed("read_file")
