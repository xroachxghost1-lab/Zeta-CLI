from unittest.mock import MagicMock

from zeta_cli.agent.engine import AgentEngine
from zeta_cli.api.models import CompletionResult
from zeta_cli.events import EventJournal
from zeta_cli.state import StateStore


def test_engine_start_records_watchdog_decision(tmp_path):
    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    planner = MagicMock()
    planner.plan.return_value = CompletionResult(
        content="Plan",
        model="mercury-2",
    )

    engine = AgentEngine(
        planner=planner,
        state_store=state_store,
        journal=journal,
    )

    engine.start(
        task_id="task-1",
        goal="Build the agent",
    )

    events = journal.read()

    watchdog_events = [
        event for event in events
        if event.event_type == "WATCHDOG_DECISION"
    ]

    assert len(watchdog_events) == 1
    assert watchdog_events[0].task_id == "task-1"
    assert watchdog_events[0].data["progressed"] is True
    assert watchdog_events[0].data["healthy"] is True
    assert watchdog_events[0].data["action"] == "CONTINUE"


def test_engine_accepts_custom_watchdog(tmp_path):
    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    watchdog = MagicMock()

    planner = MagicMock()
    planner.plan.return_value = CompletionResult(
        content="Plan",
        model="mercury-2",
    )

    engine = AgentEngine(
        planner=planner,
        state_store=state_store,
        journal=journal,
        watchdog=watchdog,
    )

    engine.start(
        task_id="task-1",
        goal="Build the agent",
    )

    watchdog.observe.assert_called_once()
