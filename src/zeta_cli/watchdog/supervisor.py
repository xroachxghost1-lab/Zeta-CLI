from __future__ import annotations

from dataclasses import dataclass

from zeta_cli.watchdog.health import StallDetector
from zeta_cli.watchdog.loops import RepeatDetector
from zeta_cli.watchdog.progress import ProgressRecord, progress_changed


@dataclass(frozen=True)
class WatchdogObservation:
    """Result of one watchdog observation."""

    progressed: bool
    stalled: bool
    repeated: bool
    healthy: bool


class Watchdog:
    """Coordinate watchdog checks for agent iterations."""

    def __init__(
        self,
        *,
        stall_threshold: int = 3,
        repeat_threshold: int = 3,
    ) -> None:
        self.stall_detector = StallDetector(threshold=stall_threshold)
        self.repeat_detector = RepeatDetector(threshold=repeat_threshold)

    def observe(
        self,
        previous_progress: ProgressRecord,
        current_progress: ProgressRecord,
    ) -> WatchdogObservation:
        progressed = progress_changed(previous_progress, current_progress)

        stalled = self.stall_detector.observe(progressed)
        repeated = self.repeat_detector.observe(current_progress)

        return WatchdogObservation(
            progressed=progressed,
            stalled=stalled,
            repeated=repeated,
            healthy=not stalled and not repeated,
        )

    def reset(self) -> None:
        self.stall_detector.reset()
        self.repeat_detector.reset()
