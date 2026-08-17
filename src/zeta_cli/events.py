from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Event:
    """A durable record of something that happened in Zeta."""

    event_type: str
    task_id: str
    data: dict[str, Any] = field(default_factory=dict)


class EventJournal:
    """Append-only JSON Lines event journal."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def append(self, event: Event) -> None:
        """Append one event without rewriting existing events."""

        self.path.parent.mkdir(parents=True, exist_ok=True)

        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    asdict(event),
                    sort_keys=True,
                )
                + "\n"
            )

    def read(self) -> list[Event]:
        """Read all events in their original append order."""

        if not self.path.exists():
            return []

        events: list[Event] = []

        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()

                if not line:
                    continue

                events.append(
                    Event(**json.loads(line))
                )

        return events
