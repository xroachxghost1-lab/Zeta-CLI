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
        result = self.engine.start(task_id=task_id, goal=goal)

        for _ in range(self.max_steps):
            state = self.engine.state_store.load()

            if state.phase in TERMINAL_PHASES:
                return state

            if state.phase == "BOOT":
                raise RuntimeError("agent remained in BOOT after start()")

            if state.phase == "PLAN":
                result = self.engine.execute(result)
                continue

            if state.phase == "EXECUTE":
                if result is None:
                    raise RuntimeError(
                        "agent entered EXECUTE without a tool result"
                    )
                result = self.engine.assess(result)
                continue

            if state.phase == "ASSESS":
                if result is None:
                    raise RuntimeError(
                        "agent entered ASSESS without an assessment result"
                    )
                result = self.engine.verify(result)
                continue

            if state.phase == "VERIFY":
                # verify() normally transitions directly to COMPLETE or
                # RECOVER. If a future policy leaves VERIFY pending,
                # complete() is the explicit fallback.
                result = self.engine.complete()
                continue

            if state.phase == "RECOVER":
                result = self.engine.retry()
                continue

            raise RuntimeError(
                f"unsupported agent phase: {state.phase!r}"
            )

        raise RuntimeError(
            f"agent exceeded maximum step count: {self.max_steps}"
        )
