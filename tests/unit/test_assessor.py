from zeta_cli.agent.assessor import Assessor
from zeta_cli.tools.results import ToolResult


def test_assessor_marks_successful_tool_result_as_passed():
    assessor = Assessor()

    assessment = assessor.assess(
        ToolResult.from_value("README contents")
    )

    assert assessment.passed is True
    assert assessment.value == "README contents"
    assert assessment.error is None


def test_assessor_marks_failed_tool_result_as_failed():
    assessor = Assessor()

    assessment = assessor.assess(
        ToolResult.from_exception(RuntimeError("read failed"))
    )

    assert assessment.passed is False
    assert assessment.value is None
    assert assessment.error == "read failed"


def test_assessor_rejects_non_tool_result():
    assessor = Assessor()

    try:
        assessor.assess("README contents")
    except TypeError as error:
        assert "ToolResult" in str(error)
    else:
        raise AssertionError("expected ToolResult requirement")
