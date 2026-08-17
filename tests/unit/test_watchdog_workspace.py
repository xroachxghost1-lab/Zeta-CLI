from zeta_cli.watchdog.progress import ProgressRecord
from zeta_cli.watchdog.workspace import WorkspaceProgressDetector


def test_workspace_detector_requires_threshold():
    detector = WorkspaceProgressDetector(threshold=2)

    progress = ProgressRecord()

    assert detector.observe(progress, progress) is False
    assert detector.observe(progress, progress) is True


def test_workspace_detector_resets_on_file_change():
    detector = WorkspaceProgressDetector(threshold=2)

    previous = ProgressRecord()
    changed = ProgressRecord(files_changed=1)

    detector.observe(previous, previous)

    assert detector.observe(previous, changed) is False
    assert detector.observe(changed, changed) is False


def test_workspace_detector_tracks_created_files():
    detector = WorkspaceProgressDetector(threshold=2)

    previous = ProgressRecord()
    created = ProgressRecord(files_created=1)

    detector.observe(previous, previous)

    assert detector.observe(previous, created) is False
    assert detector.observe(created, created) is False


def test_workspace_detector_tracks_deleted_files():
    detector = WorkspaceProgressDetector(threshold=2)

    previous = ProgressRecord()
    deleted = ProgressRecord(files_deleted=1)

    detector.observe(previous, previous)

    assert detector.observe(previous, deleted) is False
    assert detector.observe(deleted, deleted) is False


def test_workspace_detector_rejects_invalid_threshold():
    try:
        WorkspaceProgressDetector(threshold=0)
    except ValueError as exc:
        assert str(exc) == "threshold must be positive"
    else:
        raise AssertionError("expected ValueError")
