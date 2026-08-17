from unittest.mock import MagicMock

from zeta_cli.agent.engine import AgentEngine
from zeta_cli.api.models import CompletionResult, ToolCall
from zeta_cli.events import EventJournal
from zeta_cli.state import AgentState, StateStore
from zeta_cli.tools.results import ToolResult


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


def test_engine_executes_through_executor(tmp_path):
    tool_call = ToolCall(
        id="call-1",
        name="read_file",
        arguments={"path": "README.md"},
    )

    planner = MagicMock()
    planner.plan.return_value = CompletionResult(
        tool_calls=[tool_call],
    )

    executor = MagicMock()
    executor.execute.return_value = ToolResult.from_value(
        "README contents"
    )

    engine, state_store, journal = make_engine(
        tmp_path,
        planner,
        executor,
    )

    result = engine.execute()

    assert result.ok is True
    assert result.value == "README contents"

    executor.execute.assert_called_once_with(
        planner.plan.return_value
    )

    state = state_store.load()
    assert state.phase == "EXECUTE"

    events = journal.read()
    assert len(events) == 1
    assert events[0].event_type == "PHASE_CHANGED"


def test_engine_requires_executor_for_execution(tmp_path):
    planner = MagicMock()

    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    state_store.save(
        AgentState(
            task_id="task-1",
            goal="Read README.md",
            phase="PLAN",
        )
    )

    engine = AgentEngine(
        planner=planner,
        state_store=state_store,
        journal=journal,
    )

    try:
        engine.execute()
    except ValueError as error:
        assert "executor" in str(error)
    else:
        raise AssertionError("expected executor requirement")
