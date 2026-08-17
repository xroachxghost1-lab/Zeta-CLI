from __future__ import annotations

from zeta_cli.constants import ACTIVE_PHASES, ALL_PHASES, TERMINAL_PHASES
from zeta_cli.state.runtime import AgentState


class InvalidTransitionError(Exception):
    """Raised when an agent attempts an invalid phase transition."""


_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "BOOT": {"PLAN", "FAILED", "STOPPED"},
    "PLAN": {"EXECUTE", "FAILED", "STOPPED"},
    "EXECUTE": {"ASSESS", "RECOVER", "FAILED", "STOPPED"},
    "ASSESS": {"VERIFY", "RECOVER", "FAILED", "STOPPED"},
    "VERIFY": {"COMPLETE", "RECOVER", "FAILED", "STOPPED"},
    "RECOVER": {"PLAN", "EXECUTE", "FAILED", "STOPPED"},
}


def transition(state: AgentState, target: str) -> AgentState:
    """Safely transition an agent state to a valid next phase."""

    if target not in ALL_PHASES:
        raise InvalidTransitionError(
            f"unknown target phase: {target!r}"
        )

    current = state.phase

    if current in TERMINAL_PHASES:
        raise InvalidTransitionError(
            f"terminal phase {current!r} cannot transition "
            f"to {target!r}"
        )

    allowed = _ALLOWED_TRANSITIONS.get(current, set())

    if target not in allowed:
        raise InvalidTransitionError(
            f"invalid transition: {current!r} -> {target!r}"
        )

    state.phase = target

    if target == "COMPLETE":
        state.completed = True
        state.failed = False
    elif target == "FAILED":
        state.failed = True
        state.completed = False
    elif target == "STOPPED":
        state.completed = False

    return state


def transition_and_persist(
    state: AgentState,
    target: str,
    *,
    store,
    journal,
    task_id: str,
) -> AgentState:
    """Transition state, persist it, and record the phase-change event."""

    previous = state.phase

    transition(state, target)

    store.save(state)

    from zeta_cli.events import Event

    journal.append(
        Event(
            event_type="PHASE_CHANGED",
            task_id=task_id,
            data={
                "from": previous,
                "to": state.phase,
            },
        )
    )

    return state
