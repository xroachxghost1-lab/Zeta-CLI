from __future__ import annotations

from zeta_cli.watchdog.progress import ProgressRecord


class WorkspaceProgressDetector:
    """Detect consecutive iterations without workspace changes."""

    def __init__(self, threshold: int = 3) -> None:
        if threshold <= 0:
            raise ValueError("threshold must be positive")

        self.threshold = threshold
        self.consecutive_no_progress = 0

    def observe(
        self,
        previous: ProgressRecord,
        current: ProgressRecord,
    ) -> bool:
        """Record workspace activity and return whether progress has stalled."""
        changed = (
            current.files_changed != previous.files_changed
            or current.files_created != previous.files_created
            or current.files_deleted != previous.files_deleted
        )

        if changed:
            self.consecutive_no_progress = 0
            return False

        self.consecutive_no_progress += 1
        return self.consecutive_no_progress >= self.threshold

    def reset(self) -> None:
        self.consecutive_no_progress = 0
