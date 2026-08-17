from zeta_cli.constants import (
    ALL_PHASES,
    APP_NAME,
    APP_VERSION,
    DEFAULT_EDIT_MODEL,
    DEFAULT_MODEL,
    DEFAULT_REASONING_EFFORT,
    SUPPORTED_REASONING_EFFORTS,
)


def test_application_identity():
    assert APP_NAME == "Zeta-CLI"
    assert APP_VERSION == "0.1.0"


def test_default_models():
    assert DEFAULT_MODEL == "mercury-2"
    assert DEFAULT_EDIT_MODEL == "mercury-edit-2"


def test_reasoning_effort_values():
    assert DEFAULT_REASONING_EFFORT == "medium"
    assert SUPPORTED_REASONING_EFFORTS == (
        "instant",
        "low",
        "medium",
        "high",
    )


def test_all_phases_are_present():
    assert "BOOT" in ALL_PHASES
    assert "PLAN" in ALL_PHASES
    assert "EXECUTE" in ALL_PHASES
    assert "VERIFY" in ALL_PHASES
    assert "RECOVER" in ALL_PHASES
    assert "COMPLETE" in ALL_PHASES
