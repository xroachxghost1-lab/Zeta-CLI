from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProgressRecord:
    """Structured progress observed during one agent iteration."""

    files_changed: int = 0
    files_created: int = 0
    files_deleted: int = 0
    tests_changed: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    task_state_changed: bool = False
    tool_result_changed: bool = False
    verification_state_changed: bool = False
    strategy_changed: bool = False
    objective_distance: int | float = 0

    def has_progress(self) -> bool:
        """Return whether this record represents meaningful progress."""
        return any(
            (
                self.files_changed,
                self.files_created,
                self.files_deleted,
                self.tests_changed,
                self.tests_passed,
                self.tests_failed,
                self.task_state_changed,
                self.tool_result_changed,
                self.verification_state_changed,
                self.strategy_changed,
                self.objective_distance != 0,
            )
        )


def progress_changed(
    previous: ProgressRecord,
    current: ProgressRecord,
) -> bool:
    """Return whether the current iteration differs from the previous one."""
    return previous != current


@dataclass(frozen=True)
class ProgressDelta:
    """Changes observed between two progress records."""

    files_changed: int = 0
    files_created: int = 0
    files_deleted: int = 0
    tests_changed: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    task_state_changed: bool = False
    tool_result_changed: bool = False
    verification_state_changed: bool = False
    strategy_changed: bool = False
    objective_distance: int | float = 0

    def has_progress(self) -> bool:
        return any(
            (
                self.files_changed,
                self.files_created,
                self.files_deleted,
                self.tests_changed,
                self.tests_passed,
                self.tests_failed,
                self.task_state_changed,
                self.tool_result_changed,
                self.verification_state_changed,
                self.strategy_changed,
                self.objective_distance != 0,
            )
        )


def progress_delta(
    previous: ProgressRecord,
    current: ProgressRecord,
) -> ProgressDelta:
    """Return the dimension-by-dimension change between two records."""
    return ProgressDelta(
        files_changed=current.files_changed - previous.files_changed,
        files_created=current.files_created - previous.files_created,
        files_deleted=current.files_deleted - previous.files_deleted,
        tests_changed=current.tests_changed - previous.tests_changed,
        tests_passed=current.tests_passed - previous.tests_passed,
        tests_failed=current.tests_failed - previous.tests_failed,
        task_state_changed=(
            current.task_state_changed != previous.task_state_changed
        ),
        tool_result_changed=(
            current.tool_result_changed != previous.tool_result_changed
        ),
        verification_state_changed=(
            current.verification_state_changed
            != previous.verification_state_changed
        ),
        strategy_changed=current.strategy_changed != previous.strategy_changed,
        objective_distance=(
            current.objective_distance - previous.objective_distance
        ),
    )
