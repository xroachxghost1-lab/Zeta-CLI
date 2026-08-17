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
    if observation.repeated and observation.stalled:
        return WatchdogAction.STOP

    if observation.stalled:
        if budget is not None and not budget.consume():
            return WatchdogAction.STOP
        return WatchdogAction.RECOVER

    if observation.repeated:
        return WatchdogAction.REPLAN

    return WatchdogAction.CONTINUE
