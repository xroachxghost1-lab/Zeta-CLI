from __future__ import annotations


class RepeatDetector:
    """Detect consecutive identical observations."""

    def __init__(self, threshold: int = 3) -> None:
        if threshold <= 0:
            raise ValueError("threshold must be positive")

        self.threshold = threshold
        self.consecutive_repeats = 0
        self._previous: object = None
        self._has_previous = False

    def observe(self, value: object) -> bool:
        """Record an observation and return whether repetition is detected."""
        if not self._has_previous or value != self._previous:
            self._previous = value
            self._has_previous = True
            self.consecutive_repeats = 0
            return False

        self.consecutive_repeats += 1
        return self.consecutive_repeats >= self.threshold

    def reset(self) -> None:
        self._previous = None
        self._has_previous = False
        self.consecutive_repeats = 0
