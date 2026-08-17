from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolSchema:
    """Description of a tool and the arguments it accepts."""

    name: str
    description: str
    parameters: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("tool name cannot be empty")

        if self.parameters.get("type") != "object":
            raise ValueError("tool parameters must be an object schema")

    def to_definition(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolSchemaRegistry:
    """Registry of schemas exposed to the planner."""

    def __init__(self) -> None:
        self._schemas: dict[str, ToolSchema] = {}

    def register(self, schema: ToolSchema) -> None:
        if schema.name in self._schemas:
            raise ValueError(
                f"tool schema already registered: {schema.name!r}"
            )

        self._schemas[schema.name] = schema

    def get(self, name: str) -> ToolSchema | None:
        return self._schemas.get(name)

    def names(self) -> tuple[str, ...]:
        return tuple(self._schemas)

    def definitions(self) -> list[dict[str, Any]]:
        return [
            schema.to_definition()
            for schema in self._schemas.values()
        ]
