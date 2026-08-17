from unittest.mock import MagicMock

from zeta_cli.agent.engine import AgentEngine
from zeta_cli.api.models import CompletionResult
from zeta_cli.events import EventJournal
from zeta_cli.state import AgentState, StateStore
from zeta_cli.tools.results import ToolResult
from zeta_cli.verification.engine import VerificationResult


def test_engine_verify_then_complete(tmp_path):
    planner = MagicMock()
    planner.plan.return_value = CompletionResult(
        content="Verification passed.",
    )

    policy = MagicMock()
    policy.evaluate.return_value = VerificationResult(
        passed=True,
        reason="all verification evidence passed",
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
        dispatcher=MagicMock(),
        state_store=state_store,
        journal=journal,
        verification_policy=policy,
    )

    result = engine.verify(
        ToolResult.from_value("README contents")
    )

    assert result.phase == "COMPLETE"
    assert result.completed is True
    assert result.failed is False

    persisted = state_store.load()
    assert persisted.phase == "COMPLETE"
    assert persisted.completed is True
    assert persisted.failed is False

    events = journal.read()
    assert [event.data for event in events] == [
        {
            "from": "ASSESS",
            "to": "VERIFY",
        },
        {
            "from": "VERIFY",
            "to": "COMPLETE",
        },
    ]
