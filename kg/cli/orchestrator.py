"""The original kg subcommands: list / add / remove / hook.

Kept at the top level of `kg ...` as back-compat aliases so existing
muscle memory keeps working after the consolidation. The new home for
list/add/remove is under `kg project ...` (see kg/cli/project.py).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from kg import project as project_loader, registry


def cmd_list(args: argparse.Namespace) -> int:
    entries = registry.load()
    if not entries:
        print("No graphs registered. Use `kg project add <path>` to register one.")
        return 0
    default = registry.load_default()
    name_width = max(len(e.name) for e in entries)
    for e in entries:
        marker = "*" if e.name == default else " "
        print(f"{marker} {e.name:<{name_width}}  {e.path}")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    graph_dir = Path(args.path).expanduser().resolve()
    if not graph_dir.exists():
        print(f"Error: path does not exist: {graph_dir}", file=sys.stderr)
        return 1
    try:
        proj = project_loader.load(graph_dir)
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


def cmd_remove(args: argparse.Namespace) -> int:
    if registry.remove(args.name):
        print(f"Removed '{args.name}'")
        return 0
    print(f"Error: '{args.name}' is not registered", file=sys.stderr)
    return 1


def cmd_hook(args: argparse.Namespace) -> int:
    from kg import hook
    return hook.run(args.phase)


def register_alias(sub: argparse._SubParsersAction) -> None:
    """Register top-level back-compat aliases: kg list/add/remove/hook."""
    p_list = sub.add_parser("list", help="(alias of `kg project list`)")
    p_list.set_defaults(func=cmd_list)

    p_add = sub.add_parser("add", help="(alias of `kg project add`)")
    p_add.add_argument("path")
    p_add.set_defaults(func=cmd_add)

    p_remove = sub.add_parser("remove", help="(alias of `kg project remove`)")
    p_remove.add_argument("name")
    p_remove.set_defaults(func=cmd_remove)

    p_hook = sub.add_parser("hook", help="Hook dispatcher invoked by Claude Code settings.json.")
    p_hook.add_argument(
        "phase",
        choices=["pre-edit", "post-edit", "session-start", "session-end", "pre-irreversible"],
    )
    p_hook.set_defaults(func=cmd_hook)
