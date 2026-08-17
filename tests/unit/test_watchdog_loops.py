import pytest

from zeta_cli.watchdog.loops import RepeatDetector


def test_repeat_detector_requires_positive_threshold():
    with pytest.raises(ValueError, match="threshold"):
        RepeatDetector(threshold=0)


def test_first_observation_is_not_a_repeat():
    detector = RepeatDetector(threshold=2)

    assert detector.observe("tool-a") is False
    assert detector.consecutive_repeats == 0


def test_different_observation_resets_repeat_count():
    detector = RepeatDetector(threshold=2)

    detector.observe("tool-a")

    assert detector.observe("tool-b") is False
    assert detector.consecutive_repeats == 0


def test_repeat_detector_triggers_at_threshold():
    detector = RepeatDetector(threshold=2)

    assert detector.observe("same") is False
    assert detector.observe("same") is False
    assert detector.consecutive_repeats == 1

    assert detector.observe("same") is True
    assert detector.consecutive_repeats == 2


def test_repeat_detector_can_reset():
    detector = RepeatDetector(threshold=2)

    detector.observe("same")
    detector.observe("same")

    detector.reset()

    assert detector.consecutive_repeats == 0
    assert detector.observe("same") is False
