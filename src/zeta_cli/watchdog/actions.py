from __future__ import annotations

from enum import Enum

from zeta_cli.watchdog.budget import RecoveryBudget
from zeta_cli.watchdog.supervisor import WatchdogObservation


class WatchdogAction(str, Enum):
    CONTINUE = "CONTINUE"
    REPLAN = "REPLAN"
    RECOVER = "RECOVER"
    STOP = "STOP"


def choose_action(
    observation: WatchdogObservation,
    *,
    budget: RecoveryBudget | None = None,
) -> WatchdogAction:
    """Select the safest watchdog action for an observation."""
    repeated_signal = (
        observation.repeated
        or observation.repeated_call
        or observation.repeated_result
        or observation.repeated_reasoning
    )

    if repeated_signal and (
        observation.stalled or observation.no_workspace_progress
    ):
        return WatchdogAction.STOP

    if repeated_signal:
        return WatchdogAction.REPLAN

    if observation.stalled or observation.no_workspace_progress:
        if budget is not None and not budget.consume():
            return WatchdogAction.STOP
        return WatchdogAction.RECOVER

    return WatchdogAction.CONTINUE
