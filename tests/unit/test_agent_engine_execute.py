from unittest.mock import MagicMock

import pytest

from zeta_cli.agent.engine import AgentEngine
from zeta_cli.api.models import CompletionResult, ToolCall
from zeta_cli.errors import ToolError
from zeta_cli.events import EventJournal
from zeta_cli.state import AgentState, StateStore
from zeta_cli.tools.results import ToolResult
from zeta_cli.watchdog.actions import WatchdogAction


def make_engine(tmp_path, planner, executor):
    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    state_store.save(
        AgentState(
            task_id="task-1",
            goal="Read README.md",
            phase="PLAN",
        )
    )

    return AgentEngine(
        planner=planner,
        executor=executor,
        state_store=state_store,
        journal=journal,
    ), state_store, journal


def test_engine_executes_planner_tool_call(tmp_path):
    tool_call = ToolCall(
        id="call-1",
        name="read_file",
        arguments={"path": "README.md"},
    )

    planner = MagicMock()
    planner.plan.return_value = CompletionResult(
        content="",
        tool_calls=[tool_call],
    )

    executor = MagicMock()
    executor.execute.return_value = ToolResult.from_value("README contents")

    engine, state_store, journal = make_engine(
        tmp_path,
        planner,
        executor,
    )

    result = engine.execute()

    assert result.ok is True
    assert result.value == "README contents"

    executor.execute.assert_called_once_with(planner.plan.return_value)

    state = state_store.load()
    assert state.phase == "EXECUTE"

    events = [
        event
        for event in journal.read()
        if event.event_type == "PHASE_CHANGED"
    ]
    assert len(events) == 1
    assert events[0].event_type == "PHASE_CHANGED"
    assert events[0].data == {
        "from": "PLAN",
        "to": "EXECUTE",
    }


def test_engine_returns_tool_failure_without_executing_next_step(tmp_path):
    tool_call = ToolCall(
        id="call-1",
        name="read_file",
        arguments={"path": "README.md"},
    )

    planner = MagicMock()
    planner.plan.return_value = CompletionResult(
        content="",
        tool_calls=[tool_call],
    )

    executor = MagicMock()
    executor.execute.return_value = ToolResult.from_exception(
        RuntimeError("read failed")
    )

    engine, state_store, journal = make_engine(
        tmp_path,
        planner,
        executor,
    )

    result = engine.execute()

    assert result.ok is False
    assert result.value is None
    assert result.error == "read failed"

    state = state_store.load()
    assert state.phase == "EXECUTE"

    executor.execute.assert_called_once_with(planner.plan.return_value)


def test_engine_propagates_safety_rejection(tmp_path):
    tool_call = ToolCall(
        id="call-1",
        name="shell",
        arguments={"command": "echo hello"},
    )

    planner = MagicMock()
    planner.plan.return_value = CompletionResult(
        content="",
        tool_calls=[tool_call],
    )

    executor = MagicMock()
    executor.execute.side_effect = ToolError(
        "tool is not allowed: 'shell'"
    )

    engine, state_store, journal = make_engine(
        tmp_path,
        planner,
        executor,
    )

    with pytest.raises(ToolError):
        engine.execute()

    state = state_store.load()
    assert state.phase == "EXECUTE"

    executor.execute.assert_called_once_with(planner.plan.return_value)


def test_engine_rejects_execute_without_planned_tool(tmp_path):
    planner = MagicMock()
    planner.plan.return_value = CompletionResult(
        content="No tool needed.",
        tool_calls=[],
    )

    executor = MagicMock()

    engine, state_store, journal = make_engine(
        tmp_path,
        planner,
        executor,
    )

    with pytest.raises(ValueError, match="no tool call"):
        engine.execute()

    state = state_store.load()
    assert state.phase == "PLAN"

    executor.execute.assert_not_called()


