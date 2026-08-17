from pathlib import Path

from zeta_cli.cli.main import create_parser


def test_run_command():
    parser = create_parser()
    args = parser.parse_args(["run", "build the agent"])

    assert args.command == "run"
    assert args.goal == "build the agent"


def test_status_command():
    parser = create_parser()
    args = parser.parse_args(["status"])

    assert args.command == "status"


def test_resume_command():
    parser = create_parser()
    args = parser.parse_args(["resume", "task-123"])

    assert args.command == "resume"
    assert args.task_id == "task-123"


def test_parser_has_expected_commands():
    parser = create_parser()
    commands = parser._subparsers._group_actions[0].choices

    assert {"run", "status", "resume"} <= set(commands)


def test_build_engine(monkeypatch, tmp_path):
    from zeta_cli.cli.main import build_engine
    from zeta_cli.config import Settings

    settings = Settings(
        api_key="test-key",
        workspace=tmp_path,
        state_dir=Path("data"),
    )

    class FakeProvider:
        pass

    engine = build_engine(settings)

    assert engine.state_store.path == tmp_path / "data" / "state.json"
    assert engine.journal.path == tmp_path / "data" / "events.jsonl"
    assert engine.executor is not None
