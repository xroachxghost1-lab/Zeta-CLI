from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VerificationResult:
    """Outcome of evaluating verification evidence."""

    passed: bool
    reason: str
