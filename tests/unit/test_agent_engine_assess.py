from unittest.mock import MagicMock

import pytest

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
            phase="EXECUTE",
        )
    )

    return AgentEngine(
        planner=planner,
        executor=executor,
        state_store=state_store,
        journal=journal,
    ), state_store, journal


def test_engine_assess_successful_result(tmp_path):
    planner = MagicMock()
    executor = MagicMock()

    engine, state_store, journal = make_engine(
        tmp_path,
        planner,
        executor,
    )

    result = engine.assess(
        ToolResult.from_value("README contents")
    )

    assert result.passed is True
    assert result.value == "README contents"
    assert result.error is None

    planner.plan.assert_not_called()

    state = state_store.load()
    assert state.phase == "ASSESS"

    events = journal.read()
    assert len(events) == 1
    assert events[0].data == {
        "from": "EXECUTE",
        "to": "ASSESS",
    }


def test_engine_assess_requires_execute_phase(tmp_path):
    planner = MagicMock()
    executor = MagicMock()

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
        executor=executor,
        state_store=state_store,
        journal=journal,
    )

    with pytest.raises(ValueError, match="cannot assess"):
        engine.assess(
            ToolResult.from_value("README contents")
        )

    planner.plan.assert_not_called()


def test_engine_assess_requires_task_goal(tmp_path):
    planner = MagicMock()
    executor = MagicMock()

    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    state_store.save(
        AgentState(
            task_id="task-1",
            goal=None,
            phase="EXECUTE",
        )
    )

    engine = AgentEngine(
        planner=planner,
        executor=executor,
        state_store=state_store,
        journal=journal,
    )

    with pytest.raises(ValueError, match="goal"):
        engine.assess(
            ToolResult.from_value("README contents")
        )


def test_engine_assess_uses_assessor(tmp_path):
    planner = MagicMock()
    executor = MagicMock()
    assessor = MagicMock()
    assessor.assess.return_value = "assessed"

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
        assessor=assessor,
        state_store=state_store,
        journal=journal,
    )

    result = ToolResult.from_value("README contents")

    assessed = engine.assess(result)

    assessor.assess.assert_called_once_with(result)
    assert assessed == "assessed"
