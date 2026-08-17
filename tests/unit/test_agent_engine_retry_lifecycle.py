from unittest.mock import MagicMock

from zeta_cli.agent.engine import AgentEngine
from zeta_cli.api.models import CompletionResult, ToolCall
from zeta_cli.events import EventJournal
from zeta_cli.state import AgentState, StateStore
from zeta_cli.tools.results import ToolResult
from zeta_cli.verification.engine import VerificationResult


def test_retry_lifecycle_returns_to_plan_and_can_complete(tmp_path):
    planner = MagicMock()
    planner.plan.side_effect = [
        CompletionResult(
            content="retry plan",
            tool_calls=[ToolCall(id="call-1", name="read_file", arguments={"path": "README.md"})],
        ),
        CompletionResult(content="assessment"),
        CompletionResult(content="verification"),
    ]

    executor = MagicMock()
    executor.execute.return_value = ToolResult.from_value("README contents")

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
            phase="RECOVER",
            attempt=1,
            failed=True,
        )
    )

    engine = AgentEngine(
        planner=planner,
        executor=executor,
        state_store=state_store,
        journal=journal,
        verification_policy=policy,
    )

    retry_result = engine.retry()

    assert retry_result.phase == "PLAN"
    assert retry_result.attempt == 2
    assert retry_result.failed is False
    assert retry_result.completed is False

    execute_result = engine.execute()

    assert execute_result.ok is True
    assert execute_result.value == "README contents"

    assess_result = engine.assess(execute_result)

    assert assess_result.content == "assessment"

    verify_result = engine.verify(
        ToolResult.from_value("verification evidence")
    )

    assert verify_result.phase == "COMPLETE"
    assert verify_result.completed is True
    assert verify_result.failed is False

    planner.plan.assert_any_call("Read README.md")
    executor.execute.assert_called_once()

    events = journal.read()

    assert [event.data for event in events] == [
        {"from": "RECOVER", "to": "PLAN"},
        {"from": "PLAN", "to": "EXECUTE"},
        {"from": "EXECUTE", "to": "ASSESS"},
        {"from": "ASSESS", "to": "VERIFY"},
        {"from": "VERIFY", "to": "COMPLETE"},
    ]

    persisted = state_store.load()

    assert persisted.phase == "COMPLETE"
    assert persisted.attempt == 2
    assert persisted.completed is True
    assert persisted.failed is False
