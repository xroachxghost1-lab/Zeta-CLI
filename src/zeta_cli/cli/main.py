from __future__ import annotations

import argparse
import uuid
from pathlib import Path

from zeta_cli.agent.engine import AgentEngine
from zeta_cli.agent.executor import Executor
from zeta_cli.agent.loop import AgentLoop
from zeta_cli.agent.planner import Planner
from zeta_cli.api.client import APIClient
from zeta_cli.config import Settings
from zeta_cli.events import EventJournal
from zeta_cli.state import StateStore
from zeta_cli.tools.builtin import build_builtin_tools, builtin_schemas
from zeta_cli.tools.dispatcher import ToolDispatcher
from zeta_cli.tools.registry import ToolRegistry
from zeta_cli.workspace.files import Workspace


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="zeta",
        description="Persistent autonomous coding agent for Inception Mercury.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    run_parser = subparsers.add_parser(
        "run",
        help="start an agent task",
    )
    run_parser.add_argument("goal")

    status_parser = subparsers.add_parser(
        "status",
        help="show current agent state",
    )
    status_parser.add_argument(
        "--state",
        type=Path,
        default=None,
        help="path to the state file",
    )

    resume_parser = subparsers.add_parser(
        "resume",
        help="resume a persisted task",
    )
    resume_parser.add_argument(
        "task_id",
    )

    return parser


def build_engine(settings: Settings) -> AgentEngine:
    workspace = Workspace(settings.workspace)

    tools = build_builtin_tools(workspace)

    registry = ToolRegistry()
    for name, tool in tools.items():
        registry.register(name, tool)

    dispatcher = ToolDispatcher(registry)
    executor = Executor(dispatcher)

    api = APIClient(settings)
    planner = Planner(api, settings)

    state_store = StateStore(
        settings.workspace / settings.state_dir / "state.json"
    )
    journal = EventJournal(
        settings.workspace / settings.state_dir / "events.jsonl"
    )

    return AgentEngine(
        planner=planner,
        executor=executor,
        state_store=state_store,
        journal=journal,
        tool_schemas=builtin_schemas(),
    )


def run_task(settings: Settings, goal: str) -> int:
    engine = build_engine(settings)

    task_id = str(uuid.uuid4())
    loop = AgentLoop(engine)

    state = loop.run(
        task_id=task_id,
        goal=goal,
    )

    result = loop.last_result
    if result is not None:
        value = getattr(result, "value", None)
        if value is not None:
            print(value)

    print(
        f"task={state.task_id} "
        f"phase={state.phase} "
        f"progress={state.progress} "
        f"completed={state.completed} "
        f"failed={state.failed}"
    )

    final_result = loop.last_result
    if final_result is not None:
        content = getattr(final_result, "content", None)
        if content:
            print(content)

    return 0 if state.completed else 1


def show_status(settings: Settings, state_path: Path | None) -> int:
    path = state_path or (
        settings.workspace / settings.state_dir / "state.json"
    )

    state = StateStore(path).load()

    print(f"task_id={state.task_id}")
    print(f"goal={state.goal}")
    print(f"phase={state.phase}")
    print(f"attempt={state.attempt}")
    print(f"progress={state.progress}")
    print(f"completed={state.completed}")
    print(f"failed={state.failed}")
    print(f"strategy={state.strategy}")

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        settings = Settings.from_environment()
        return run_task(settings, args.goal)

    if args.command == "status":
        settings = Settings.from_environment()
        return show_status(settings, args.state)

    if args.command == "resume":
        settings = Settings.from_environment()
        engine = build_engine(settings)

        state = engine.state_store.load()

        if state.task_id != args.task_id:
            parser.error(
                f"persisted task is {state.task_id!r}, "
                f"not {args.task_id!r}"
            )

        loop = AgentLoop(engine)
        resumed = loop.run(
            task_id=state.task_id,
            goal=state.goal or "",
        )

        print(
            f"task={resumed.task_id} "
            f"phase={resumed.phase} "
            f"progress={resumed.progress} "
            f"completed={resumed.completed} "
            f"failed={resumed.failed}"
        )

        return 0 if resumed.completed else 1

    parser.error(f"unknown command: {args.command}")
    return 2
