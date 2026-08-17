from pathlib import Path

from zeta_cli.state import (
    AgentState,
    StateStore,
)
from zeta_cli.constants import ALL_PHASES


def test_initial_state():
    state = AgentState()

    assert state.phase == "BOOT"
    assert state.task_id is None
    assert state.goal is None
    assert state.attempt == 0
    assert state.completed is False
    assert state.failed is False


def test_state_can_track_task():
    state = AgentState()

    state.task_id = "task-001"
    state.goal = "Build the agent"
    state.phase = "PLAN"

    assert state.task_id == "task-001"
    assert state.goal == "Build the agent"
    assert state.phase == "PLAN"


def test_state_phase_must_be_valid():
    state = AgentState()

    for phase in ALL_PHASES:
        state.phase = phase
        assert state.phase == phase


def test_state_store_round_trip(tmp_path: Path):
    store = StateStore(tmp_path / "state.json")

    state = AgentState(
        task_id="task-123",
        goal="Implement persistence",
        phase="EXECUTE",
        attempt=2,
    )

    store.save(state)

    restored = store.load()

    assert restored.task_id == "task-123"
    assert restored.goal == "Implement persistence"
    assert restored.phase == "EXECUTE"
    assert restored.attempt == 2


def test_missing_state_returns_initial_state(tmp_path: Path):
    store = StateStore(tmp_path / "missing.json")

    state = store.load()

    assert state.phase == "BOOT"
    assert state.task_id is None


def test_state_store_creates_parent_directory(tmp_path: Path):
    path = tmp_path / "nested" / "runtime" / "state.json"

    store = StateStore(path)
    store.save(AgentState(task_id="abc"))

    assert path.exists()


def test_initial_state_has_zero_goal_progress():
    state = AgentState()

    assert state.progress == 0


def test_state_can_track_goal_progress():
    state = AgentState(
        task_id="task-001",
        goal="Build the agent",
        progress=50,
    )

    assert state.progress == 50


def test_state_rejects_invalid_goal_progress():
    import pytest

    with pytest.raises(ValueError, match="progress"):
        AgentState(progress=-1)

    with pytest.raises(ValueError, match="progress"):
        AgentState(progress=101)


def test_state_store_persists_goal_progress(tmp_path: Path):
    store = StateStore(tmp_path / "state.json")

    state = AgentState(
        task_id="task-123",
        goal="Implement persistence",
        phase="EXECUTE",
        progress=75,
    )

    store.save(state)

    restored = store.load()

    assert restored.progress == 75


def test_state_store_loads_legacy_state_without_progress(tmp_path: Path):
    path = tmp_path / "legacy.json"
    path.write_text(
        """{
  "attempt": 2,
  "completed": false,
  "failed": false,
  "goal": "Build the agent",
  "phase": "PLAN",
  "task_id": "task-123"
}
""",
        encoding="utf-8",
    )

    store = StateStore(path)

    restored = store.load()

    assert restored.task_id == "task-123"
    assert restored.goal == "Build the agent"
    assert restored.phase == "PLAN"
    assert restored.attempt == 2
    assert restored.progress == 0
