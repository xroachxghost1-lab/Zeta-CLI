from __future__ import annotations

import subprocess
from typing import Any

from zeta_cli.workspace.files import Workspace


def build_builtin_tools(workspace: Workspace) -> dict[str, Any]:
    """Build the tools the coding agent can execute."""

    def read_file(arguments: dict[str, Any]) -> dict[str, Any]:
        path = arguments["path"]

        return {
            "path": path,
            "content": workspace.read_file(path),
        }

    def write_file(arguments: dict[str, Any]) -> dict[str, Any]:
        path = arguments["path"]
        content = arguments["content"]

        written = workspace.write_file(path, content)

        return {
            "path": written,
            "bytes": len(content.encode("utf-8")),
        }

    def run_command(arguments: dict[str, Any]) -> dict[str, Any]:
        command = arguments["command"]

        if not isinstance(command, str) or not command.strip():
            raise ValueError("command must be a non-empty string")

        timeout = float(arguments.get("timeout", 60))

        completed = subprocess.run(
            command,
            cwd=workspace.root,
            shell=True,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )

        return {
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "ok": completed.returncode == 0,
        }

    return {
        "read_file": read_file,
        "write_file": write_file,
        "run_command": run_command,
    }


def builtin_schemas() -> list[dict[str, Any]]:
    return [
        {
            "name": "read_file",
            "description": "Read a UTF-8 file inside the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                },
                "required": ["path"],
                "additionalProperties": False,
            },
        },
        {
            "name": "write_file",
            "description": "Create or replace a UTF-8 file inside the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
                "additionalProperties": False,
            },
        },
        {
            "name": "run_command",
            "description": "Run a development command inside the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "timeout": {"type": "number"},
                },
                "required": ["command"],
                "additionalProperties": False,
            },
        },
    ]
