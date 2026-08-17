import pytest

from zeta_cli.watchdog.actions import WatchdogAction, choose_action
from zeta_cli.watchdog.supervisor import WatchdogObservation


@pytest.mark.parametrize(
    ("observation", "expected"),
    [
        (
            WatchdogObservation(
                progressed=True,
                stalled=False,
                repeated=False,
                healthy=True,
            ),
            WatchdogAction.CONTINUE,
        ),
        (
            WatchdogObservation(
                progressed=False,
                stalled=False,
                repeated=True,
                healthy=False,
            ),
            WatchdogAction.REPLAN,
        ),
        (
            WatchdogObservation(
                progressed=False,
                stalled=True,
                repeated=False,
                healthy=False,
            ),
            WatchdogAction.RECOVER,
        ),
        (
            WatchdogObservation(
                progressed=False,
                stalled=True,
                repeated=True,
                healthy=False,
            ),
            WatchdogAction.STOP,
        ),
    ],
)
def test_choose_action(observation, expected):
    assert choose_action(observation) is expected


def test_watchdog_action_values_are_stable():
    assert WatchdogAction.CONTINUE.value == "CONTINUE"
    assert WatchdogAction.REPLAN.value == "REPLAN"
    assert WatchdogAction.RECOVER.value == "RECOVER"
    assert WatchdogAction.STOP.value == "STOP"
