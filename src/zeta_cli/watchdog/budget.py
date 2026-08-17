from __future__ import annotations


class RecoveryBudget:
    def __init__(self, max_attempts: int) -> None:
        if max_attempts <= 0:
            raise ValueError("max_attempts must be positive")

        self.max_attempts = max_attempts
        self.attempts = 0

    @property
    def exhausted(self) -> bool:
        return self.attempts >= self.max_attempts

    def consume(self) -> bool:
        if self.exhausted:
            return False

        self.attempts += 1
        return True
