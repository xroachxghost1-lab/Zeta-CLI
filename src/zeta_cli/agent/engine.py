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
from zeta_cli.watchdog.actions import WatchdogAction
from zeta_cli.watchdog.budget import RecoveryBudget
from zeta_cli.watchdog.coordinator import WatchdogCoordinator
from zeta_cli.watchdog.events import WatchdogEventRecorder
from zeta_cli.watchdog.snapshot import progress_record_from_state


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
        watchdog: WatchdogCoordinator | None = None,
    ) -> None:
        self.planner = planner
        self.executor = executor
        self.assessor = assessor or Assessor()
        self.decision_engine = decision_engine or DecisionEngine()
        self.state_store = state_store
        self.journal = journal
        self.verification_policy = verification_policy or VerificationPolicy()
        self.watchdog = watchdog or WatchdogCoordinator(
            recorder=WatchdogEventRecorder(journal),
            budget=RecoveryBudget(max_attempts=3),
        )

    def _observe_watchdog(self, previous_state: AgentState, current_state: AgentState):
        if current_state.task_id is None:
            return

        return self.watchdog.observe(
            task_id=current_state.task_id,
            previous=progress_record_from_state(previous_state),
            current=progress_record_from_state(current_state),
        )

    def start(self, *, task_id: str, goal: str):
        task_id = task_id.strip()
        goal = goal.strip()

        if not task_id:
            raise ValueError("task_id cannot be empty")

        if not goal:
            raise ValueError("goal cannot be empty")

        state = AgentState(
            task_id=task_id,
            goal=goal,
        )

        self.state_store.save(state)

        previous_state = AgentState(
            task_id=state.task_id,
            goal=state.goal,
            phase=state.phase,
            attempt=state.attempt,
            progress=state.progress,
            completed=state.completed,
            failed=state.failed,
        )

        transition_and_persist(
            state,
            "PLAN",
            store=self.state_store,
            journal=self.journal,
            task_id=task_id,
        )
        self._observe_watchdog(previous_state, state)

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

        previous_state = AgentState(
            task_id=state.task_id,
            goal=state.goal,
            phase=state.phase,
            attempt=state.attempt,
            progress=state.progress,
            completed=state.completed,
            failed=state.failed,
        )

        transition_and_persist(
            state,
            "EXECUTE",
            store=self.state_store,
            journal=self.journal,
            task_id=state.task_id,
        )
        _, watchdog_action = self._observe_watchdog(previous_state, state)

        if watchdog_action is WatchdogAction.RECOVER:
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
            return None

        if watchdog_action is WatchdogAction.STOP:
            transition_and_persist(
                state,
                "STOPPED",
                store=self.state_store,
                journal=self.journal,
                task_id=state.task_id,
            )
            self.state_store.save(state)
            return None

        if watchdog_action is WatchdogAction.REPLAN:
            planning_result = self.planner.plan(state.goal)

            if not planning_result.tool_calls:
                raise ValueError("no tool call in replanned result")

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

        previous_state = AgentState(
            task_id=state.task_id,
            goal=state.goal,
            phase=state.phase,
            attempt=state.attempt,
            progress=state.progress,
            completed=state.completed,
            failed=state.failed,
        )

        transition_and_persist(
            state,
            "ASSESS",
            store=self.state_store,
            journal=self.journal,
            task_id=state.task_id,
        )
        self._observe_watchdog(previous_state, state)

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

        previous_state = AgentState(
            task_id=state.task_id,
            goal=state.goal,
            phase=state.phase,
            attempt=state.attempt,
            progress=state.progress,
            completed=state.completed,
            failed=state.failed,
        )

        transition_and_persist(
            state,
            "VERIFY",
            store=self.state_store,
            journal=self.journal,
            task_id=state.task_id,
        )
        self._observe_watchdog(previous_state, state)

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

        previous_state = AgentState(
            task_id=state.task_id,
            goal=state.goal,
            phase=state.phase,
            attempt=state.attempt,
            progress=state.progress,
            completed=state.completed,
            failed=state.failed,
        )

        transition_and_persist(
            state,
            "RECOVER",
            store=self.state_store,
            journal=self.journal,
            task_id=state.task_id,
        )
        self._observe_watchdog(previous_state, state)

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

        previous_state = AgentState(
            task_id=state.task_id,
            goal=state.goal,
            phase=state.phase,
            attempt=state.attempt,
            progress=state.progress,
            completed=state.completed,
            failed=state.failed,
        )
        previous_progress = state.progress

        transition_and_persist(
            state,
            "PLAN",
            store=self.state_store,
            journal=self.journal,
            task_id=state.task_id,
        )
        self._observe_watchdog(previous_state, state)

        state.progress = previous_progress
        state.attempt += 1
        state.failed = False
        state.completed = False
        self.state_store.save(state)

        return self.state_store.load()
