from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


ReasoningEffort = Literal["instant", "low", "medium", "high"]


@dataclass(frozen=True)
class Message:
    role: str
    content: str


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass
class CompletionResult:
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str | None = None
    model: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    raw: Any = None


@dataclass(frozen=True)
class ModelInfo:
    id: str
    owned_by: str | None = None
    context_window: int | None = None
    capabilities: tuple[str, ...] = ()


@dataclass(frozen=True)
class RateLimitInfo:
    limit: int | None = None
    remaining: int | None = None
    reset_seconds: float | None = None


@dataclass(frozen=True)
class RetryState:
    attempt: int
    max_attempts: int
    delay_seconds: float
    reason: str
