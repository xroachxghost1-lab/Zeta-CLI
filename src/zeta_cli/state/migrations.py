from __future__ import annotations

from typing import Any

CURRENT_SCHEMA_VERSION = 1


class StateCorruptionError(ValueError):
    """Raised when persisted state cannot be safely loaded."""


def migrate_state(data: dict[str, Any]) -> dict[str, Any]:
    """Migrate legacy state dictionaries to the current schema."""
    if not isinstance(data, dict):
        raise StateCorruptionError("state must be a JSON object")

    version = data.get("schema_version", 0)

    if not isinstance(version, int):
        raise StateCorruptionError("schema_version must be an integer")

    if version > CURRENT_SCHEMA_VERSION:
        raise StateCorruptionError(
            f"unsupported state schema version: {version}"
        )

    migrated = dict(data)

    # Version 0 was the original state format.
    if version == 0:
        migrated.setdefault("progress", 0)
        migrated["schema_version"] = 1

    return migrated
