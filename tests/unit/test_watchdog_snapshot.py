from zeta_cli.state import AgentState
from zeta_cli.watchdog.progress import ProgressRecord
from zeta_cli.watchdog.snapshot import progress_record_from_state


def test_boot_state_has_no_lifecycle_progress():
    state = AgentState()

    assert progress_record_from_state(state) == ProgressRecord(
        task_state_changed=False,
        verification_state_changed=False,
        objective_distance=100,
    )


def test_plan_state_records_task_progress():
    state = AgentState(
        task_id="task-1",
        goal="Build the agent",
        phase="PLAN",
        progress=10,
    )

    record = progress_record_from_state(state)

    assert record.task_state_changed is True
    assert record.verification_state_changed is False
    assert record.objective_distance == 90


def test_verify_state_records_verification_progress():
    state = AgentState(
        task_id="task-1",
        goal="Build the agent",
        phase="VERIFY",
        progress=75,
    )

    record = progress_record_from_state(state)

    assert record.task_state_changed is True
    assert record.verification_state_changed is True
    assert record.objective_distance == 25


def test_complete_state_has_zero_objective_distance():
    state = AgentState(
        task_id="task-1",
        goal="Build the agent",
        phase="COMPLETE",
        progress=100,
        completed=True,
    )

    record = progress_record_from_state(state)

    assert record.objective_distance == 0
    assert record.verification_state_changed is True
