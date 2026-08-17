import pytest

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
