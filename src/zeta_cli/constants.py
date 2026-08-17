from __future__ import annotations

APP_NAME = "Zeta-CLI"
APP_VERSION = "0.1.0"

DEFAULT_MODEL = "mercury-2"
DEFAULT_EDIT_MODEL = "mercury-edit-2"
DEFAULT_REASONING_EFFORT = "medium"

SUPPORTED_REASONING_EFFORTS = (
    "instant",
    "low",
    "medium",
    "high",
)

DEFAULT_API_BASE = "https://api.inceptionlabs.ai/v1"

TERMINAL_PHASES = (
    "COMPLETE",
    "FAILED",
    "STOPPED",
)

ACTIVE_PHASES = (
    "BOOT",
    "PLAN",
    "EXECUTE",
    "ASSESS",
    "VERIFY",
    "RECOVER",
)

ALL_PHASES = ACTIVE_PHASES + TERMINAL_PHASES
