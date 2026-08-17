from zeta_cli.events import Event, EventJournal


def test_event_defaults():
    event = Event(
        event_type="TASK_STARTED",
        task_id="task-1",
    )

    assert event.event_type == "TASK_STARTED"
    assert event.task_id == "task-1"
    assert event.data == {}


def test_event_can_store_data():
    event = Event(
        event_type="TOOL_COMPLETED",
        task_id="task-1",
        data={
            "tool": "shell",
            "exit_code": 0,
        },
    )

    assert event.data["tool"] == "shell"
    assert event.data["exit_code"] == 0


def test_journal_append_and_read(tmp_path):
    journal = EventJournal(tmp_path / "events.jsonl")

    journal.append(
        Event(
            event_type="TASK_STARTED",
            task_id="task-1",
        )
    )

    journal.append(
        Event(
            event_type="PHASE_CHANGED",
            task_id="task-1",
            data={"from": "BOOT", "to": "PLAN"},
        )
    )

    events = journal.read()

    assert len(events) == 2
    assert events[0].event_type == "TASK_STARTED"
    assert events[1].event_type == "PHASE_CHANGED"
    assert events[1].data["to"] == "PLAN"


def test_journal_preserves_event_order(tmp_path):
    journal = EventJournal(tmp_path / "events.jsonl")

    for index in range(5):
        journal.append(
            Event(
                event_type="STEP",
                task_id="task-1",
                data={"index": index},
            )
        )

    events = journal.read()

    assert [event.data["index"] for event in events] == [
        0,
        1,
        2,
        3,
        4,
    ]


def test_missing_journal_is_empty(tmp_path):
    journal = EventJournal(tmp_path / "missing.jsonl")

    assert journal.read() == []


def test_journal_creates_parent_directory(tmp_path):
    path = tmp_path / "nested" / "events" / "journal.jsonl"

    journal = EventJournal(path)

    journal.append(
        Event(
            event_type="TASK_STARTED",
            task_id="task-1",
        )
    )

    assert path.exists()
