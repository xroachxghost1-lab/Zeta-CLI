from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VerificationEvidence:
    """A single piece of evidence used to verify a task."""

    source: str
    description: str
    passed: bool
