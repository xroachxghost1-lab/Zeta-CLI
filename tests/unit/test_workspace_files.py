from pathlib import Path

import pytest

from zeta_cli.workspace.files import Workspace


def test_workspace_writes_and_reads(tmp_path: Path):
    workspace = Workspace(tmp_path)

    workspace.write_file("src/example.py", "print('hello')")

    assert workspace.read_file("src/example.py") == "print('hello')"


def test_workspace_rejects_escape(tmp_path: Path):
    workspace = Workspace(tmp_path)

    with pytest.raises(ValueError):
        workspace.write_file("../escape.txt", "bad")


def test_workspace_rejects_missing_file(tmp_path: Path):
    workspace = Workspace(tmp_path)

    with pytest.raises(FileNotFoundError):
        workspace.read_file("missing.py")
