from unittest.mock import MagicMock

import pytest

from zeta_cli.agent.engine import AgentEngine
from zeta_cli.api.models import CompletionResult
from zeta_cli.events import EventJournal
from zeta_cli.state import AgentState, StateStore
from zeta_cli.tools.results import ToolResult
from zeta_cli.verification.engine import VerificationResult


def make_engine(tmp_path, policy):
    planner = MagicMock()
    planner.plan.return_value = CompletionResult(
        content="should not continue",
    )

    state_store = StateStore(tmp_path / "state.json")
    journal = EventJournal(tmp_path / "events.jsonl")

    state_store.save(
        AgentState(
            task_id="task-1",
            goal="Read README.md",
            phase="ASSESS",
        )
    )

    engine = AgentEngine(
        planner=planner,
        executor=MagicMock(),
        state_store=state_store,
        journal=journal,
        verification_policy=policy,
    )

    return engine, state_store, journal, planner


def test_engine_verify_failed_policy_routes_to_recover(tmp_path):
    policy = MagicMock()
    policy.evaluate.return_value = VerificationResult(
        passed=False,
        reason="verification evidence failed",
    )

    engine, state_store, journal, planner = make_engine(
        tmp_path,
        policy,
    )

    result = engine.verify(
        ToolResult.from_exception(
            RuntimeError("verification failed")
        )
    )

    assert result.phase == "RECOVER"
    assert result.failed is True
    assert result.completed is False

    planner.plan.assert_not_called()

    events = journal.read()
    assert [event.data for event in events] == [
        {
            "from": "ASSESS",
            "to": "VERIFY",
        },
        {
            "from": "VERIFY",
            "to": "RECOVER",
        },
    ]


def test_engine_verify_failed_policy_preserves_reason(tmp_path):
    policy = MagicMock()
    policy.evaluate.return_value = VerificationResult(
        passed=False,
        reason="pytest failed",
    )

    engine, state_store, journal, planner = make_engine(
        tmp_path,
        policy,
    )

    result = engine.verify(
        ToolResult.from_value("bad evidence")
    )

    assert result.phase == "RECOVER"
    assert result.failed is True
    assert result.completed is False


def test_engine_verify_failure_preserves_goal_progress(tmp_path):
    policy = MagicMock()
    policy.evaluate.return_value = VerificationResult(
        passed=False,
        reason="verification evidence failed",
    )

    engine, state_store, journal, planner = make_engine(
        tmp_path,
        policy,
    )

    state = state_store.load()
    state.progress = 75
    state_store.save(state)

    result = engine.verify(
        ToolResult.from_exception(
            RuntimeError("verification failed")
        )
    )

    assert result.phase == "RECOVER"
    assert result.failed is True
    assert result.progress == 75

    persisted = state_store.load()
    assert persisted.progress == 75
