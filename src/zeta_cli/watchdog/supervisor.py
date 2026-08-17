from __future__ import annotations

from dataclasses import dataclass

from zeta_cli.watchdog.calls import CallHistoryDetector
from zeta_cli.watchdog.health import StallDetector
from zeta_cli.watchdog.loops import RepeatDetector
from zeta_cli.watchdog.progress import ProgressRecord, progress_changed


@dataclass(frozen=True)
class WatchdogObservation:
    """Result of one watchdog observation."""

    progressed: bool
    stalled: bool
    repeated: bool
    repeated_call: bool = False
    repeated_result: bool = False
    healthy: bool = True


class Watchdog:
    """Coordinate watchdog checks for agent iterations."""

    def __init__(
        self,
        *,
        stall_threshold: int = 3,
        repeat_threshold: int = 3,
        call_threshold: int = 3,
    ) -> None:
        self.stall_detector = StallDetector(threshold=stall_threshold)
        self.repeat_detector = RepeatDetector(threshold=repeat_threshold)
        self.call_detector = CallHistoryDetector(threshold=call_threshold)
        self.result_detector = CallHistoryDetector(threshold=call_threshold)

    def observe(
        self,
        previous_progress: ProgressRecord,
        current_progress: ProgressRecord,
        *,
        tool_call_fingerprint: str | None = None,
        tool_result_fingerprint: str | None = None,
    ) -> WatchdogObservation:
        progressed = progress_changed(previous_progress, current_progress)

        stalled = self.stall_detector.observe(progressed)
        repeated = self.repeat_detector.observe(current_progress)
        repeated_call = self.call_detector.observe(tool_call_fingerprint)
        repeated_result = self.result_detector.observe(tool_result_fingerprint)

        return WatchdogObservation(
            progressed=progressed,
            stalled=stalled,
            repeated=repeated,
            repeated_call=repeated_call,
            repeated_result=repeated_result,
            healthy=(
                not stalled
                and not repeated
                and not repeated_call
                and not repeated_result
            ),
        )

    def reset(self) -> None:
        self.stall_detector.reset()
        self.repeat_detector.reset()
        self.call_detector.reset()
        self.result_detector.reset()
