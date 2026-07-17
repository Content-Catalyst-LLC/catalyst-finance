"""Command-line workspace management for Catalyst Finance."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel, ValidationError

from .repositories import (
    JsonWorkspaceRepository,
    SQLiteWorkspaceRepository,
    WorkspaceNotFoundError,
    WorkspaceRepository,
)
from .templates import list_templates
from .version import __version__
from .workspace import WorkspaceConflictError, WorkspaceService
from .workspace_models import WorkspaceDefaults


def _repository(args: argparse.Namespace) -> WorkspaceRepository:
    if args.sqlite:
        return SQLiteWorkspaceRepository(args.sqlite)
    return JsonWorkspaceRepository(args.directory)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create and manage persistent Catalyst Finance workspaces."
    )
    parser.add_argument("--version", action="version", version=__version__)
    storage = parser.add_mutually_exclusive_group()
    storage.add_argument(
        "--directory",
        type=Path,
        default=Path.home() / ".catalyst-finance" / "workspaces",
        help="JSON workspace directory.",
    )
    storage.add_argument("--sqlite", type=Path, help="SQLite workspace database.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="Create a workspace.")
    create.add_argument("name")
    create.add_argument("--description", default="")
    create.add_argument("--currency", default="USD")
    create.add_argument("--locale", default="en-US")

    subparsers.add_parser("list", help="List workspaces.")

    show = subparsers.add_parser("show", help="Show a workspace.")
    show.add_argument("workspace_id")

    add_project = subparsers.add_parser("add-project", help="Add a project.")
    add_project.add_argument("workspace_id")
    add_project.add_argument("name")

    add_scenario = subparsers.add_parser("add-scenario", help="Add a scenario.")
    add_scenario.add_argument("workspace_id")
    add_scenario.add_argument("name")
    add_scenario.add_argument("--template", default="capital-project")
    add_scenario.add_argument("--alternative", default="Base")
    add_scenario.add_argument("--project-id")

    export = subparsers.add_parser("export", help="Export a complete workspace.")
    export.add_argument("workspace_id")
    export.add_argument("output", type=Path)

    import_parser = subparsers.add_parser("import", help="Import a workspace.")
    import_parser.add_argument("input", type=Path)
    import_parser.add_argument("--replace", action="store_true")

    delete = subparsers.add_parser("delete", help="Delete a workspace.")
    delete.add_argument("workspace_id")

    subparsers.add_parser("templates", help="List built-in scenario templates.")
    return parser


def _jsonable(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


def _dump(value: object) -> None:
    print(json.dumps(_jsonable(value), indent=2))


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    service = WorkspaceService(_repository(args))
    try:
        if args.command == "create":
            _dump(
                service.create_workspace(
                    args.name,
                    description=args.description,
                    defaults=WorkspaceDefaults(
                        currency=args.currency, locale=args.locale
                    ),
                )
            )
        elif args.command == "list":
            _dump(service.list_workspaces())
        elif args.command == "show":
            _dump(service.get_workspace(args.workspace_id))
        elif args.command == "add-project":
            _dump(service.add_project(args.workspace_id, args.name))
        elif args.command == "add-scenario":
            _dump(
                service.create_scenario(
                    args.workspace_id,
                    args.name,
                    template_id=args.template,
                    alternative_label=args.alternative,
                    project_id=args.project_id,
                )
            )
        elif args.command == "export":
            _dump(service.export_workspace(args.workspace_id, args.output))
        elif args.command == "import":
            _dump(service.import_workspace_file(args.input, replace=args.replace))
        elif args.command == "delete":
            service.delete_workspace(args.workspace_id)
            _dump({"deleted": args.workspace_id})
        elif args.command == "templates":
            _dump(list_templates())
        else:
            raise ValueError(f"Unknown command: {args.command}")
    except (
        ValidationError,
        WorkspaceNotFoundError,
        WorkspaceConflictError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(
            json.dumps({"error": type(exc).__name__, "message": str(exc)}),
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
