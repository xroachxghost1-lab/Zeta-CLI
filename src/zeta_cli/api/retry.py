from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class RetryPolicy:
    """Bounded exponential backoff policy."""

    max_attempts: int = 5
    base_delay: float = 1.0
    max_delay: float = 60.0
    jitter: float = 0.25

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        if self.base_delay < 0:
            raise ValueError("base_delay cannot be negative")

        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")

        if self.jitter < 0:
            raise ValueError("jitter cannot be negative")

    def delay_for(self, attempt: int) -> float:
        """Return the bounded delay for a zero-based retry attempt."""

        if attempt < 0:
            raise ValueError("attempt cannot be negative")

        exponential = self.base_delay * (2**attempt)
        bounded = min(exponential, self.max_delay)

        if self.jitter == 0:
            return bounded

        variation = bounded * self.jitter
        return min(
            self.max_delay,
            max(0.0, bounded + random.uniform(-variation, variation)),
        )

    def should_retry(self, attempt: int) -> bool:
        """Return whether another attempt is allowed."""

        return attempt < self.max_attempts - 1
