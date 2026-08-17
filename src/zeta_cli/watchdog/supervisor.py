from __future__ import annotations

from dataclasses import dataclass

from zeta_cli.watchdog.calls import CallHistoryDetector
from zeta_cli.watchdog.health import StallDetector
from zeta_cli.watchdog.loops import RepeatDetector
from zeta_cli.watchdog.progress import ProgressRecord, progress_changed
from zeta_cli.watchdog.workspace import WorkspaceProgressDetector


@dataclass(frozen=True)
class WatchdogObservation:
    """Result of one watchdog observation."""

    progressed: bool
    stalled: bool
    repeated: bool
    repeated_call: bool = False
    repeated_result: bool = False
    repeated_reasoning: bool = False
    no_workspace_progress: bool = False
    healthy: bool = True


class Watchdog:
    """Coordinate watchdog checks for agent iterations."""

    def __init__(
        self,
        *,
        stall_threshold: int = 3,
        repeat_threshold: int = 3,
        call_threshold: int = 3,
        workspace_threshold: int = 3,
    ) -> None:
        self.stall_detector = StallDetector(threshold=stall_threshold)
        self.repeat_detector = RepeatDetector(threshold=repeat_threshold)
        self.call_detector = CallHistoryDetector(threshold=call_threshold)
        self.result_detector = CallHistoryDetector(threshold=call_threshold)
        self.reasoning_detector = CallHistoryDetector(threshold=call_threshold)
        self.workspace_detector = WorkspaceProgressDetector(threshold=workspace_threshold)

    def observe(
        self,
        previous_progress: ProgressRecord,
        current_progress: ProgressRecord,
        *,
        tool_call_fingerprint: str | None = None,
        tool_result_fingerprint: str | None = None,
        reasoning_fingerprint: str | None = None,
    ) -> WatchdogObservation:
        progressed = progress_changed(previous_progress, current_progress)

        stalled = self.stall_detector.observe(progressed)
        repeated = self.repeat_detector.observe(current_progress)
        repeated_call = self.call_detector.observe(tool_call_fingerprint)
        repeated_result = self.result_detector.observe(tool_result_fingerprint)
        repeated_reasoning = self.reasoning_detector.observe(reasoning_fingerprint)
        no_workspace_progress = self.workspace_detector.observe(
            previous_progress,
            current_progress,
        )

        return WatchdogObservation(
            progressed=progressed,
            stalled=stalled,
            repeated=repeated,
            repeated_call=repeated_call,
            repeated_result=repeated_result,
            repeated_reasoning=repeated_reasoning,
            no_workspace_progress=no_workspace_progress,
            healthy=(
                not stalled
                and not repeated
                and not repeated_call
                and not repeated_result
                and not repeated_reasoning
                and not no_workspace_progress
            ),
        )

    def reset(self) -> None:
        self.stall_detector.reset()
        self.repeat_detector.reset()
        self.call_detector.reset()
        self.result_detector.reset()
        self.reasoning_detector.reset()
        self.workspace_detector.reset()
