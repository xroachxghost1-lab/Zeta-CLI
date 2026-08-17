from unittest.mock import MagicMock

from zeta_cli.agent.engine import AgentEngine
from zeta_cli.api.models import CompletionResult
from zeta_cli.events import EventJournal
from zeta_cli.state import AgentState, StateStore


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


def test_engine_recover_records_watchdog_decision(tmp_path):
    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")


    state_store.save(
        AgentState(
            task_id="task-1",
            goal="Build the agent",
            phase="VERIFY",
        )
    )

    engine = AgentEngine(
        planner=MagicMock(),
        executor=MagicMock(),
        state_store=state_store,
        journal=journal,
    )

    engine.recover()

    watchdog_events = [
        event
        for event in journal.read()
        if event.event_type == "WATCHDOG_DECISION"
    ]

    assert len(watchdog_events) == 1
    assert watchdog_events[0].data["action"] == "CONTINUE"
    assert watchdog_events[0].data["progressed"] is True
    assert watchdog_events[0].data["healthy"] is True


def test_engine_retry_records_watchdog_decision(tmp_path):
    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")


    state_store.save(
        AgentState(
            task_id="task-1",
            goal="Build the agent",
            phase="RECOVER",
            attempt=1,
            failed=True,
        )
    )

    engine = AgentEngine(
        planner=MagicMock(),
        executor=MagicMock(),
        state_store=state_store,
        journal=journal,
    )

    engine.retry()

    watchdog_events = [
        event
        for event in journal.read()
        if event.event_type == "WATCHDOG_DECISION"
    ]

    assert len(watchdog_events) == 1
    assert watchdog_events[0].data["action"] == "CONTINUE"
    assert watchdog_events[0].data["progressed"] is True
    assert watchdog_events[0].data["healthy"] is True


def test_engine_observe_watchdog_returns_decision(tmp_path):
    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    engine = AgentEngine(
        planner=MagicMock(),
        executor=MagicMock(),
        state_store=state_store,
        journal=journal,
    )

    previous = AgentState(
        task_id="task-1",
        goal="Build the agent",
        phase="PLAN",
        progress=0,
    )
    current = AgentState(
        task_id="task-1",
        goal="Build the agent",
        phase="EXECUTE",
        progress=30,
    )

    observation, action = engine._observe_watchdog(previous, current)

    assert observation.progressed is True
    assert observation.healthy is True
    assert action.value == "CONTINUE"


def test_engine_observe_watchdog_returns_replan_for_repeated_progress(tmp_path):
    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    from zeta_cli.watchdog.coordinator import WatchdogCoordinator
    from zeta_cli.watchdog.events import WatchdogEventRecorder
    from zeta_cli.watchdog.supervisor import Watchdog

    watchdog = WatchdogCoordinator(
        recorder=WatchdogEventRecorder(journal),
        watchdog=Watchdog(stall_threshold=10, repeat_threshold=3, workspace_threshold=10),
    )

    engine = AgentEngine(
        planner=MagicMock(),
        executor=MagicMock(),
        state_store=state_store,
        journal=journal,
        watchdog=watchdog,
    )

    state = AgentState(
        task_id="task-1",
        goal="Build the agent",
        phase="EXECUTE",
        progress=30,
    )

    states = [
        AgentState(
            task_id="task-1",
            goal="Build the agent",
            phase="EXECUTE",
            progress=30,
        ),
        AgentState(
            task_id="task-1",
            goal="Build the agent",
            phase="EXECUTE",
            progress=31,
        ),
        AgentState(
            task_id="task-1",
            goal="Build the agent",
            phase="EXECUTE",
            progress=32,
        ),
        AgentState(
            task_id="task-1",
            goal="Build the agent",
            phase="EXECUTE",
            progress=33,
        ),
    ]

    decisions = [
        engine._observe_watchdog(
            states[i],
            states[i + 1],
            tool_call_fingerprint="same-call",
        )
        for i in range(3)
    ]

    assert decisions[-1][1].value == "REPLAN"
    assert decisions[-1][0].repeated_call is True
    assert decisions[-1][0].no_workspace_progress is False
    assert decisions[-1][0].stalled is False
    assert decisions[-1][0].healthy is False

from unittest.mock import Mock

from zeta_cli.agent.engine import AgentEngine
from zeta_cli.state import AgentState
from zeta_cli.watchdog.progress import ProgressRecord


def test_observe_watchdog_passes_result_and_reasoning_fingerprints():
    planner = Mock()
    state_store = Mock()
    journal = Mock()
    watchdog = Mock()

    state = AgentState(task_id="task-1", goal="test")

    engine = AgentEngine(
        planner=planner,
        state_store=state_store,
        journal=journal,
        watchdog=watchdog,
    )

    engine._observe_watchdog(
        state,
        state,
        tool_call_fingerprint="call-1",
        tool_result_fingerprint="result-1",
        reasoning="same reasoning",
    )

    watchdog.observe.assert_called_once()

    kwargs = watchdog.observe.call_args.kwargs

    assert kwargs["tool_call_fingerprint"] == "call-1"
    assert kwargs["tool_result_fingerprint"] == "result-1"
    assert kwargs["reasoning_fingerprint"] is not None
