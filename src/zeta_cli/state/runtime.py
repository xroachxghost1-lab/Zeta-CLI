from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from zeta_cli.constants import ALL_PHASES
from zeta_cli.state.migrations import (
    CURRENT_SCHEMA_VERSION,
    StateCorruptionError,
    migrate_state,
)


@dataclass
class AgentState:
    """Persistent runtime state for a Zeta agent."""

    schema_version: int = CURRENT_SCHEMA_VERSION
    task_id: str | None = None
    goal: str | None = None
    phase: str = "BOOT"
    attempt: int = 0
    progress: int = 0
    completed: bool = False
    failed: bool = False
    strategy: str = "default"

    def __post_init__(self) -> None:
        if self.phase not in ALL_PHASES:
            raise ValueError(
                f"invalid phase: {self.phase!r}; "
                f"expected one of {ALL_PHASES!r}"
            )

        if self.attempt < 0:
            raise ValueError("attempt cannot be negative")

        if self.progress < 0 or self.progress > 100:
            raise ValueError("progress must be between 0 and 100")

        if self.schema_version != CURRENT_SCHEMA_VERSION:
            raise ValueError(
                f"unsupported state schema version: "
                f"{self.schema_version}"
            )


class StateStore:
    """Atomic JSON-backed persistence for AgentState."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._state: AgentState | None = None

    def save(self, state: AgentState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        temporary = self.path.with_suffix(
            self.path.suffix + ".tmp"
        )

        payload = json.dumps(
            asdict(state),
            indent=2,
            sort_keys=True,
        ) + "\n"

        try:
            with temporary.open("w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())

            temporary.replace(self.path)

            # Ensure the directory entry is durable on POSIX systems.
            try:
                directory_fd = os.open(
                    self.path.parent,
                    os.O_RDONLY,
                )
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            except OSError:
                # Some platforms/filesystems do not support directory fsync.
                pass

        except OSError:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            raise

        self._state = state

    def load(self) -> AgentState:
        if self._state is not None:
            return self._state

        if not self.path.exists():
            self._state = AgentState()
            return self._state

        try:
            raw = self.path.read_text(encoding="utf-8")
            data = json.loads(raw)
            migrated = migrate_state(data)
            self._state = AgentState(**migrated)
        except json.JSONDecodeError as exc:
            raise StateCorruptionError(
                f"invalid JSON in state file: {self.path}"
            ) from exc
        except (TypeError, KeyError) as exc:
            raise StateCorruptionError(
                f"invalid state data in: {self.path}"
            ) from exc

        return self._state
