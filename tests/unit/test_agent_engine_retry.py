from unittest.mock import MagicMock

import pytest

from zeta_cli.agent.engine import AgentEngine
from zeta_cli.events import EventJournal
from zeta_cli.state import AgentState, StateStore


def make_engine(tmp_path, phase="RECOVER", attempt=0):
    planner = MagicMock()
    executor = MagicMock()

    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    state_store.save(
        AgentState(
            task_id="task-1",
            goal="Read README.md",
            phase=phase,
            attempt=attempt,
            completed=False,
            failed=True,
        )
    )

    engine = AgentEngine(
        planner=planner,
        executor=executor,
        state_store=state_store,
        journal=journal,
    )

    return engine, state_store, journal, planner


def test_engine_retry_returns_to_plan(tmp_path):
    engine, state_store, journal, planner = make_engine(
        tmp_path,
        attempt=2,
    )

    result = engine.retry()

    assert result.phase == "PLAN"
    assert result.attempt == 3
    assert result.failed is False
    assert result.completed is False

    persisted = state_store.load()
    assert persisted.phase == "PLAN"
    assert persisted.attempt == 3
    assert persisted.failed is False
    assert persisted.completed is False

    planner.plan.assert_not_called()

    events = [
        event for event in journal.read()
        if event.event_type == "PHASE_CHANGED"
    ]
    assert [event.data for event in events] == [
        {
            "from": "RECOVER",
            "to": "PLAN",
        },
    ]


def test_engine_retry_requires_recover_phase(tmp_path):
    engine, state_store, journal, planner = make_engine(
        tmp_path,
        phase="VERIFY",
    )

    with pytest.raises(ValueError, match="cannot retry"):
        engine.retry()

    assert state_store.load().phase == "VERIFY"
    assert state_store.load().attempt == 0
    assert journal.read() == []


def test_engine_retry_requires_task_id(tmp_path):
    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    state_store.save(
        AgentState(
            task_id=None,
            goal="Read README.md",
            phase="RECOVER",
            failed=True,
        )
    )

    engine = AgentEngine(
        planner=MagicMock(),
        executor=MagicMock(),
        state_store=state_store,
        journal=journal,
    )

    with pytest.raises(ValueError, match="task_id"):
        engine.retry()

    assert state_store.load().phase == "RECOVER"
    assert journal.read() == []


def test_engine_retry_preserves_goal_progress(tmp_path):
    engine, state_store, journal, planner = make_engine(
        tmp_path,
        attempt=2,
    )

    state = state_store.load()
    state.progress = 75
    state_store.save(state)

    result = engine.retry()

    assert result.phase == "PLAN"
    assert result.attempt == 3
    assert result.progress == 75

    persisted = state_store.load()
    assert persisted.progress == 75
