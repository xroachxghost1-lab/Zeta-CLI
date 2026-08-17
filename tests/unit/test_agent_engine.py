from unittest.mock import MagicMock

import pytest

from zeta_cli.agent.engine import AgentEngine
from zeta_cli.api.models import CompletionResult
from zeta_cli.events import EventJournal
from zeta_cli.state import AgentState, StateStore


def test_engine_starts_task_and_enters_plan(tmp_path):
    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    planner = MagicMock()
    planner.plan.return_value = CompletionResult(
        content="Inspect the repository and identify the required changes.",
        model="mercury-2",
    )

    engine = AgentEngine(
        planner=planner,
        state_store=state_store,
        journal=journal,
    )

    result = engine.start(
        task_id="task-1",
        goal="Build the authentication system",
    )

    assert result.content == (
        "Inspect the repository and identify the required changes."
    )

    planner.plan.assert_called_once_with(
        "Build the authentication system",
    )

    state = state_store.load()

    assert state.task_id == "task-1"
    assert state.goal == "Build the authentication system"
    assert state.phase == "PLAN"
    assert state.completed is False
    assert state.failed is False

    events = journal.read()

    assert len(events) == 2
    assert events[0].event_type == "PHASE_CHANGED"
    assert events[1].event_type == "WATCHDOG_DECISION"
    assert events[0].task_id == "task-1"
    assert events[0].data == {
        "from": "BOOT",
        "to": "PLAN",
    }


def test_engine_can_resume_persisted_task(tmp_path):
    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    state_store.save(
        AgentState(
            task_id="task-2",
            goal="Continue the implementation",
            phase="PLAN",
        )
    )

    planner = MagicMock()
    planner.plan.return_value = CompletionResult(
        content="Continue with implementation.",
        model="mercury-2",
    )

    engine = AgentEngine(
        planner=planner,
        state_store=state_store,
        journal=journal,
    )

    result = engine.resume()

    assert result.content == "Continue with implementation."

    planner.plan.assert_called_once_with(
        "Continue the implementation",
    )


def test_engine_start_rejects_empty_task_id(tmp_path):
    planner = MagicMock()
    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    engine = AgentEngine(
        planner=planner,
        state_store=state_store,
        journal=journal,
    )

    with pytest.raises(ValueError, match="task_id"):
        engine.start(task_id="", goal="Build the agent")

    assert state_store.load().phase == "BOOT"
    planner.plan.assert_not_called()


def test_engine_start_rejects_empty_goal(tmp_path):
    planner = MagicMock()
    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    engine = AgentEngine(
        planner=planner,
        state_store=state_store,
        journal=journal,
    )

    with pytest.raises(ValueError, match="goal"):
        engine.start(task_id="task-1", goal="")

    assert state_store.load().phase == "BOOT"
    planner.plan.assert_not_called()


def test_engine_start_strips_task_id_and_goal(tmp_path):
    planner = MagicMock()
    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    engine = AgentEngine(
        planner=planner,
        state_store=state_store,
        journal=journal,
    )

    planner.plan.return_value = MagicMock()

    engine.start(
        task_id="  task-1  ",
        goal="  Build the agent  ",
    )

    state = state_store.load()

    assert state.task_id == "task-1"
    assert state.goal == "Build the agent"
    planner.plan.assert_called_once_with("Build the agent")


def test_engine_resume_preserves_persisted_progress(tmp_path):
    planner = MagicMock()
    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    state_store.save(
        AgentState(
            task_id="task-1",
            goal="Build the agent",
            phase="PLAN",
            progress=10,
        )
    )

    engine = AgentEngine(
        planner=planner,
        state_store=state_store,
        journal=journal,
    )

    planner.plan.return_value = MagicMock()

    engine.resume()

    state = state_store.load()

    assert state.phase == "PLAN"
    assert state.progress == 10
    assert state.task_id == "task-1"
    assert state.goal == "Build the agent"
    planner.plan.assert_called_once_with("Build the agent")


def test_engine_resume_preserves_mid_lifecycle_progress(tmp_path):
    planner = MagicMock()
    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    state_store.save(
        AgentState(
            task_id="task-1",
            goal="Build the agent",
            phase="VERIFY",
            progress=75,
        )
    )

    engine = AgentEngine(
        planner=planner,
        state_store=state_store,
        journal=journal,
    )

    planner.plan.return_value = MagicMock()

    engine.resume()

    state = state_store.load()

    assert state.phase == "VERIFY"
    assert state.progress == 75
    assert state.task_id == "task-1"
    assert state.goal == "Build the agent"
    planner.plan.assert_called_once_with("Build the agent")


def test_engine_passes_tool_schemas_to_planner(tmp_path):
    from unittest.mock import MagicMock

    from zeta_cli.agent.engine import AgentEngine
    from zeta_cli.api.models import CompletionResult
    from zeta_cli.events import EventJournal
    from zeta_cli.state import StateStore

    planner = MagicMock()
    planner.plan.return_value = CompletionResult(
        tool_calls=[],
    )

    schemas = [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read a file",
                "parameters": {
                    "type": "object",
                },
            },
        }
    ]

    engine = AgentEngine(
        planner=planner,
        state_store=StateStore(tmp_path / "state.json"),
        journal=EventJournal(tmp_path / "events.jsonl"),
        tool_schemas=schemas,
    )

    engine.start(
        task_id="task-1",
        goal="Inspect the repository",
    )

    planner.reset_mock()

    try:
        engine.execute()
    except ValueError:
        # The test is only interested in the planner invocation.
        pass

    assert planner.plan.call_args.kwargs["tools"] == schemas
