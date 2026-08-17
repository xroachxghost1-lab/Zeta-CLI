from __future__ import annotations

from zeta_cli.workspace.files import Workspace


class WorkspaceInspector:
    """Inspect files inside a workspace."""

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def list_files(self, *, max_files: int = 500) -> list[str]:
        files: list[str] = []

        for path in self.workspace.root.rglob("*"):
            if not path.is_file():
                continue

            if ".git" in path.parts or "__pycache__" in path.parts:
                continue

            files.append(str(path.relative_to(self.workspace.root)))

            if len(files) >= max_files:
                break

        return sorted(files)
