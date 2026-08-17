from __future__ import annotations

from zeta_cli.events import Event, EventJournal
from zeta_cli.watchdog.actions import WatchdogAction
from zeta_cli.watchdog.supervisor import WatchdogObservation


class WatchdogEventRecorder:
    """Persist watchdog observations and selected actions."""

    def __init__(self, journal: EventJournal) -> None:
        self.journal = journal

    def record(
        self,
        *,
        task_id: str,
        observation: WatchdogObservation,
        action: WatchdogAction,
    ) -> None:
        self.journal.append(
            Event(
                event_type="WATCHDOG_DECISION",
                task_id=task_id,
                data={
                    "action": action.value,
                    "progressed": observation.progressed,
                    "stalled": observation.stalled,
                    "repeated": observation.repeated,
                    "repeated_call": observation.repeated_call,
                    "healthy": observation.healthy,
                },
            )
        )
