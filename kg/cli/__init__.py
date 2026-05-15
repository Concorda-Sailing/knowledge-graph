"""CLI entry point for ``kg``.

Subcommands:

* ``kg list`` — show registered graphs
* ``kg add <path>`` — register a graph repo (reads its project.toml for the name)
* ``kg remove <name>`` — unregister (does not delete from disk)
* ``kg hook <phase>`` — hook dispatcher invoked by Claude Code settings.json

Exit codes:
    0  success
    1  user error (bad args, duplicate name, missing path)
    2  registry error (corrupt, unreadable)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from kg import project, registry


def _cmd_list(args: argparse.Namespace) -> int:
    entries = registry.load()
    if not entries:
        print("No graphs registered. Use `kg add <path>` to register one.")
        return 0
    name_width = max(len(e.name) for e in entries)
    for e in entries:
        print(f"  {e.name:<{name_width}}  {e.path}")
    return 0


def _cmd_add(args: argparse.Namespace) -> int:
    graph_dir = Path(args.path).expanduser().resolve()
    if not graph_dir.exists():
        print(f"Error: path does not exist: {graph_dir}", file=sys.stderr)
        return 1

    try:
        proj = project.load(graph_dir)
    except FileNotFoundError as e:
        print(f"Error: no project.toml at {graph_dir}: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: invalid project.toml: {e}", file=sys.stderr)
        return 1

    try:
        entry = registry.add(name=proj.name, path=graph_dir)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Registered '{entry.name}' at {entry.path}")
    return 0


def _cmd_remove(args: argparse.Namespace) -> int:
    if registry.remove(args.name):
        print(f"Removed '{args.name}'")
        return 0
    print(f"Error: '{args.name}' is not registered", file=sys.stderr)
    return 1


def _cmd_hook(args: argparse.Namespace) -> int:
    # Implemented in kg.hook; imported lazily so plain `kg list` etc. stay fast.
    from kg import hook

    return hook.run(args.phase)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="kg",
        description="Knowledge-graph orchestrator and lifecycle CLI.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    sub_list = sub.add_parser("list", help="List registered graphs.")
    sub_list.set_defaults(func=_cmd_list)

    sub_add = sub.add_parser(
        "add",
        help="Register a graph repo at <path>. Reads project.toml for name.",
    )
    sub_add.add_argument("path", help="Path to the graph repo's root directory.")
    sub_add.set_defaults(func=_cmd_add)

    sub_remove = sub.add_parser(
        "remove",
        help="Unregister a graph by name. Does not delete the graph on disk.",
    )
    sub_remove.add_argument("name", help="Registered name of the graph.")
    sub_remove.set_defaults(func=_cmd_remove)

    sub_hook = sub.add_parser(
        "hook",
        help="Hook dispatcher invoked by Claude Code settings.json.",
    )
    sub_hook.add_argument(
        "phase",
        choices=[
            "pre-edit",
            "post-edit",
            "session-start",
            "session-end",
            "pre-irreversible",
        ],
    )
    sub_hook.set_defaults(func=_cmd_hook)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
