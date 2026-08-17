from __future__ import annotations

from enum import Enum

from zeta_cli.watchdog.supervisor import WatchdogObservation


class WatchdogAction(str, Enum):
    CONTINUE = "CONTINUE"
    REPLAN = "REPLAN"
    RECOVER = "RECOVER"
    STOP = "STOP"


def choose_action(observation: WatchdogObservation) -> WatchdogAction:
    """Select the safest watchdog action for an observation."""
    if observation.repeated and observation.stalled:
        return WatchdogAction.STOP

    if observation.stalled:
        return WatchdogAction.RECOVER

    if observation.repeated:
        return WatchdogAction.REPLAN

    return WatchdogAction.CONTINUE