def test_engine_execute_updates_goal_progress(tmp_path):
    planner = MagicMock()
    executor = MagicMock()
    executor.execute.return_value = ToolResult.from_value("README contents")

    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    state_store.save(
        AgentState(
            task_id="task-1",
            goal="Read README.md",
            phase="PLAN",
            progress=10,
        )
    )

    planner.plan.return_value = CompletionResult(
        content="read README",
        tool_calls=[
            ToolCall(
                id="call-1",
                name="read_file",
                arguments={"path": "README.md"},
            )
        ],
    )

    engine = AgentEngine(
        planner=planner,
        executor=executor,
        state_store=state_store,
        journal=journal,
    )

    result = engine.execute()

    assert result.ok is True

    state = state_store.load()
    assert state.phase == "EXECUTE"
    assert state.progress == 30


def test_engine_execute_failure_preserves_goal_progress(tmp_path):
    tool_call = ToolCall(
        id="call-1",
        name="read_file",
        arguments={"path": "README.md"},
    )

    planner = MagicMock()
    planner.plan.return_value = CompletionResult(
        content="",
        tool_calls=[tool_call],
    )

    executor = MagicMock()
    executor.execute.return_value = ToolResult.from_exception(
        RuntimeError("read failed")
    )

    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    state_store.save(
        AgentState(
            task_id="task-1",
            goal="Read README.md",
            phase="PLAN",
            progress=10,
        )
    )

    engine = AgentEngine(
        planner=planner,
        executor=executor,
        state_store=state_store,
        journal=journal,
    )

    result = engine.execute()

    assert result.ok is False

    state = state_store.load()
    assert state.phase == "EXECUTE"
    assert state.progress == 30


def test_engine_replans_once_when_watchdog_requests_replan(tmp_path):
    first_call = ToolCall(
        id="call-1",
        name="read_file",
        arguments={"path": "README.md"},
    )
    replanned_call = ToolCall(
        id="call-2",
        name="read_file",
        arguments={"path": "pyproject.toml"},
    )

    planner = MagicMock()
    replanned_result = CompletionResult(tool_calls=[replanned_call])
    planner.plan.side_effect = [
        CompletionResult(tool_calls=[first_call]),
        replanned_result,
    ]

    executor = MagicMock()
    executor.execute.return_value = ToolResult.from_value("contents")

    engine, state_store, journal = make_engine(
        tmp_path,
        planner,
        executor,
    )

    watchdog = MagicMock()
    observation = MagicMock()
    watchdog.observe.return_value = (
        observation,
        WatchdogAction.REPLAN,
    )
    engine.watchdog = watchdog

    result = engine.execute()

    assert result.ok is True
    assert planner.plan.call_count == 2
    executor.execute.assert_called_once_with(replanned_result)
    assert state_store.load().phase == "EXECUTE"


def test_engine_replan_rejects_empty_planning_result(tmp_path):
    first_call = ToolCall(
        id="call-1",
        name="read_file",
        arguments={"path": "README.md"},
    )

    planner = MagicMock()
    planner.plan.side_effect = [
        CompletionResult(tool_calls=[first_call]),
        CompletionResult(tool_calls=[]),
    ]

    executor = MagicMock()

    engine, state_store, journal = make_engine(
        tmp_path,
        planner,
        executor,
    )

    watchdog = MagicMock()
    watchdog.observe.return_value = (
        MagicMock(),
        WatchdogAction.REPLAN,
    )
    engine.watchdog = watchdog

    with pytest.raises(ValueError, match="no tool call in replanned result"):
        engine.execute()

    executor.execute.assert_not_called()
    assert planner.plan.call_count == 2
    assert state_store.load().phase == "EXECUTE"


