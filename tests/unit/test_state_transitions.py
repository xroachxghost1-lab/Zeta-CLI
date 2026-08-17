import pytest

from zeta_cli.constants import ALL_PHASES

from zeta_cli.state import AgentState, StateStore
from zeta_cli.state.transitions import (
    InvalidTransitionError,
    transition,
)


def test_boot_can_transition_to_plan():
    state = AgentState()

    transition(state, "PLAN")

    assert state.phase == "PLAN"


def test_plan_can_transition_to_execute():
    state = AgentState(phase="PLAN")

    transition(state, "EXECUTE")

    assert state.phase == "EXECUTE"


def test_execute_can_transition_to_assess():
    state = AgentState(phase="EXECUTE")

    transition(state, "ASSESS")

    assert state.phase == "ASSESS"


def test_assess_can_transition_to_verify():
    state = AgentState(phase="ASSESS")

    transition(state, "VERIFY")

    assert state.phase == "VERIFY"


def test_verify_can_complete():
    state = AgentState(phase="VERIFY")

    transition(state, "COMPLETE")

    assert state.phase == "COMPLETE"
    assert state.completed is True
    assert state.failed is False


def test_execute_can_recover():
    state = AgentState(phase="EXECUTE")

    transition(state, "RECOVER")

    assert state.phase == "RECOVER"


def test_recover_can_return_to_execute():
    state = AgentState(phase="RECOVER")

    transition(state, "EXECUTE")

    assert state.phase == "EXECUTE"


def test_any_active_phase_can_fail():
    for phase in ("BOOT", "PLAN", "EXECUTE", "ASSESS", "VERIFY", "RECOVER"):
        state = AgentState(phase=phase)

        transition(state, "FAILED")

        assert state.phase == "FAILED"
        assert state.failed is True


def test_active_phase_can_stop():
    state = AgentState(phase="EXECUTE")

    transition(state, "STOPPED")

    assert state.phase == "STOPPED"


def test_terminal_states_cannot_transition():
    for phase in ("COMPLETE", "FAILED", "STOPPED"):
        state = AgentState(phase=phase)

        with pytest.raises(InvalidTransitionError):
            transition(state, "EXECUTE")


def test_invalid_transition_is_rejected():
    state = AgentState(phase="BOOT")

    with pytest.raises(InvalidTransitionError):
        transition(state, "VERIFY")


def test_transition_can_persist_state(tmp_path):
    store = StateStore(tmp_path / "state.json")
    state = AgentState()

    transition(state, "PLAN")
    store.save(state)

    restored = store.load()

    assert restored.phase == "PLAN"


@pytest.mark.parametrize(
    ("current", "target"),
    [
        ("BOOT", "PLAN"),
        ("BOOT", "FAILED"),
        ("BOOT", "STOPPED"),
        ("PLAN", "EXECUTE"),
        ("PLAN", "FAILED"),
        ("PLAN", "STOPPED"),
        ("EXECUTE", "ASSESS"),
        ("EXECUTE", "RECOVER"),
        ("EXECUTE", "FAILED"),
        ("EXECUTE", "STOPPED"),
        ("ASSESS", "VERIFY"),
        ("ASSESS", "RECOVER"),
        ("ASSESS", "FAILED"),
        ("ASSESS", "STOPPED"),
        ("VERIFY", "COMPLETE"),
        ("VERIFY", "RECOVER"),
        ("VERIFY", "FAILED"),
        ("VERIFY", "STOPPED"),
        ("RECOVER", "PLAN"),
        ("RECOVER", "EXECUTE"),
        ("RECOVER", "FAILED"),
        ("RECOVER", "STOPPED"),
    ],
)
def test_all_allowed_transitions_are_accepted(current, target):
    state = AgentState(
        task_id="task-1",
        goal="Read README.md",
        phase=current,
    )

    transition(state, target)

    assert state.phase == target


@pytest.mark.parametrize(
    ("current", "target"),
    [
        ("BOOT", "EXECUTE"),
        ("BOOT", "ASSESS"),
        ("PLAN", "ASSESS"),
        ("PLAN", "VERIFY"),
        ("EXECUTE", "PLAN"),
        ("EXECUTE", "VERIFY"),
        ("ASSESS", "PLAN"),
        ("ASSESS", "EXECUTE"),
        ("VERIFY", "PLAN"),
        ("VERIFY", "EXECUTE"),
        ("VERIFY", "ASSESS"),
        ("RECOVER", "ASSESS"),
        ("RECOVER", "VERIFY"),
        ("COMPLETE", "PLAN"),
        ("FAILED", "PLAN"),
        ("STOPPED", "PLAN"),
    ],
)
def test_invalid_phase_transitions_are_rejected(current, target):
    state = AgentState(
        task_id="task-1",
        goal="Read README.md",
        phase=current,
    )

    with pytest.raises(InvalidTransitionError):
        transition(state, target)


def test_unknown_target_phase_is_rejected():
    state = AgentState(
        task_id="task-1",
        goal="Read README.md",
        phase="PLAN",
    )

    with pytest.raises(InvalidTransitionError, match="unknown target phase"):
        transition(state, "NOT_A_PHASE")


@pytest.mark.parametrize("phase", ["COMPLETE", "FAILED", "STOPPED"])
def test_terminal_phase_cannot_transition_to_any_phase(phase):
    state = AgentState(
        task_id="task-1",
        goal="Read README.md",
        phase=phase,
    )

    for target in ALL_PHASES:
        with pytest.raises(InvalidTransitionError):
            transition(state, target)


def test_invalid_transition_does_not_mutate_state():
    state = AgentState(
        task_id="task-1",
        goal="Read README.md",
        phase="PLAN",
    )

    with pytest.raises(InvalidTransitionError):
        transition(state, "VERIFY")

    assert state.phase == "PLAN"
    assert state.completed is False
    assert state.failed is False


@pytest.mark.parametrize(
    ("current", "target", "progress"),
    [
        ("BOOT", "PLAN", 10),
        ("PLAN", "EXECUTE", 30),
        ("EXECUTE", "ASSESS", 50),
        ("ASSESS", "VERIFY", 75),
        ("VERIFY", "COMPLETE", 100),
    ],
)
def test_lifecycle_transitions_update_goal_progress(
    current,
    target,
    progress,
):
    state = AgentState(
        task_id="task-1",
        goal="Read README.md",
        phase=current,
    )

    transition(state, target)

    assert state.phase == target
    assert state.progress == progress


def test_recover_does_not_reset_goal_progress():
    state = AgentState(
        task_id="task-1",
        goal="Read README.md",
        phase="EXECUTE",
        progress=30,
    )

    transition(state, "RECOVER")

    assert state.phase == "RECOVER"
    assert state.progress == 30


@pytest.mark.parametrize("target", ["FAILED", "STOPPED"])
def test_failure_or_stop_does_not_change_goal_progress(target):
    state = AgentState(
        task_id="task-1",
        goal="Read README.md",
        phase="EXECUTE",
        progress=30,
    )

    transition(state, target)

    assert state.phase == target
    assert state.progress == 30
