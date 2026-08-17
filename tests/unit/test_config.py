import os

from zeta_cli.config import Settings


def test_settings_defaults():
    settings = Settings()

    assert settings.model == "mercury-2"
    assert settings.edit_model == "mercury-edit-2"
    assert settings.reasoning_effort == "medium"


def test_settings_reads_inception_api_key(monkeypatch):
    monkeypatch.setenv("INCEPTION_API_KEY", "test-key")

    settings = Settings()

    assert settings.api_key == "test-key"


def test_settings_does_not_require_api_key_for_construction(monkeypatch):
    monkeypatch.delenv("INCEPTION_API_KEY", raising=False)

    settings = Settings()

    assert settings.api_key is None
