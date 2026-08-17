from __future__ import annotations

from zeta_cli.state import AgentState
from zeta_cli.watchdog.progress import ProgressRecord


def progress_record_from_state(
    state: AgentState,
    *,
    files_changed: int = 0,
    files_created: int = 0,
    files_deleted: int = 0,
) -> ProgressRecord:
    """Build a watchdog progress record from authoritative agent state."""

    return ProgressRecord(
        files_changed=files_changed,
        files_created=files_created,
        files_deleted=files_deleted,
        task_state_changed=state.phase != "BOOT",
        verification_state_changed=state.phase in {"VERIFY", "COMPLETE"},
        objective_distance=100 - state.progress,
    )
