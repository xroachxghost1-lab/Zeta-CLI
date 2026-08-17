from __future__ import annotations

from zeta_cli.agent.assessor import Assessor
from zeta_cli.agent.decision import Decision, DecisionEngine
from zeta_cli.agent.executor import Executor
from zeta_cli.agent.planner import Planner
from zeta_cli.events import EventJournal
from zeta_cli.state import AgentState, StateStore
from zeta_cli.state.transitions import transition_and_persist
from zeta_cli.verification.evidence import VerificationEvidence
from zeta_cli.verification.policies import VerificationPolicy


class AgentEngine:
    """Orchestrate the durable lifecycle of a Zeta agent."""

    def __init__(
        self,
        *,
        planner: Planner,
        state_store: StateStore,
        journal: EventJournal,
        executor: Executor | None = None,
        assessor: Assessor | None = None,
        decision_engine: DecisionEngine | None = None,
        verification_policy: VerificationPolicy | None = None,
    ) -> None:
        self.planner = planner
        self.executor = executor
        self.assessor = assessor or Assessor()
        self.decision_engine = decision_engine or DecisionEngine()
        self.state_store = state_store
        self.journal = journal
        self.verification_policy = verification_policy or VerificationPolicy()

    def start(self, *, task_id: str, goal: str):
        state = AgentState(
            task_id=task_id,
            goal=goal,
        )

        self.state_store.save(state)

        transition_and_persist(
            state,
            "PLAN",
            store=self.state_store,
            journal=self.journal,
            task_id=task_id,
        )

        return self.planner.plan(goal)

    def resume(self):
        state = self.state_store.load()

        if state.task_id is None:
            raise ValueError("cannot resume a task without a task_id")

        if state.goal is None:
            raise ValueError("cannot resume a task without a goal")

        return self.planner.plan(state.goal)

    def execute(self):
        if self.executor is None:
            raise ValueError("cannot execute without an executor")

        state = self.state_store.load()

        if state.task_id is None:
            raise ValueError("cannot execute a task without a task_id")

        if state.goal is None:
            raise ValueError("cannot execute a task without a goal")

        if state.phase != "PLAN":
            raise ValueError(
                f"cannot execute from phase {state.phase!r}"
            )

        planning_result = self.planner.plan(state.goal)

        if not planning_result.tool_calls:
            raise ValueError("no tool call in planning result")

        transition_and_persist(
            state,
            "EXECUTE",
            store=self.state_store,
            journal=self.journal,
            task_id=state.task_id,
        )

        return self.executor.execute(planning_result)


    def assess(self, result):
        state = self.state_store.load()

        if state.phase != "EXECUTE":
            raise ValueError(
                f"cannot assess from phase {state.phase!r}"
            )

        if state.task_id is None:
            raise ValueError("cannot assess a task without a task_id")

        if state.goal is None:
            raise ValueError("cannot assess a task without a goal")

        assessment = self.assessor.assess(result)

        transition_and_persist(
            state,
            "ASSESS",
            store=self.state_store,
            journal=self.journal,
            task_id=state.task_id,
        )

        return assessment

    def verify(self, result):
        state = self.state_store.load()

        if state.phase != "ASSESS":
            raise ValueError(
                f"cannot verify from phase {state.phase!r}"
            )

        if state.task_id is None:
            raise ValueError("cannot verify a task without a task_id")

        if state.goal is None:
            raise ValueError("cannot verify a task without a goal")

        transition_and_persist(
            state,
            "VERIFY",
            store=self.state_store,
            journal=self.journal,
            task_id=state.task_id,
        )

        evidence = VerificationEvidence(
            source="agent",
            description=str(result.value),
            passed=result.ok,
        )

        verification = self.verification_policy.evaluate([evidence])
        decision = self.decision_engine.decide(verification)

        if decision == Decision.RECOVER:
            transition_and_persist(
                state,
                "RECOVER",
                store=self.state_store,
                journal=self.journal,
                task_id=state.task_id,
            )

            state.failed = True
            state.completed = False
            self.state_store.save(state)

            return self.state_store.load()

        transition_and_persist(
            state,
            "COMPLETE",
            store=self.state_store,
            journal=self.journal,
            task_id=state.task_id,
        )

        state.completed = True
        state.failed = False
        self.state_store.save(state)

        return self.state_store.load()

    def complete(self):
        state = self.state_store.load()

        if state.phase != "VERIFY":
            raise ValueError(
                f"cannot complete from phase {state.phase!r}"
            )

        if state.task_id is None:
            raise ValueError("cannot complete a task without a task_id")

        transition_and_persist(
            state,
            "COMPLETE",
            store=self.state_store,
            journal=self.journal,
            task_id=state.task_id,
        )

        state.completed = True
        state.failed = False
        self.state_store.save(state)

        return self.state_store.load()

    def recover(self):
        state = self.state_store.load()

        if state.phase != "VERIFY":
            raise ValueError(
                f"cannot recover from phase {state.phase!r}"
            )

        if state.task_id is None:
            raise ValueError("cannot recover a task without a task_id")

        transition_and_persist(
            state,
            "RECOVER",
            store=self.state_store,
            journal=self.journal,
            task_id=state.task_id,
        )

        state.failed = True
        state.completed = False
        self.state_store.save(state)

        return self.state_store.load()


    def retry(self):
        state = self.state_store.load()

        if state.phase != "RECOVER":
            raise ValueError(
                f"cannot retry from phase {state.phase!r}"
            )

        if state.task_id is None:
            raise ValueError("cannot retry a task without a task_id")

        if state.goal is None:
            raise ValueError("cannot retry a task without a goal")

        transition_and_persist(
            state,
            "PLAN",
            store=self.state_store,
            journal=self.journal,
            task_id=state.task_id,
        )

        state.attempt += 1
        state.failed = False
        state.completed = False
        self.state_store.save(state)

        return self.state_store.load()
