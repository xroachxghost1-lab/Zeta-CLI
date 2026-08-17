from unittest.mock import MagicMock

import pytest

from zeta_cli.agent.decision import Decision
from zeta_cli.agent.engine import AgentEngine
from zeta_cli.api.models import CompletionResult
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
            phase="ASSESS",
        )
    )

    return AgentEngine(
        planner=planner,
        executor=executor,
        state_store=state_store,
        journal=journal,
    ), state_store, journal


def test_engine_verify_successful_assessment(tmp_path):
    planner = MagicMock()
    planner.plan.return_value = CompletionResult(
        content="Verification passed.",
    )

    executor = MagicMock()

    engine, state_store, journal = make_engine(
        tmp_path,
        planner,
        executor,
    )

    result = engine.verify(
        ToolResult.from_value("Verification evidence")
    )

    assert result.phase == "COMPLETE"
    assert result.completed is True
    assert result.failed is False

    planner.plan.assert_not_called()

    state = state_store.load()
    assert state.phase == "COMPLETE"

    events = journal.read()
    assert [event.data for event in events] == [
        {"from": "ASSESS", "to": "VERIFY"},
        {"from": "VERIFY", "to": "COMPLETE"},
    ]


def test_engine_verify_requires_assess_phase(tmp_path):
    planner = MagicMock()
    executor = MagicMock()

    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    state_store.save(
        AgentState(
            task_id="task-1",
            goal="Read README.md",
            phase="EXECUTE",
        )
    )

    engine = AgentEngine(
        planner=planner,
        executor=executor,
        state_store=state_store,
        journal=journal,
    )

    with pytest.raises(ValueError, match="cannot verify"):
        engine.verify(
            ToolResult.from_value("Verification evidence")
        )

    planner.plan.assert_not_called()


def test_engine_verify_requires_task_goal(tmp_path):
    planner = MagicMock()
    executor = MagicMock()

    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    state_store.save(
        AgentState(
            task_id="task-1",
            goal=None,
            phase="ASSESS",
        )
    )

    engine = AgentEngine(
        planner=planner,
        executor=executor,
        state_store=state_store,
        journal=journal,
    )

    with pytest.raises(ValueError, match="goal"):
        engine.verify(
            ToolResult.from_value("Verification evidence")
        )

    planner.plan.assert_not_called()


def test_engine_verify_uses_decision_engine(tmp_path):
    planner = MagicMock()
    executor = MagicMock()
    decision_engine = MagicMock()

    decision_engine.decide.return_value = Decision.COMPLETE

    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    state_store.save(
        AgentState(
            task_id="task-1",
            goal="Read README.md",
            phase="ASSESS",
        )
    )

    engine = AgentEngine(
        planner=planner,
        executor=executor,
        state_store=state_store,
        journal=journal,
        decision_engine=decision_engine,
    )

    result = ToolResult.from_value("README contents")

    verified = engine.verify(result)

    decision_engine.decide.assert_called_once()
    assert verified.phase == "COMPLETE"
    assert verified.completed is True
    assert verified.failed is False


def test_engine_verify_sets_goal_progress_to_100(tmp_path):
    planner = MagicMock()
    executor = MagicMock()

    engine, state_store, journal = make_engine(
        tmp_path,
        planner,
        executor,
    )

    result = engine.verify(
        ToolResult.from_value("Verification evidence")
    )

    assert result.phase == "COMPLETE"
    assert result.completed is True

    state = state_store.load()
    assert state.phase == "COMPLETE"
    assert state.progress == 100
