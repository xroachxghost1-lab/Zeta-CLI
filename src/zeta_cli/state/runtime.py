from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from zeta_cli.constants import ALL_PHASES


@dataclass
class AgentState:
    """Persistent runtime state for a Zeta agent."""

    task_id: str | None = None
    goal: str | None = None
    phase: str = "BOOT"
    attempt: int = 0
    completed: bool = False
    failed: bool = False

    def __post_init__(self) -> None:
        if self.phase not in ALL_PHASES:
            raise ValueError(
                f"invalid phase: {self.phase!r}; "
                f"expected one of {ALL_PHASES!r}"
            )

        if self.attempt < 0:
            raise ValueError("attempt cannot be negative")


class StateStore:
    """JSON-backed persistence for AgentState."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def save(self, state: AgentState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        temporary = self.path.with_suffix(
            self.path.suffix + ".tmp"
        )

        temporary.write_text(
            json.dumps(
                asdict(state),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        temporary.replace(self.path)

    def load(self) -> AgentState:
        if not self.path.exists():
            return AgentState()

        data = json.loads(
            self.path.read_text(encoding="utf-8")
        )

        return AgentState(**data)
