from zeta_cli.verification.evidence import VerificationEvidence
from zeta_cli.verification.engine import VerificationResult
from zeta_cli.verification.policies import VerificationPolicy


def test_verification_evidence_stores_observation():
    evidence = VerificationEvidence(
        source="pytest",
        description="All tests passed",
        passed=True,
    )

    assert evidence.source == "pytest"
    assert evidence.description == "All tests passed"
    assert evidence.passed is True


def test_verification_result_defaults_to_failed():
    result = VerificationResult(
        passed=False,
        reason="Tests failed",
    )

    assert result.passed is False
    assert result.reason == "Tests failed"


def test_verification_policy_accepts_all_passing_evidence():
    policy = VerificationPolicy()

    evidence = [
        VerificationEvidence(
            source="pytest",
            description="All tests passed",
            passed=True,
        ),
    ]

    result = policy.evaluate(evidence)

    assert result.passed is True


def test_verification_policy_rejects_failed_evidence():
    policy = VerificationPolicy()

    evidence = [
        VerificationEvidence(
            source="pytest",
            description="Tests failed",
            passed=False,
        ),
    ]

    result = policy.evaluate(evidence)

    assert result.passed is False

