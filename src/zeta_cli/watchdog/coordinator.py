from __future__ import annotations

from zeta_cli.watchdog.actions import WatchdogAction, choose_action
from zeta_cli.watchdog.budget import RecoveryBudget
from zeta_cli.watchdog.events import WatchdogEventRecorder
from zeta_cli.watchdog.progress import ProgressRecord
from zeta_cli.watchdog.supervisor import Watchdog, WatchdogObservation


class WatchdogCoordinator:
    """Observe agent progress, choose an action, and persist the decision."""

    def __init__(
        self,
        *,
        recorder: WatchdogEventRecorder,
        watchdog: Watchdog | None = None,
        budget: RecoveryBudget | None = None,
    ) -> None:
        self.watchdog = watchdog or Watchdog()
        self.budget = budget
        self.recorder = recorder

    def observe(
        self,
        *,
        task_id: str,
        previous: ProgressRecord,
        current: ProgressRecord,
    ) -> tuple[WatchdogObservation, WatchdogAction]:
        observation = self.watchdog.observe(previous, current)
        action = choose_action(observation, budget=self.budget)

        self.recorder.record(
            task_id=task_id,
            observation=observation,
            action=action,
        )

        return observation, action

    def reset(self) -> None:
        self.watchdog.reset()
