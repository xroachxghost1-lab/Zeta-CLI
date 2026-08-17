from zeta_cli.events import EventJournal
from zeta_cli.state import AgentState, StateStore
from zeta_cli.state.transitions import transition_and_persist


def test_transition_and_persist_updates_state(tmp_path):
    state_path = tmp_path / "state.json"
    event_path = tmp_path / "events.jsonl"

    store = StateStore(state_path)
    journal = EventJournal(event_path)

    state = AgentState()

    transition_and_persist(
        state,
        "PLAN",
        store=store,
        journal=journal,
        task_id="task-1",
    )

    restored = store.load()

    assert restored.phase == "PLAN"


def test_transition_and_persist_records_event(tmp_path):
    store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    state = AgentState()

    transition_and_persist(
        state,
        "PLAN",
        store=store,
        journal=journal,
        task_id="task-1",
    )

    events = journal.read()

    assert len(events) == 1
    assert events[0].event_type == "PHASE_CHANGED"
    assert events[0].task_id == "task-1"
    assert events[0].data["from"] == "BOOT"
    assert events[0].data["to"] == "PLAN"


def test_multiple_transitions_preserve_history(tmp_path):
    store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    state = AgentState()

    transition_and_persist(
        state,
        "PLAN",
        store=store,
        journal=journal,
        task_id="task-1",
    )

    transition_and_persist(
        state,
        "EXECUTE",
        store=store,
        journal=journal,
        task_id="task-1",
    )

    transition_and_persist(
        state,
        "ASSESS",
        store=store,
        journal=journal,
        task_id="task-1",
    )

    events = journal.read()

    assert [event.data["to"] for event in events] == [
        "PLAN",
        "EXECUTE",
        "ASSESS",
    ]


def test_persisted_terminal_state_is_restored(tmp_path):
    store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    state = AgentState(phase="VERIFY")

    transition_and_persist(
        state,
        "COMPLETE",
        store=store,
        journal=journal,
        task_id="task-1",
    )

    restored = store.load()

    assert restored.phase == "COMPLETE"
    assert restored.completed is True
