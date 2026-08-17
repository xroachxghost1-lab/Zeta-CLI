from unittest.mock import MagicMock

from zeta_cli.agent.engine import AgentEngine
from zeta_cli.api.models import CompletionResult
from zeta_cli.events import EventJournal
from zeta_cli.state import AgentState, StateStore
from zeta_cli.tools.results import ToolResult
from zeta_cli.verification.evidence import VerificationEvidence
from zeta_cli.verification.engine import VerificationResult


def make_engine(tmp_path, policy):
    planner = MagicMock()
    planner.plan.return_value = CompletionResult(
        content="verification",
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

    return engine, planner


def test_engine_verify_evaluates_policy(tmp_path):
    policy = MagicMock()
    policy.evaluate.return_value = VerificationResult(
        passed=True,
        reason="all evidence passed",
    )

    engine, planner = make_engine(tmp_path, policy)

    result = engine.verify(
        ToolResult.from_value("README contents")
    )

    assert result.phase == "COMPLETE"
    assert result.completed is True
    assert result.failed is False

    policy.evaluate.assert_called_once()

    evidence = policy.evaluate.call_args.args[0]
    assert len(evidence) == 1
    assert isinstance(evidence[0], VerificationEvidence)
    assert evidence[0].source == "agent"
    assert evidence[0].passed is True

    planner.plan.assert_not_called()
