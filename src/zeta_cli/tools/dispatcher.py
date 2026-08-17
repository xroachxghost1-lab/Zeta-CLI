from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError
from threading import Event
from time import sleep as default_sleep

from zeta_cli.api.retry import RetryPolicy

from zeta_cli.api.models import ToolCall
from zeta_cli.errors import ToolError
from zeta_cli.tools.results import ToolResult
from zeta_cli.tools.safety import ToolSafety


class ToolDispatcher:
    """Dispatch registered tools through safety and timeout policies."""

    def __init__(
        self,
        registry,
        safety: ToolSafety | None = None,
        timeout: float | None = None,
        retry_policy: RetryPolicy | None = None,
        sleep=default_sleep,
    ) -> None:
        self.registry = registry
        self.safety = safety
        self.timeout = timeout
        self.retry_policy = retry_policy
        self.sleep = sleep

        if timeout is not None and timeout <= 0:
            raise ValueError("timeout must be greater than zero")

    def dispatch(
        self,
        call: ToolCall,
        *,
        cancellation: Event | None = None,
    ) -> ToolResult:
        tool = self.registry.get(call.name)

        if tool is None:
            raise ToolError(f"unknown tool: {call.name!r}")

        if self.safety is not None and not self.safety.is_allowed(call.name):
            raise ToolError(f"tool is not allowed: {call.name!r}")

        if cancellation is not None and cancellation.is_set():
            return ToolResult(
                ok=False,
                error=f"tool {call.name!r} was cancelled before execution",
            )

        attempt = 0

        while True:
            try:
                if self.timeout is None:
                    return ToolResult.from_value(
                        tool(call.arguments)
                    )

                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(
                        tool,
                        call.arguments,
                    )

                    try:
                        return ToolResult.from_value(
                            future.result(timeout=self.timeout)
                        )
                    except TimeoutError:
                        future.cancel()
                        raise TimeoutError(
                            f"tool {call.name!r} timed out "
                            f"after {self.timeout}s"
                        )

            except Exception as error:
                if (
                    self.retry_policy is None
                    or not self.retry_policy.should_retry(attempt)
                ):
                    return ToolResult.from_exception(error)

                self.sleep(
                    self.retry_policy.delay_for(attempt)
                )
                attempt += 1
