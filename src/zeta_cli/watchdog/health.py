from __future__ import annotations


class StallDetector:
    """Detect consecutive observations without meaningful progress."""

    def __init__(self, threshold: int = 3) -> None:
        if threshold <= 0:
            raise ValueError("threshold must be positive")

        self.threshold = threshold
        self.consecutive_stalls = 0

    def observe(self, progressed: bool) -> bool:
        """Record an observation and return whether a stall is detected."""
        if progressed:
            self.consecutive_stalls = 0
            return False

        self.consecutive_stalls += 1
        return self.consecutive_stalls >= self.threshold

    def reset(self) -> None:
        self.consecutive_stalls = 0
