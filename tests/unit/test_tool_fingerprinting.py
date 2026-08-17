from zeta_cli.tools.fingerprinting import tool_fingerprint


def test_tool_fingerprint_is_stable_for_same_call():
    first = tool_fingerprint(
        "read_file",
        {"path": "README.md"},
    )
    second = tool_fingerprint(
        "read_file",
        {"path": "README.md"},
    )

    assert first == second


def test_tool_fingerprint_changes_when_tool_name_changes():
    first = tool_fingerprint(
        "read_file",
        {"path": "README.md"},
    )
    second = tool_fingerprint(
        "write_file",
        {"path": "README.md"},
    )

    assert first != second


def test_tool_fingerprint_changes_when_arguments_change():
    first = tool_fingerprint(
        "read_file",
        {"path": "README.md"},
    )
    second = tool_fingerprint(
        "read_file",
        {"path": "ROADMAP.md"},
    )

    assert first != second


def test_tool_fingerprint_is_independent_of_mapping_order():
    first = tool_fingerprint(
        "read_file",
        {
            "path": "README.md",
            "encoding": "utf-8",
        },
    )
    second = tool_fingerprint(
        "read_file",
        {
            "encoding": "utf-8",
            "path": "README.md",
        },
    )

    assert first == second


def test_tool_fingerprint_returns_hex_digest():
    fingerprint = tool_fingerprint(
        "read_file",
        {"path": "README.md"},
    )

    assert len(fingerprint) == 64
    int(fingerprint, 16)

from zeta_cli.tools.fingerprinting import tool_result_fingerprint
from zeta_cli.tools.results import ToolResult


def test_tool_result_fingerprint_is_stable_for_same_result():
    first = tool_result_fingerprint(ToolResult.from_value("hello"))
    second = tool_result_fingerprint(ToolResult.from_value("hello"))

    assert first == second


def test_tool_result_fingerprint_changes_when_value_changes():
    first = tool_result_fingerprint(ToolResult.from_value("hello"))
    second = tool_result_fingerprint(ToolResult.from_value("goodbye"))

    assert first != second


def test_tool_result_fingerprint_changes_between_success_and_failure():
    first = tool_result_fingerprint(ToolResult.from_value("hello"))
    second = tool_result_fingerprint(
        ToolResult.from_exception(RuntimeError("boom"))
    )

    assert first != second


def test_reasoning_fingerprint_is_stable_for_whitespace():
    from zeta_cli.tools.fingerprinting import reasoning_fingerprint

    assert reasoning_fingerprint("hello   world") == reasoning_fingerprint(
        " hello world "
    )


def test_reasoning_fingerprint_changes_when_reasoning_changes():
    from zeta_cli.tools.fingerprinting import reasoning_fingerprint

    assert reasoning_fingerprint("step one") != reasoning_fingerprint(
        "step two"
    )
