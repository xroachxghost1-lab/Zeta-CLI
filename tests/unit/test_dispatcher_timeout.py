from __future__ import annotations

import time

from zeta_cli.api.models import ToolCall
from zeta_cli.tools.dispatcher import ToolDispatcher
from zeta_cli.tools.registry import ToolRegistry


def make_call(name: str, arguments: dict) -> ToolCall:
    return ToolCall(
        id="call-1",
        name=name,
        arguments=arguments,
    )


def test_dispatcher_runs_tool_without_timeout():
    registry = ToolRegistry()
    registry.register(
        "echo",
        lambda arguments: arguments["value"],
    )

    dispatcher = ToolDispatcher(registry)

    result = dispatcher.dispatch(
        make_call("echo", {"value": "hello"})
    )

    assert result.ok is True
    assert result.value == "hello"


def test_dispatcher_timeout_is_disabled_by_default():
    registry = ToolRegistry()
    registry.register(
        "slow",
        lambda arguments: "finished",
    )

    dispatcher = ToolDispatcher(registry)

    result = dispatcher.dispatch(
        make_call("slow", {})
    )

    assert result.ok is True
    assert result.value == "finished"


def test_dispatcher_returns_timeout_failure():
    def slow_tool(arguments):
        time.sleep(0.2)
        return "finished"

    registry = ToolRegistry()
    registry.register("slow", slow_tool)

    dispatcher = ToolDispatcher(
        registry,
        timeout=0.05,
    )

    result = dispatcher.dispatch(
        make_call("slow", {})
    )

    assert result.ok is False
    assert result.error is not None
    assert "timed out" in result.error.lower()


def test_dispatcher_returns_success_when_tool_finishes_before_timeout():
    registry = ToolRegistry()
    registry.register(
        "fast",
        lambda arguments: "finished",
    )

    dispatcher = ToolDispatcher(
        registry,
        timeout=1.0,
    )

    result = dispatcher.dispatch(
        make_call("fast", {})
    )

    assert result.ok is True
    assert result.value == "finished"
