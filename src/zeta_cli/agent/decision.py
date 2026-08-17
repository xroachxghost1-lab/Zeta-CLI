from __future__ import annotations

from enum import Enum

from zeta_cli.verification.engine import VerificationResult


class Decision(str, Enum):
    """Next lifecycle action selected from a verification result."""

    COMPLETE = "COMPLETE"
    RECOVER = "RECOVER"


class DecisionEngine:
    """Translate verification outcomes into lifecycle decisions."""

    def decide(self, result: VerificationResult) -> Decision:
        if not isinstance(result, VerificationResult):
            raise TypeError("decide expects a VerificationResult")

        if result.passed:
            return Decision.COMPLETE

        return Decision.RECOVER
