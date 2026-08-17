from __future__ import annotations

from zeta_cli.state import AgentState
from zeta_cli.watchdog.progress import ProgressRecord


def progress_record_from_state(state: AgentState) -> ProgressRecord:
    """Build a watchdog progress record from authoritative agent state."""

    return ProgressRecord(
        task_state_changed=state.phase != "BOOT",
        verification_state_changed=state.phase in {"VERIFY", "COMPLETE"},
        objective_distance=100 - state.progress,
    )
