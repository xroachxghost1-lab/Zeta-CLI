import pytest

from zeta_cli.watchdog.calls import CallHistoryDetector


def test_detector_ignores_missing_calls():
    detector = CallHistoryDetector(threshold=2)

    assert detector.observe(None) is False
    assert detector.observe(None) is False


def test_detector_detects_repeated_calls():
    detector = CallHistoryDetector(threshold=3)

    assert detector.observe("abc") is False
    assert detector.observe("abc") is False
    assert detector.observe("abc") is True


def test_detector_does_not_flag_different_calls():
    detector = CallHistoryDetector(threshold=3)

    assert detector.observe("abc") is False
    assert detector.observe("def") is False
    assert detector.observe("abc") is False


def test_detector_reset_clears_history():
    detector = CallHistoryDetector(threshold=2)

    detector.observe("abc")
    detector.observe("abc")
    detector.reset()

    assert detector.observe("abc") is False


@pytest.mark.parametrize("threshold", [0, -1])
def test_detector_rejects_invalid_threshold(threshold):
    with pytest.raises(ValueError, match="threshold"):
        CallHistoryDetector(threshold=threshold)
