import pytest

from zeta_cli.watchdog.progress import ProgressDelta, ProgressRecord, progress_changed, progress_delta


def test_progress_record_defaults_to_no_progress():
    progress = ProgressRecord()

    assert progress.files_changed == 0
    assert progress.tests_passed == 0
    assert progress.task_state_changed is False
    assert progress.objective_distance == 0
    assert progress.has_progress() is False


@pytest.mark.parametrize(
    "field",
    [
        "files_changed",
        "files_created",
        "files_deleted",
        "tests_changed",
        "tests_passed",
        "tests_failed",
        "task_state_changed",
        "tool_result_changed",
        "verification_state_changed",
        "strategy_changed",
    ],
)
def test_progress_record_detects_structural_progress(field):
    value = True if field in {
        "task_state_changed",
        "tool_result_changed",
        "verification_state_changed",
        "strategy_changed",
    } else 1

    progress = ProgressRecord(**{field: value})

    assert progress.has_progress() is True


def test_progress_record_detects_objective_distance():
    progress = ProgressRecord(objective_distance=1)

    assert progress.has_progress() is True


def test_progress_record_accepts_negative_objective_distance():
    progress = ProgressRecord(objective_distance=-2)

    assert progress.has_progress() is True


def test_progress_record_is_immutable():
    progress = ProgressRecord(files_changed=1)

    with pytest.raises(AttributeError):
        progress.files_changed = 2


def test_progress_changed_detects_identical_records():
    previous = ProgressRecord(files_changed=1, tests_passed=2)
    current = ProgressRecord(files_changed=1, tests_passed=2)

    assert progress_changed(previous, current) is False


def test_progress_changed_detects_new_progress():
    previous = ProgressRecord(files_changed=1)
    current = ProgressRecord(files_changed=2)

    assert progress_changed(previous, current) is True


def test_progress_delta_reports_numeric_changes():
    previous = ProgressRecord(
        files_changed=1,
        tests_passed=2,
        objective_distance=5,
    )
    current = ProgressRecord(
        files_changed=3,
        tests_passed=5,
        objective_distance=2,
    )

    delta = progress_delta(previous, current)

    assert delta.files_changed == 2
    assert delta.tests_passed == 3
    assert delta.objective_distance == -3
    assert delta.has_progress() is True


def test_progress_delta_reports_boolean_changes():
    previous = ProgressRecord()
    current = ProgressRecord(
        task_state_changed=True,
        verification_state_changed=True,
    )

    delta = progress_delta(previous, current)

    assert delta.task_state_changed is True
    assert delta.verification_state_changed is True
    assert delta.has_progress() is True


def test_progress_delta_is_zero_for_identical_records():
    progress = ProgressRecord(
        files_changed=2,
        tests_passed=4,
        strategy_changed=True,
    )

    delta = progress_delta(progress, progress)

    assert delta == ProgressDelta()
    assert delta.has_progress() is False
