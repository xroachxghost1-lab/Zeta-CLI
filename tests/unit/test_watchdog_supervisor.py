from zeta_cli.watchdog.progress import ProgressRecord
from zeta_cli.watchdog.supervisor import Watchdog, WatchdogObservation


def test_watchdog_reports_progress_as_healthy():
    watchdog = Watchdog()

    previous = ProgressRecord()
    current = ProgressRecord(files_changed=1)

    result = watchdog.observe(previous, current)

    assert result == WatchdogObservation(
        progressed=True,
        stalled=False,
        repeated=False,
        healthy=True,
    )


def test_watchdog_detects_consecutive_stalls():
    watchdog = Watchdog(stall_threshold=2)

    progress = ProgressRecord()

    first = watchdog.observe(progress, progress)
    second = watchdog.observe(progress, progress)

    assert first.stalled is False
    assert second.stalled is True
    assert second.healthy is False


def test_watchdog_detects_repeated_observations():
    watchdog = Watchdog(repeat_threshold=2)

    progress = ProgressRecord(files_changed=1)

    first = watchdog.observe(ProgressRecord(), progress)
    second = watchdog.observe(progress, progress)
    third = watchdog.observe(progress, progress)

    assert first.repeated is False
    assert second.repeated is False
    assert third.repeated is True
    assert third.healthy is False


def test_watchdog_reset_clears_detector_state():
    watchdog = Watchdog(stall_threshold=2, repeat_threshold=2)

    progress = ProgressRecord()
    watchdog.observe(progress, progress)
    watchdog.observe(progress, progress)

    watchdog.reset()

    result = watchdog.observe(progress, progress)

    assert result.stalled is False
    assert result.repeated is False
    assert result.healthy is True


def test_watchdog_detects_repeated_tool_calls():
    watchdog = Watchdog(call_threshold=2)

    progress = ProgressRecord(files_changed=1)

    first = watchdog.observe(
        ProgressRecord(),
        progress,
        tool_call_fingerprint="abc",
    )
    second = watchdog.observe(
        progress,
        progress,
        tool_call_fingerprint="abc",
    )

    assert first.repeated_call is False
    assert second.repeated_call is True
    assert second.healthy is False


def test_watchdog_reset_clears_call_detector():
    watchdog = Watchdog(call_threshold=2)

    progress = ProgressRecord(files_changed=1)

    watchdog.observe(
        ProgressRecord(),
        progress,
        tool_call_fingerprint="abc",
    )
    watchdog.observe(
        progress,
        progress,
        tool_call_fingerprint="abc",
    )

    watchdog.reset()

    result = watchdog.observe(
        progress,
        progress,
        tool_call_fingerprint="abc",
    )

    assert result.repeated_call is False


def test_watchdog_detects_repeated_tool_results():
    watchdog = Watchdog(call_threshold=3)

    previous = ProgressRecord()
    current = ProgressRecord()

    assert watchdog.observe(
        previous,
        current,
        tool_result_fingerprint="result-a",
    ).repeated_result is False

    assert watchdog.observe(
        previous,
        current,
        tool_result_fingerprint="result-a",
    ).repeated_result is False

    observation = watchdog.observe(
        previous,
        current,
        tool_result_fingerprint="result-a",
    )

    assert observation.repeated_result is True
    assert observation.healthy is False


def test_watchdog_changed_tool_result_breaks_repetition():
    watchdog = Watchdog(call_threshold=3)

    previous = ProgressRecord()
    current = ProgressRecord()

    for fingerprint in ("result-a", "result-a"):
        observation = watchdog.observe(
            previous,
            current,
            tool_result_fingerprint=fingerprint,
        )
        assert observation.repeated_result is False

    observation = watchdog.observe(
        previous,
        current,
        tool_result_fingerprint="result-b",
    )

    assert observation.repeated_result is False


def test_watchdog_detects_repeated_reasoning():
    watchdog = Watchdog(call_threshold=3)

    previous = ProgressRecord()
    current = ProgressRecord()

    for fingerprint in ("reason-a", "reason-a"):
        observation = watchdog.observe(
            previous,
            current,
            reasoning_fingerprint=fingerprint,
        )
        assert observation.repeated_reasoning is False

    observation = watchdog.observe(
        previous,
        current,
        reasoning_fingerprint="reason-a",
    )

    assert observation.repeated_reasoning is True
    assert observation.healthy is False


def test_watchdog_changed_reasoning_breaks_repetition():
    watchdog = Watchdog(call_threshold=3)

    previous = ProgressRecord()
    current = ProgressRecord(tool_result_changed=True)

    for fingerprint in ("reason-a", "reason-a"):
        observation = watchdog.observe(
            previous,
            current,
            reasoning_fingerprint=fingerprint,
        )
        assert observation.repeated_reasoning is False

    observation = watchdog.observe(
        previous,
        current,
        reasoning_fingerprint="reason-b",
    )

    assert observation.repeated_reasoning is False
    assert observation.healthy is True
