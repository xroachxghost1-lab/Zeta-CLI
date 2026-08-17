from pathlib import Path

from zeta_cli.tools.builtin import build_builtin_tools
from zeta_cli.workspace.files import Workspace


def test_read_file(tmp_path: Path):
    workspace = Workspace(tmp_path)
    workspace.write_file("hello.py", "print('hello')")

    tools = build_builtin_tools(workspace)

    result = tools["read_file"]({"path": "hello.py"})

    assert result["content"] == "print('hello')"


def test_write_file(tmp_path: Path):
    workspace = Workspace(tmp_path)
    tools = build_builtin_tools(workspace)

    result = tools["write_file"](
        {
            "path": "hello.py",
            "content": "print('hello')",
        }
    )

    assert result["path"] == "hello.py"
    assert workspace.read_file("hello.py") == "print('hello')"


def test_run_command(tmp_path: Path):
    workspace = Workspace(tmp_path)
    tools = build_builtin_tools(workspace)

    result = tools["run_command"](
        {
            "command": "python -c \"print('hello')\"",
        }
    )

    assert result["returncode"] == 0
    assert result["stdout"].strip() == "hello"
    assert result["ok"] is True
