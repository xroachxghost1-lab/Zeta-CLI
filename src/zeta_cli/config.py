from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Runtime configuration for Zeta-CLI."""

    model: str = "mercury-2"
    edit_model: str = "mercury-edit-2"
    reasoning_effort: str = "medium"
    api_key: str | None = None
    api_base: str = "https://api.inceptionlabs.ai/v1"
    workspace: Path = Path.cwd()
    state_dir: Path = Path("data")

    def __post_init__(self) -> None:
        if self.api_key is None:
            object.__setattr__(
                self,
                "api_key",
                os.environ.get("INCEPTION_API_KEY"),
            )

        if self.reasoning_effort not in {
            "instant",
            "low",
            "medium",
            "high",
        }:
            raise ValueError(
                "reasoning_effort must be one of: "
                "instant, low, medium, high"
            )

    @classmethod
    def from_environment(cls) -> "Settings":
        """Build settings from supported environment variables."""

        return cls(
            model=os.environ.get("ZETA_MODEL", "mercury-2"),
            edit_model=os.environ.get(
                "ZETA_EDIT_MODEL",
                "mercury-edit-2",
            ),
            reasoning_effort=os.environ.get(
                "ZETA_REASONING_EFFORT",
                "medium",
            ),
            api_key=os.environ.get("INCEPTION_API_KEY"),
            api_base=os.environ.get(
                "INCEPTION_API_BASE",
                "https://api.inceptionlabs.ai/v1",
            ),
        )
