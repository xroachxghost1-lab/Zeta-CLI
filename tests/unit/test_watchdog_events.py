from zeta_cli.events import EventJournal
from zeta_cli.watchdog.actions import WatchdogAction
from zeta_cli.watchdog.events import WatchdogEventRecorder
from zeta_cli.watchdog.supervisor import WatchdogObservation


def observation(
    *,
    progressed: bool = False,
    stalled: bool = False,
    repeated: bool = False,
    healthy: bool = True,
) -> WatchdogObservation:
    return WatchdogObservation(
        progressed=progressed,
        stalled=stalled,
        repeated=repeated,
        healthy=healthy,
    )


def test_recorder_persists_watchdog_decision(tmp_path):
    journal = EventJournal(tmp_path / "events.jsonl")
    recorder = WatchdogEventRecorder(journal)

    recorder.record(
        task_id="task-1",
        observation=observation(stalled=True, healthy=False),
        action=WatchdogAction.RECOVER,
    )

    events = journal.read()

    assert len(events) == 1
    assert events[0].event_type == "WATCHDOG_DECISION"
    assert events[0].task_id == "task-1"
    assert events[0].data == {
        "action": "RECOVER",
        "healthy": False,
        "progressed": False,
        "repeated": False,
        "repeated_call": False,
        "stalled": True,
    }


def test_recorder_preserves_observation_flags(tmp_path):
    journal = EventJournal(tmp_path / "events.jsonl")
    recorder = WatchdogEventRecorder(journal)

    recorder.record(
        task_id="task-2",
        observation=observation(
            progressed=True,
            repeated=True,
            healthy=False,
        ),
        action=WatchdogAction.REPLAN,
    )

    event = journal.read()[0]

    assert event.data["progressed"] is True
    assert event.data["stalled"] is False
    assert event.data["repeated"] is True
    assert event.data["healthy"] is False
    assert event.data["action"] == "REPLAN"


def test_recorder_appends_without_replacing_existing_events(tmp_path):
    journal = EventJournal(tmp_path / "events.jsonl")

    from zeta_cli.events import Event

    journal.append(
        Event(
            event_type="TASK_STARTED",
            task_id="task-3",
        )
    )

    recorder = WatchdogEventRecorder(journal)
    recorder.record(
        task_id="task-3",
        observation=observation(),
        action=WatchdogAction.CONTINUE,
    )

    events = journal.read()

    assert [event.event_type for event in events] == [
        "TASK_STARTED",
        "WATCHDOG_DECISION",
    ]
