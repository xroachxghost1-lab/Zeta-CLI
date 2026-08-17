import pytest

from zeta_cli.watchdog.progress import ProgressRecord, progress_changed


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
