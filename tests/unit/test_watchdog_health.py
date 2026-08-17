import pytest

from zeta_cli.watchdog.health import StallDetector


def test_stall_detector_requires_positive_threshold():
    with pytest.raises(ValueError, match="threshold"):
        StallDetector(threshold=0)


def test_stall_detector_does_not_trigger_before_threshold():
    detector = StallDetector(threshold=3)

    assert detector.observe(False) is False
    assert detector.consecutive_stalls == 1

    assert detector.observe(False) is False
    assert detector.consecutive_stalls == 2


def test_stall_detector_triggers_at_threshold():
    detector = StallDetector(threshold=3)

    assert detector.observe(False) is False
    assert detector.observe(False) is False
    assert detector.observe(False) is True
    assert detector.consecutive_stalls == 3


def test_progress_resets_stall_count():
    detector = StallDetector(threshold=3)

    detector.observe(False)
    detector.observe(False)

    assert detector.observe(True) is False
    assert detector.consecutive_stalls == 0


def test_stall_detection_can_trigger_again_after_reset():
    detector = StallDetector(threshold=2)

    assert detector.observe(False) is False
    assert detector.observe(False) is True

    detector.reset()

    assert detector.consecutive_stalls == 0
    assert detector.observe(False) is False
    assert detector.observe(False) is True
