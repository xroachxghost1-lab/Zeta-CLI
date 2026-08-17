from __future__ import annotations

from pathlib import Path


class Workspace:
    """Sandboxed filesystem access rooted at the configured workspace."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def resolve(self, path: str) -> Path:
        candidate = (self.root / path).resolve()

        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ValueError(f"path escapes workspace: {path!r}") from exc

        return candidate

    def read_file(self, path: str, *, max_bytes: int = 1_000_000) -> str:
        target = self.resolve(path)

        if not target.is_file():
            raise FileNotFoundError(path)

        data = target.read_bytes()

        if len(data) > max_bytes:
            raise ValueError(
                f"file exceeds maximum size of {max_bytes} bytes"
            )

        return data.decode("utf-8")

    def write_file(self, path: str, content: str) -> str:
        target = self.resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

        return str(target.relative_to(self.root))
