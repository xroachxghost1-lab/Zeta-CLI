from zeta_cli.logging import redact


def test_redacts_inception_api_key():
    text = "INCEPTION_API_KEY=super-secret-key"

    result = redact(text)

    assert "super-secret-key" not in result
    assert "[REDACTED]" in result


def test_redacts_bearer_token():
    text = "Authorization: Bearer abc123secret"

    result = redact(text)

    assert "abc123secret" not in result
    assert "[REDACTED]" in result


def test_preserves_normal_text():
    text = "tool completed successfully"

    assert redact(text) == text
