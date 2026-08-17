from unittest.mock import MagicMock

import pytest

from zeta_cli.agent.engine import AgentEngine
from zeta_cli.events import EventJournal
from zeta_cli.state import AgentState, StateStore


def make_engine(tmp_path, phase):
    planner = MagicMock()
    executor = MagicMock()

    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    state_store.save(
        AgentState(
            task_id="task-1",
            goal="Read README.md",
            phase=phase,
        )
    )

    return (
        AgentEngine(
            planner=planner,
            executor=executor,
            state_store=state_store,
            journal=journal,
        ),
        state_store,
        journal,
    )


def test_engine_complete_transitions_verify_to_complete(tmp_path):
    engine, state_store, journal = make_engine(
        tmp_path,
        "VERIFY",
    )

    result = engine.complete()

    assert result is state_store.load()
    assert result.phase == "COMPLETE"
    assert result.completed is True
    assert result.failed is False

    events = [
        event for event in journal.read()
        if event.event_type == "PHASE_CHANGED"
    ]
    assert len(events) == 1
    assert events[0].data == {
        "from": "VERIFY",
        "to": "COMPLETE",
    }


def test_engine_complete_requires_verify_phase(tmp_path):
    engine, state_store, journal = make_engine(
        tmp_path,
        "ASSESS",
    )

    with pytest.raises(ValueError, match="cannot complete"):
        engine.complete()

    assert state_store.load().phase == "ASSESS"
    assert journal.read() == []


def test_engine_recover_transitions_verify_to_recover(tmp_path):
    engine, state_store, journal = make_engine(
        tmp_path,
        "VERIFY",
    )

    result = engine.recover()

    assert result is state_store.load()
    assert result.phase == "RECOVER"

    events = [
        event for event in journal.read()
        if event.event_type == "PHASE_CHANGED"
    ]
    assert len(events) == 1
    assert events[0].data == {
        "from": "VERIFY",
        "to": "RECOVER",
    }


def test_engine_recover_requires_verify_phase(tmp_path):
    engine, state_store, journal = make_engine(
        tmp_path,
        "ASSESS",
    )

    with pytest.raises(ValueError, match="cannot recover"):
        engine.recover()

    assert state_store.load().phase == "ASSESS"
    assert journal.read() == []


def test_engine_complete_sets_goal_progress_to_100(tmp_path):
    planner = MagicMock()
    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    state_store.save(
        AgentState(
            task_id="task-1",
            goal="Read README.md",
            phase="VERIFY",
            progress=75,
        )
    )

    engine = AgentEngine(
        planner=planner,
        state_store=state_store,
        journal=journal,
    )

    result = engine.complete()

    assert result.phase == "COMPLETE"
    assert result.progress == 100

    persisted = state_store.load()
    assert persisted.progress == 100


def test_engine_recover_preserves_goal_progress(tmp_path):
    planner = MagicMock()
    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    state_store.save(
        AgentState(
            task_id="task-1",
            goal="Read README.md",
            phase="VERIFY",
            progress=75,
        )
    )

    engine = AgentEngine(
        planner=planner,
        state_store=state_store,
        journal=journal,
    )

    result = engine.recover()

    assert result.phase == "RECOVER"
    assert result.progress == 75

    persisted = state_store.load()
    assert persisted.progress == 75
