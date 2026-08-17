from zeta_cli.api.models import (
    CompletionResult,
    Message,
    ModelInfo,
    RateLimitInfo,
    RetryState,
    ToolCall,
)


def test_message():
    message = Message(role="user", content="hello")

    assert message.role == "user"
    assert message.content == "hello"


def test_tool_call_defaults_arguments():
    call = ToolCall(id="call-1", name="shell")

    assert call.id == "call-1"
    assert call.name == "shell"
    assert call.arguments == {}


def test_completion_result_defaults():
    result = CompletionResult()

    assert result.content == ""
    assert result.tool_calls == []
    assert result.finish_reason is None
    assert result.usage == {}


def test_model_info():
    model = ModelInfo(
        id="mercury-2",
        owned_by="inception",
        context_window=128_000,
        capabilities=("chat", "streaming", "tools"),
    )

    assert model.id == "mercury-2"
    assert model.context_window == 128_000
    assert "tools" in model.capabilities


def test_rate_limit_info():
    info = RateLimitInfo(
        limit=100,
        remaining=95,
        reset_seconds=10.5,
    )

    assert info.limit == 100
    assert info.remaining == 95
    assert info.reset_seconds == 10.5


def test_retry_state():
    state = RetryState(
        attempt=2,
        max_attempts=5,
        delay_seconds=1.5,
        reason="rate_limit",
    )

    assert state.attempt == 2
    assert state.max_attempts == 5
    assert state.reason == "rate_limit"
