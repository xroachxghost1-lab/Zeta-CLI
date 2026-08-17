from unittest.mock import MagicMock

import pytest

from zeta_cli.agent.engine import AgentEngine
from zeta_cli.events import EventJournal
from zeta_cli.state import AgentState, StateStore


def make_engine(tmp_path, phase="VERIFY"):
    planner = MagicMock()
    dispatcher = MagicMock()

    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    state_store.save(
        AgentState(
            task_id="task-1",
            goal="Read README.md",
            phase=phase,
        )
    )

    engine = AgentEngine(
        planner=planner,
        dispatcher=dispatcher,
        state_store=state_store,
        journal=journal,
    )

    return engine, state_store, journal, planner


def test_engine_recover_marks_task_failed(tmp_path):
    engine, state_store, journal, planner = make_engine(tmp_path)

    result = engine.recover()

    assert result.phase == "RECOVER"
    assert result.failed is True
    assert result.completed is False

    persisted = state_store.load()
    assert persisted.phase == "RECOVER"
    assert persisted.failed is True
    assert persisted.completed is False

    planner.plan.assert_not_called()

    events = journal.read()
    assert [event.data for event in events] == [
        {
            "from": "VERIFY",
            "to": "RECOVER",
        },
    ]


def test_engine_recover_requires_task_id(tmp_path):
    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    state_store.save(
        AgentState(
            task_id=None,
            goal="Read README.md",
            phase="VERIFY",
        )
    )

    engine = AgentEngine(
        planner=MagicMock(),
        dispatcher=MagicMock(),
        state_store=state_store,
        journal=journal,
    )

    with pytest.raises(ValueError, match="task_id"):
        engine.recover()

    assert state_store.load().phase == "VERIFY"
    assert journal.read() == []