def test_engine_recovers_when_watchdog_requests_recovery(tmp_path):
    tool_call = ToolCall(
        id="call-1",
        name="read_file",
        arguments={"path": "README.md"},
    )

    planner = MagicMock()
    planner.plan.return_value = CompletionResult(tool_calls=[tool_call])

    executor = MagicMock()
    executor.execute.return_value = ToolResult.from_value("contents")

    engine, state_store, journal = make_engine(
        tmp_path,
        planner,
        executor,
    )

    watchdog = MagicMock()
    watchdog.observe.return_value = (
        MagicMock(),
        WatchdogAction.RECOVER,
    )
    engine.watchdog = watchdog

    result = engine.execute()

    assert result is None
    executor.execute.assert_not_called()
    assert state_store.load().phase == "RECOVER"

    events = [
        event
        for event in journal.read()
        if event.event_type == "PHASE_CHANGED"
    ]
    assert events[-1].data == {
        "from": "EXECUTE",
        "to": "RECOVER",
    }


def test_engine_stops_when_watchdog_requests_stop(tmp_path):
    tool_call = ToolCall(
        id="call-1",
        name="read_file",
        arguments={"path": "README.md"},
    )

    planner = MagicMock()
    planner.plan.return_value = CompletionResult(tool_calls=[tool_call])

    executor = MagicMock()

    engine, state_store, journal = make_engine(
        tmp_path,
        planner,
        executor,
    )

    watchdog = MagicMock()
    watchdog.observe.return_value = (
        MagicMock(),
        WatchdogAction.STOP,
    )
    engine.watchdog = watchdog

    result = engine.execute()

    assert result is None
    executor.execute.assert_not_called()
    assert state_store.load().phase == "STOPPED"

    events = [
        event
        for event in journal.read()
        if event.event_type == "PHASE_CHANGED"
    ]
    assert events[-1].data == {
        "from": "EXECUTE",
        "to": "STOPPED",
    }


def test_engine_stalled_watchdog_exhausts_budget_and_stops(tmp_path):
    tool_call = ToolCall(
        id="call-1",
        name="read_file",
        arguments={"path": "README.md"},
    )

    planner = MagicMock()
    planner.plan.return_value = CompletionResult(tool_calls=[tool_call])

    executor = MagicMock()
    executor.execute.return_value = ToolResult.from_value("contents")

    engine, state_store, journal = make_engine(
        tmp_path,
        planner,
        executor,
    )

    watchdog = MagicMock()
    watchdog.observe.side_effect = [
        (MagicMock(), WatchdogAction.RECOVER),
        (MagicMock(), WatchdogAction.STOP),
    ]
    engine.watchdog = watchdog

    first = engine.execute()
    assert first is None
    assert state_store.load().phase == "RECOVER"
    executor.execute.assert_not_called()

    # Put the task back into PLAN for the second watchdog decision.
    state = state_store.load()
    state.phase = "PLAN"
    state_store.save(state)

    second = engine.execute()
    assert second is None
    assert state_store.load().phase == "STOPPED"
    executor.execute.assert_not_called()

    watchdog.observe.assert_called()


def test_engine_stop_persists_stopped_state(tmp_path):
    from zeta_cli.watchdog.actions import WatchdogAction

    planner = MagicMock()
    planner.plan.return_value = CompletionResult(
        tool_calls=[
            ToolCall(
                id="call-1",
                name="read_file",
                arguments={"path": "README.md"},
            )
        ]
    )
    executor = MagicMock()

    engine, state_store, journal = make_engine(
        tmp_path,
        planner,
        executor,
    )

    watchdog = MagicMock()
    watchdog.observe.return_value = (
        MagicMock(),
        WatchdogAction.STOP,
    )
    engine.watchdog = watchdog

    result = engine.execute()

    assert result is None
    assert state_store.load().phase == "STOPPED"
    assert state_store.load().completed is False
    assert state_store.load().failed is False
    executor.execute.assert_not_called()

    phase_events = [
        event
        for event in journal.read()
        if event.event_type == "PHASE_CHANGED"
    ]

    assert [event.data for event in phase_events] == [
        {"from": "PLAN", "to": "EXECUTE"},
        {"from": "EXECUTE", "to": "STOPPED"},
    ]

    with pytest.raises(ValueError, match="cannot execute from phase"):
        engine.execute()
