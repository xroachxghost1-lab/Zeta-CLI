from zeta_cli.state import AgentState
from zeta_cli.watchdog.snapshot import progress_record_from_state


def test_snapshot_defaults_workspace_progress_to_zero():
    state = AgentState(task_id="task-1", goal="test")

    record = progress_record_from_state(state)

    assert record.files_changed == 0
    assert record.files_created == 0
    assert record.files_deleted == 0


def test_snapshot_accepts_workspace_progress():
    state = AgentState(task_id="task-1", goal="test")

    record = progress_record_from_state(
        state,
        files_changed=2,
        files_created=1,
        files_deleted=1,
    )

    assert record.files_changed == 2
    assert record.files_created == 1
    assert record.files_deleted == 1
