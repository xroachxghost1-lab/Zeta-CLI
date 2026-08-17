import pytest

from zeta_cli.watchdog.budget import RecoveryBudget


def test_budget_starts_unused():
    budget = RecoveryBudget(max_attempts=3)

    assert budget.attempts == 0
    assert budget.exhausted is False


def test_consume_allows_recovery():
    budget = RecoveryBudget(max_attempts=2)

    assert budget.consume() is True
    assert budget.attempts == 1
    assert budget.consume() is True
    assert budget.attempts == 2


def test_budget_becomes_exhausted():
    budget = RecoveryBudget(max_attempts=1)

    assert budget.consume() is True
    assert budget.exhausted is True
    assert budget.consume() is False
    assert budget.attempts == 1


def test_exhausted_budget_does_not_increment():
    budget = RecoveryBudget(max_attempts=2)

    budget.consume()
    budget.consume()

    assert budget.consume() is False
    assert budget.attempts == 2


@pytest.mark.parametrize("max_attempts", [0, -1, -10])
def test_budget_rejects_non_positive_limits(max_attempts):
    with pytest.raises(ValueError, match="max_attempts"):
        RecoveryBudget(max_attempts)
