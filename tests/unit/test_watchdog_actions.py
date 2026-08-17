import pytest

from zeta_cli.watchdog.actions import WatchdogAction, choose_action
from zeta_cli.watchdog.budget import RecoveryBudget
from zeta_cli.watchdog.supervisor import WatchdogObservation


def observation(*, stalled=False, repeated=False):
    return WatchdogObservation(
        progressed=not stalled and not repeated,
        stalled=stalled,
        repeated=repeated,
        healthy=not stalled and not repeated,
    )


@pytest.mark.parametrize(
    ("watchdog_observation", "expected"),
    [
        (observation(), WatchdogAction.CONTINUE),
        (observation(repeated=True), WatchdogAction.REPLAN),
        (observation(stalled=True), WatchdogAction.RECOVER),
        (
            observation(stalled=True, repeated=True),
            WatchdogAction.STOP,
        ),
    ],
)
def test_choose_action(watchdog_observation, expected):
    assert choose_action(watchdog_observation) is expected


def test_stalled_observation_consumes_recovery_budget():
    budget = RecoveryBudget(max_attempts=2)

    assert choose_action(observation(stalled=True), budget=budget) is WatchdogAction.RECOVER
    assert budget.attempts == 1


def test_exhausted_recovery_budget_stops():
    budget = RecoveryBudget(max_attempts=1)

    assert choose_action(observation(stalled=True), budget=budget) is WatchdogAction.RECOVER
    assert choose_action(observation(stalled=True), budget=budget) is WatchdogAction.STOP
    assert budget.attempts == 1
