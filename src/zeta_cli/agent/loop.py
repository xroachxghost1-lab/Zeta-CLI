from __future__ import annotations

from zeta_cli.agent.engine import AgentEngine
from zeta_cli.constants import TERMINAL_PHASES


class AgentLoop:
    """Drive an AgentEngine through its persisted lifecycle."""

    def __init__(self, engine: AgentEngine, *, max_steps: int = 50) -> None:
        if max_steps <= 0:
            raise ValueError("max_steps must be greater than zero")

        self.engine = engine
        self.max_steps = max_steps

    def run(self, *, task_id: str, goal: str):
        self.engine.start(task_id=task_id, goal=goal)

        result = None

        for _ in range(self.max_steps):
            state = self.engine.state_store.load()

            if state.phase in TERMINAL_PHASES:
                return state

            if state.phase == "PLAN":
                result = self.engine.execute()

            elif state.phase == "EXECUTE":
                if result is None:
                    raise RuntimeError(
                        "agent entered EXECUTE without a tool result"
                    )
                result = self.engine.assess(result)

            elif state.phase == "ASSESS":
                if result is None:
                    raise RuntimeError(
                        "agent entered ASSESS without an assessment result"
                    )
                result = self.engine.verify(result)

            elif state.phase == "VERIFY":
                result = self.engine.complete()

            elif state.phase == "RECOVER":
                result = self.engine.retry()

            else:
                raise RuntimeError(
                    f"unsupported agent phase: {state.phase!r}"
                )

        raise RuntimeError(
            f"agent exceeded maximum step count: {self.max_steps}"
        )
