from unittest.mock import MagicMock

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

    assert len(events) == 1
    assert events[0].event_type == "PHASE_CHANGED"
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
