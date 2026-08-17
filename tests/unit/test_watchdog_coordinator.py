from zeta_cli.events import EventJournal
from zeta_cli.watchdog.actions import WatchdogAction
from zeta_cli.watchdog.budget import RecoveryBudget
from zeta_cli.watchdog.coordinator import WatchdogCoordinator
from zeta_cli.watchdog.events import WatchdogEventRecorder
from zeta_cli.watchdog.progress import ProgressRecord
from zeta_cli.watchdog.supervisor import Watchdog


def make_coordinator(tmp_path, *, stall_threshold=3, max_attempts=None):
    journal = EventJournal(tmp_path / "events.jsonl")
    recorder = WatchdogEventRecorder(journal)

    budget = (
        RecoveryBudget(max_attempts=max_attempts)
        if max_attempts is not None
        else None
    )

    coordinator = WatchdogCoordinator(
        recorder=recorder,
        watchdog=Watchdog(stall_threshold=stall_threshold),
        budget=budget,
    )

    return coordinator, journal


def test_coordinator_returns_action_and_records_decision(tmp_path):
    coordinator, journal = make_coordinator(tmp_path)

    observation, action = coordinator.observe(
        task_id="task-1",
        previous=ProgressRecord(),
        current=ProgressRecord(files_changed=1),
    )

    assert observation.progressed is True
    assert action is WatchdogAction.CONTINUE

    events = journal.read()
    assert len(events) == 1
    assert events[0].event_type == "WATCHDOG_DECISION"
    assert events[0].data["action"] == "CONTINUE"


def test_coordinator_consumes_recovery_budget(tmp_path):
    coordinator, journal = make_coordinator(
        tmp_path,
        stall_threshold=1,
        max_attempts=1,
    )

    progress = ProgressRecord()

    _, first_action = coordinator.observe(
        task_id="task-2",
        previous=progress,
        current=progress,
    )
    _, second_action = coordinator.observe(
        task_id="task-2",
        previous=progress,
        current=progress,
    )

    assert first_action is WatchdogAction.RECOVER
    assert second_action is WatchdogAction.STOP
    assert coordinator.budget.attempts == 1

    events = journal.read()
    assert [event.data["action"] for event in events] == [
        "RECOVER",
        "STOP",
    ]


def test_coordinator_reset_clears_watchdog_state(tmp_path):
    coordinator, _ = make_coordinator(
        tmp_path,
        stall_threshold=1,
    )

    progress = ProgressRecord()

    coordinator.observe(
        task_id="task-3",
        previous=progress,
        current=progress,
    )

    coordinator.reset()

    observation, action = coordinator.observe(
        task_id="task-3",
        previous=progress,
        current=ProgressRecord(files_changed=1),
    )

    assert observation.stalled is False
    assert action is WatchdogAction.CONTINUE
