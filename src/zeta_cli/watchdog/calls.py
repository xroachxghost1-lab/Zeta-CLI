from __future__ import annotations

from collections import deque


class CallHistoryDetector:
    """Detect repeated tool-call fingerprints."""

    def __init__(self, *, threshold: int = 3, history_size: int = 32) -> None:
        if threshold <= 0:
            raise ValueError("threshold must be greater than zero")
        if history_size <= 0:
            raise ValueError("history_size must be greater than zero")

        self.threshold = threshold
        self.history_size = history_size
        self._calls: deque[str] = deque(maxlen=history_size)

    def observe(self, fingerprint: str | None) -> bool:
        if fingerprint is None:
            return False

        self._calls.append(fingerprint)

        if len(self._calls) < self.threshold:
            return False

        recent = list(self._calls)[-self.threshold:]
        return len(set(recent)) == 1

    def reset(self) -> None:
        self._calls.clear()
