from __future__ import annotations


class ToolSafety:
    """Allowlist/denylist policy for tool execution."""

    def __init__(
        self,
        allowed: set[str] | None = None,
        *,
        denied: set[str] | None = None,
    ) -> None:
        self._allowed = set(allowed or ())
        self._denied = set(denied or ())

    def is_allowed(self, name: str) -> bool:
        return name in self._allowed and name not in self._denied

    def require_allowed(self, name: str) -> None:
        if not self.is_allowed(name):
            raise ValueError(f"tool is not allowed: {name!r}")
