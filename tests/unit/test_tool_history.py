from zeta_cli.api.models import ToolCall
from zeta_cli.tools.history import ToolHistory
from zeta_cli.tools.results import ToolResult


def make_call(
    name: str = "read_file",
    arguments: dict | None = None,
) -> ToolCall:
    return ToolCall(
        id="call-1",
        name=name,
        arguments=arguments or {"path": "README.md"},
    )


def test_tool_history_starts_empty():
    history = ToolHistory()

    assert history.entries() == []


def test_tool_history_records_tool_call_and_result():
    history = ToolHistory()
    call = make_call()
    result = ToolResult.from_value("contents")

    history.record(call, result)

    entries = history.entries()

    assert len(entries) == 1
    assert entries[0].call == call
    assert entries[0].result == result


def test_tool_history_preserves_record_order():
    history = ToolHistory()

    first = make_call("read_file", {"path": "README.md"})
    second = make_call("read_file", {"path": "ROADMAP.md"})

    history.record(first, ToolResult.from_value("read"))
    history.record(second, ToolResult.from_value("roadmap"))

    entries = history.entries()

    assert [entry.call for entry in entries] == [first, second]


def test_tool_history_records_fingerprint():
    history = ToolHistory()
    call = make_call()

    history.record(
        call,
        ToolResult.from_value("contents"),
    )

    entry = history.entries()[0]

    assert len(entry.fingerprint) == 64
    int(entry.fingerprint, 16)


def test_tool_history_returns_a_snapshot():
    history = ToolHistory()
    call = make_call()

    history.record(call, ToolResult.from_value("contents"))

    entries = history.entries()
    entries.clear()

    assert len(history.entries()) == 1
