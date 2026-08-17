import pytest

from zeta_cli.agent.decision import DecisionEngine, Decision
from zeta_cli.verification.engine import VerificationResult


def test_decision_engine_completes_when_verification_passes():
    decision = DecisionEngine().decide(
        VerificationResult(
            passed=True,
            reason="all verification evidence passed",
        )
    )

    assert decision == Decision.COMPLETE


def test_decision_engine_recovers_when_verification_fails():
    decision = DecisionEngine().decide(
        VerificationResult(
            passed=False,
            reason="verification evidence failed",
        )
    )

    assert decision == Decision.RECOVER


def test_decision_engine_rejects_non_verification_result():
    with pytest.raises(TypeError, match="VerificationResult"):
        DecisionEngine().decide("passed")
