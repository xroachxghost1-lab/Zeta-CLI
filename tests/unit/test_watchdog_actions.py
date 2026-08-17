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


@pytest.mark.parametrize(
    "field",
    [
        "repeated_call",
        "repeated_result",
        "repeated_reasoning",
    ],
)
def test_repeated_watchdog_signals_trigger_replan(field):
    observation_kwargs = {
        "progressed": False,
        "stalled": False,
        "repeated": False,
        "healthy": False,
    }
    observation_kwargs[field] = True

    watchdog_observation = WatchdogObservation(**observation_kwargs)

    assert choose_action(watchdog_observation) is WatchdogAction.REPLAN


@pytest.mark.parametrize(
    "field",
    [
        "repeated_call",
        "repeated_result",
        "repeated_reasoning",
    ],
)
def test_repeated_watchdog_signals_with_stall_stop(field):
    observation_kwargs = {
        "progressed": False,
        "stalled": True,
        "repeated": False,
        "healthy": False,
    }
    observation_kwargs[field] = True

    watchdog_observation = WatchdogObservation(**observation_kwargs)

    assert choose_action(watchdog_observation) is WatchdogAction.STOP


def test_no_workspace_progress_triggers_recover():
    watchdog_observation = WatchdogObservation(
        progressed=True,
        stalled=False,
        repeated=False,
        no_workspace_progress=True,
        healthy=False,
    )

    assert choose_action(watchdog_observation) is WatchdogAction.RECOVER


def test_no_workspace_progress_consumes_recovery_budget():
    budget = RecoveryBudget(max_attempts=2)

    watchdog_observation = WatchdogObservation(
        progressed=True,
        stalled=False,
        repeated=False,
        no_workspace_progress=True,
        healthy=False,
    )

    assert choose_action(
        watchdog_observation,
        budget=budget,
    ) is WatchdogAction.RECOVER

    assert budget.attempts == 1


def test_exhausted_workspace_recovery_budget_stops():
    budget = RecoveryBudget(max_attempts=1)

    watchdog_observation = WatchdogObservation(
        progressed=True,
        stalled=False,
        repeated=False,
        no_workspace_progress=True,
        healthy=False,
    )

    assert choose_action(
        watchdog_observation,
        budget=budget,
    ) is WatchdogAction.RECOVER

    assert choose_action(
        watchdog_observation,
        budget=budget,
    ) is WatchdogAction.STOP

    assert budget.attempts == 1


@pytest.mark.parametrize(
    "field",
    [
        "repeated_call",
        "repeated_result",
        "repeated_reasoning",
    ],
)
def test_workspace_stall_with_repeated_signal_stops(field):
    observation_kwargs = {
        "progressed": True,
        "stalled": False,
        "repeated": False,
        "no_workspace_progress": True,
        "healthy": False,
    }
    observation_kwargs[field] = True

    watchdog_observation = WatchdogObservation(**observation_kwargs)

    assert choose_action(watchdog_observation) is WatchdogAction.STOP


def test_workspace_stall_with_generic_repetition_stops():
    watchdog_observation = WatchdogObservation(
        progressed=True,
        stalled=False,
        repeated=True,
        no_workspace_progress=True,
        healthy=False,
    )

    assert choose_action(watchdog_observation) is WatchdogAction.STOP
