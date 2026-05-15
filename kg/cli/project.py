"""kg project — registry + per-project config commands.

Phase 1 verbs implemented in this task:
  list / show / current / use / add

Remaining verbs (Tasks 6-10):
  remove / init           (Task 6)
  add-repo / list-repos / remove-repo (Task 7)
  set                     (Task 9)
  health                  (Task 10)
"""
from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

from kg import registry
from kg.cli import resolve


def _cmd_list(args: argparse.Namespace) -> int:
    entries = registry.load()
    if not entries:
        print("No projects registered. Use `kg project add <path>` to register one.")
        return 0
    default = registry.load_default()
    name_width = max(len(e.name) for e in entries)
    for e in entries:
        marker = "*" if e.name == default else " "
        print(f"{marker} {e.name:<{name_width}}  {e.path}")
    return 0


def _cmd_use(args: argparse.Namespace) -> int:
    if args.clear:
        registry.clear_default()
        print("Cleared default project.")
        return 0
    if not args.name:
        print("Error: provide a project name or --clear", file=sys.stderr)
        return 1
    try:
        registry.save_default(args.name)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print(f"Default project set to '{args.name}'.")
    return 0


def _cmd_current(args: argparse.Namespace) -> int:
    try:
        proj = resolve.resolve_project()
    except resolve.ProjectResolutionError as e:
        print(f"No current project — {e}", file=sys.stderr)
        return 1
    name = proj.name or "(unregistered)"
    print(f"{name}  ({proj.source})")
    print(f"  data_dir:      {proj.data_dir}")
    print(f"  depgraph_dir:  {proj.depgraph_dir}")
    print(f"  logigraph_dir: {proj.logigraph_dir}")
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    try:
        proj = resolve.resolve_project(project_name=args.name)
    except resolve.ProjectResolutionError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print(f"Project: {proj.name or '(unregistered)'}")
    print(f"  Resolution:    {proj.source}")
    print(f"  data_dir:      {proj.data_dir}")
    print(f"  depgraph_dir:  {proj.depgraph_dir}")
    print(f"  logigraph_dir: {proj.logigraph_dir}")
    repos_toml = proj.depgraph_dir / "project.toml"
    if repos_toml.exists():
        cfg = tomllib.loads(repos_toml.read_text())
        repos = cfg.get("repos") or {}
        if repos:
            print(f"  repos ({len(repos)}):")
            for key, val in repos.items():
                if isinstance(val, dict):
                    print(f"    {key:<20}  {val.get('path', '?')}")
    return 0


def _cmd_add(args: argparse.Namespace) -> int:
    graph_dir = Path(args.path).expanduser().resolve()
    if not graph_dir.exists():
        print(f"Error: path does not exist: {graph_dir}", file=sys.stderr)
        return 1

    # Read only the project name from project.toml — don't call project.load()
    # because source_roots may not be present yet (add doesn't require them).
    toml_path = graph_dir / "project.toml"
    if not toml_path.exists():
        print(f"Error: no project.toml at {graph_dir}", file=sys.stderr)
        return 1
    try:
        data = tomllib.loads(toml_path.read_text())
    except tomllib.TOMLDecodeError as e:
        print(f"Error: invalid project.toml: {e}", file=sys.stderr)
        return 1

    proj_section = data.get("project") or {}
    name = proj_section.get("name")
    if not name:
        print(f"Error: project.toml at {graph_dir} is missing [project].name", file=sys.stderr)
        return 1

    try:
        entry = registry.add(name=name, path=graph_dir)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print(f"Registered '{entry.name}' at {entry.path}")
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("project", help="Per-project config and registry.")
    proj_sub = p.add_subparsers(dest="project_cmd", required=True)

    p_list = proj_sub.add_parser("list", help="List registered projects (default marked *).")
    p_list.set_defaults(func=_cmd_list)

    p_use = proj_sub.add_parser("use", help="Set persistent default project (or --clear).")
    p_use.add_argument("name", nargs="?", help="Project name to set as default.")
    p_use.add_argument("--clear", action="store_true", help="Unset the default project.")
    p_use.set_defaults(func=_cmd_use)

    p_current = proj_sub.add_parser("current", help="Print current project + how it was resolved.")
    p_current.set_defaults(func=_cmd_current)

    p_show = proj_sub.add_parser("show", help="Inspect a project's resolved paths and repos.")
    p_show.add_argument("name", nargs="?", help="Project name (defaults to current).")
    p_show.set_defaults(func=_cmd_show)

    p_add = proj_sub.add_parser("add", help="Register a project's data dir with the orchestrator.")
    p_add.add_argument("path", help="Path to the project's knowledge-graph dir.")
    p_add.set_defaults(func=_cmd_add)
