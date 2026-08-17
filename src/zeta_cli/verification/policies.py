from __future__ import annotations

from collections.abc import Iterable

from zeta_cli.verification.evidence import VerificationEvidence
from zeta_cli.verification.engine import VerificationResult


class VerificationPolicy:
    """Default policy requiring every piece of evidence to pass."""

    def evaluate(
        self,
        evidence: Iterable[VerificationEvidence],
    ) -> VerificationResult:
        evidence = list(evidence)

        if not evidence:
            return VerificationResult(
                passed=False,
                reason="no verification evidence",
            )

        failed = [item for item in evidence if not item.passed]

        if failed:
            return VerificationResult(
                passed=False,
                reason="verification evidence failed",
            )

        return VerificationResult(
            passed=True,
            reason="all verification evidence passed",
        )
