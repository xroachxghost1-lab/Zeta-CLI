from unittest.mock import MagicMock

import pytest

from zeta_cli.agent.loop import AgentLoop
from zeta_cli.state.runtime import AgentState


def state_store_for(state):
    store = MagicMock()
    store.load.return_value = state
    return store


def test_loop_runs_to_completion():
    engine = MagicMock()
    states = [
        AgentState(task_id="task-1", goal="edit code", phase="PLAN"),
        AgentState(task_id="task-1", goal="edit code", phase="EXECUTE"),
        AgentState(task_id="task-1", goal="edit code", phase="ASSESS"),
        AgentState(task_id="task-1", goal="edit code", phase="VERIFY"),
        AgentState(
            task_id="task-1",
            goal="edit code",
            phase="COMPLETE",
            completed=True,
            progress=100,
        ),
    ]

    engine.state_store.load.side_effect = states
    engine.execute.return_value = MagicMock(ok=True)
    engine.assess.return_value = MagicMock(ok=True)
    engine.verify.return_value = states[-1]
    engine.complete.return_value = states[-1]

    result = AgentLoop(engine).run(
        task_id="task-1",
        goal="edit code",
    )

    assert result.phase == "COMPLETE"
    engine.start.assert_called_once_with(
        task_id="task-1",
        goal="edit code",
    )
    engine.execute.assert_called_once()
    engine.assess.assert_called_once()
    engine.verify.assert_called_once()


def test_loop_retries_after_recovery():
    engine = MagicMock()
    states = [
        AgentState(task_id="task-1", goal="edit code", phase="PLAN"),
        AgentState(task_id="task-1", goal="edit code", phase="RECOVER"),
        AgentState(task_id="task-1", goal="edit code", phase="PLAN"),
        AgentState(
            task_id="task-1",
            goal="edit code",
            phase="COMPLETE",
            completed=True,
            progress=100,
        ),
    ]

    engine.state_store.load.side_effect = states
    engine.execute.side_effect = [
        None,
        MagicMock(ok=True),
    ]
    engine.retry.return_value = states[2]

    result = AgentLoop(engine).run(
        task_id="task-1",
        goal="edit code",
    )

    assert result.phase == "COMPLETE"
    engine.retry.assert_called_once()


def test_loop_stops_on_terminal_state():
    engine = MagicMock()
    state = AgentState(
        task_id="task-1",
        goal="edit code",
        phase="STOPPED",
    )
    engine.state_store.load.return_value = state

    result = AgentLoop(engine).run(
        task_id="task-1",
        goal="edit code",
    )

    assert result.phase == "STOPPED"
    engine.start.assert_called_once()
    engine.execute.assert_not_called()


def test_loop_rejects_invalid_step_budget():
    with pytest.raises(ValueError, match="greater than zero"):
        AgentLoop(MagicMock(), max_steps=0)


def test_loop_detects_missing_result():
    engine = MagicMock()
    states = [
        AgentState(task_id="task-1", goal="edit code", phase="PLAN"),
        AgentState(task_id="task-1", goal="edit code", phase="EXECUTE"),
    ]

    engine.state_store.load.side_effect = states
    engine.execute.return_value = None

    with pytest.raises(
        RuntimeError,
        match="without a tool result",
    ):
        AgentLoop(engine).run(
            task_id="task-1",
            goal="edit code",
        )


def test_loop_enforces_step_budget():
    engine = MagicMock()
    state = AgentState(
        task_id="task-1",
        goal="edit code",
        phase="PLAN",
    )

    engine.state_store.load.return_value = state
    engine.execute.return_value = MagicMock(ok=True)

    with pytest.raises(
        RuntimeError,
        match="exceeded maximum step count",
    ):
        AgentLoop(engine, max_steps=2).run(
            task_id="task-1",
            goal="edit code",
        )
