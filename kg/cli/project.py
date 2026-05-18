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
import re
import sys
import tomllib
from pathlib import Path

from kg import registry
from kg.cli import resolve


def _delegate_to_depgraph(proj: "resolve.Project", *args: str) -> int:
    """Run `depgraph <args>` against `proj`'s depgraph dir."""
    import os
    import subprocess
    tool_root = Path(__file__).resolve().parents[2]
    depgraph_bin = tool_root / "depgraph" / "bin" / "depgraph"
    env = {**os.environ, "DEPGRAPH_DATA_DIR": str(proj.depgraph_dir)}
    return subprocess.run([str(depgraph_bin), *args], env=env).returncode


def _resolved(args: argparse.Namespace) -> "resolve.Project":
    """Resolve project from --project / --data-dir flags or fall through."""
    return resolve.resolve_project(
        project_name=getattr(args, "project", None),
        data_dir=Path(args.data_dir).expanduser() if getattr(args, "data_dir", None) else None,
    )


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


def _cmd_remove(args: argparse.Namespace) -> int:
    if registry.remove(args.name):
        print(f"Removed '{args.name}'")
        return 0
    print(f"Error: '{args.name}' is not registered", file=sys.stderr)
    return 1


def _cmd_init(args: argparse.Namespace) -> int:
    """Phase 4: call the Python init handler directly."""
    from kg.cli.install.init import cmd_init
    return cmd_init(args)


def _cmd_add_repo(args: argparse.Namespace) -> int:
    try:
        proj = _resolved(args)
    except resolve.ProjectResolutionError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    cli_args = ["repo-add", args.key, args.path]
    if args.extractor:
        cli_args.extend(["--extractor", *args.extractor])
    for det in args.detector or []:
        cli_args.extend(["--detector", det])
    if args.files_arg:
        cli_args.append(f"--files-arg={args.files_arg}")
    if args.force:
        cli_args.append("--force")
    rc = _delegate_to_depgraph(proj, *cli_args)
    if rc == 0:
        # Mirror the [repos.<key>] table into logigraph/project.toml so the
        # logigraph pre-edit hook can classify edits in this repo. The two
        # sides go out of sync silently otherwise (#20).
        try:
            _mirror_repo_to_logigraph(proj, args.key, args.path)
        except OSError as e:
            print(f"warning: could not mirror [repos.{args.key}] to logigraph: {e}",
                  file=sys.stderr)
    return rc


def _normalize_repo_path_for_toml(p: str) -> str:
    """Rewrite absolute paths under $HOME to ~/... so project.toml stays
    portable across users. Mirrors depgraph/lib/cli/repo.py::_normalize_repo_path."""
    home = str(Path.home())
    abs_p = str(Path(p).expanduser())
    if abs_p.startswith(home + "/"):
        return "~" + abs_p[len(home):]
    return p


def _mirror_repo_to_logigraph(proj: "resolve.Project", key: str, path: str) -> None:
    """Write [repos.<key>] path = "..." into the logigraph project.toml,
    replacing any existing block for the same key. No-op if logigraph isn't
    scaffolded yet (older projects)."""
    cfg = proj.logigraph_dir / "project.toml"
    if not cfg.exists():
        return
    stored = _normalize_repo_path_for_toml(path)
    text = cfg.read_text()
    pattern = re.compile(
        r"(?ms)^\[repos\." + re.escape(key) + r"\][^\n]*\n(?:(?!^\[).*\n?)*"
    )
    text = pattern.sub("", text).rstrip() + "\n"
    if not text.endswith("\n\n"):
        text += "\n"
    text += f'[repos.{key}]\npath = "{stored}"\n'
    cfg.write_text(text)


def _remove_repo_from_logigraph(proj: "resolve.Project", key: str) -> None:
    cfg = proj.logigraph_dir / "project.toml"
    if not cfg.exists():
        return
    text = cfg.read_text()
    pattern = re.compile(
        r"(?ms)^\[repos\." + re.escape(key) + r"\][^\n]*\n(?:(?!^\[).*\n?)*"
    )
    new = pattern.sub("", text).rstrip() + "\n"
    if new != text:
        cfg.write_text(new)


def _cmd_list_repos(args: argparse.Namespace) -> int:
    try:
        proj = _resolved(args)
    except resolve.ProjectResolutionError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return _delegate_to_depgraph(proj, "repo-list")


def _cmd_remove_repo(args: argparse.Namespace) -> int:
    try:
        proj = _resolved(args)
    except resolve.ProjectResolutionError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    rc = _delegate_to_depgraph(proj, "repo-remove", args.key)
    if rc == 0:
        try:
            _remove_repo_from_logigraph(proj, args.key)
        except OSError as e:
            print(f"warning: could not remove [repos.{args.key}] from logigraph: {e}",
                  file=sys.stderr)
    return rc


_SET_WHITELIST = {
    "primary_repo":         {"toml": "depgraph/project.toml", "section": "project", "key": "primary_repo"},
    "logigraph.data_dir":   {"toml": "depgraph/project.toml", "section": "logigraph", "key": "data_dir"},
    "memory.dir":           {"toml": "depgraph/project.toml", "section": "memory", "key": "dir"},
}


def _cmd_set(args: argparse.Namespace) -> int:
    if args.field not in _SET_WHITELIST:
        print(
            f"Error: '{args.field}' is not in whitelist. Allowed: "
            f"{', '.join(sorted(_SET_WHITELIST))}",
            file=sys.stderr,
        )
        return 1
    try:
        proj = _resolved(args)
    except resolve.ProjectResolutionError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    spec = _SET_WHITELIST[args.field]
    cfg_path = proj.data_dir / spec["toml"]
    if not cfg_path.exists():
        print(f"Error: {cfg_path} does not exist", file=sys.stderr)
        return 1

    # Validation for specific fields
    if args.field == "primary_repo":
        existing = tomllib.loads(cfg_path.read_text())
        repos = existing.get("repos") or {}
        if args.value not in repos:
            print(
                f"Error: primary_repo='{args.value}' but no [repos.{args.value}] table. "
                f"Configured: {sorted(repos)}",
                file=sys.stderr,
            )
            return 1

    _write_toml_key(cfg_path, spec["section"], spec["key"], args.value)
    print(f"set {args.field} = {args.value!r} in {cfg_path}")
    return 0


def _write_toml_key(cfg_path: Path, section: str, key: str, value: str) -> None:
    """Idempotently set [section] key = "value" in cfg_path. Preserves other content.

    When the key doesn't yet exist in the section, it is inserted directly
    after the last existing `key = value` line in the section — NOT at the
    bottom of the section body. Bottom-of-body placement (the prior
    behavior) put new keys immediately above the next table header with
    no blank-line separator; a reader (or another AI) seeing

        [project]
        name = "myproject"
        # [repos.web]    <- commented example block in the way
        primary_repo = "api"
        [repos.api]

    reasonably believed `primary_repo` belonged to `[repos.api]`. Putting
    the new key next to the section's other key=value lines keeps the
    visual association unambiguous (#31).
    """
    import re
    text = cfg_path.read_text()
    section_header = f"[{section}]"
    new_line = f'{key} = "{value}"'

    if section_header not in text:
        # Append new section at end.
        if not text.endswith("\n"):
            text += "\n"
        text += f"\n{section_header}\n{new_line}\n"
        cfg_path.write_text(text)
        return

    # Find the section body — from header up to next top-level [ or EOF.
    pattern_section = re.compile(
        r"(\[" + re.escape(section) + r"\][^\n]*\n)((?:(?!^\[).*\n?)*)",
        re.MULTILINE,
    )
    m = pattern_section.search(text)
    if not m:
        # Should not happen given the header check above, but fall through.
        text += f"\n{section_header}\n{new_line}\n"
        cfg_path.write_text(text)
        return

    body = m.group(2)
    key_re = re.compile(r"^" + re.escape(key) + r"\s*=.*$", re.MULTILINE)
    if key_re.search(body):
        new_body = key_re.sub(new_line, body)
    else:
        new_body = _insert_after_last_assignment(body, new_line)
    text = text[: m.start(2)] + new_body + text[m.end(2):]
    cfg_path.write_text(text)


def _insert_after_last_assignment(body: str, new_line: str) -> str:
    """Insert `new_line` into a TOML section body right after the last
    `key = value` line. Comments, blank lines, and commented-out table
    examples are left in place so the inserted key visually lives with
    its section's other settings.

    If the section has no existing key=value lines yet, insert at the
    top (immediately after the section header — i.e., at line 0 of body).
    """
    import re
    assignment_re = re.compile(r"^\s*[A-Za-z_][\w.-]*\s*=")
    # body usually ends with "\n"; splitlines() drops the trailing empty.
    lines = body.split("\n")
    # Track whether the body had a trailing newline so we can restore it.
    had_trailing_newline = body.endswith("\n")
    if had_trailing_newline and lines and lines[-1] == "":
        lines.pop()
    last_assignment_idx = -1
    for i, line in enumerate(lines):
        if assignment_re.match(line):
            last_assignment_idx = i
    if last_assignment_idx >= 0:
        new_lines = (
            lines[: last_assignment_idx + 1]
            + [new_line]
            + lines[last_assignment_idx + 1 :]
        )
    else:
        new_lines = [new_line] + lines
    out = "\n".join(new_lines)
    if had_trailing_newline:
        out += "\n"
    return out


def _cmd_health(args: argparse.Namespace) -> int:
    import os
    import subprocess
    try:
        proj = _resolved(args)
    except resolve.ProjectResolutionError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    tool_root = Path(__file__).resolve().parents[2]
    overall = 0

    print(f"## {proj.name or '(unregistered)'} health\n")

    # depgraph
    print("### depgraph")
    sys.stdout.flush()  # subprocess writes inherit fd 1 and bypass Python's buffer
    if proj.depgraph_dir.exists():
        rc = subprocess.run(
            [str(tool_root / "depgraph" / "bin" / "depgraph"), "health"],
            env={**os.environ, "DEPGRAPH_DATA_DIR": str(proj.depgraph_dir)},
        ).returncode
        overall |= rc
    else:
        print(f"  (no depgraph dir at {proj.depgraph_dir})")
        overall |= 1
    print()

    # logigraph
    print("### logigraph")
    sys.stdout.flush()
    if proj.logigraph_dir.exists():
        rc = subprocess.run(
            [str(tool_root / "logigraph" / "bin" / "logigraph"), "health"],
            env={**os.environ, "LOGIGRAPH_DATA_DIR": str(proj.logigraph_dir)},
        ).returncode
        overall |= rc
    else:
        print(f"  (no logigraph dir at {proj.logigraph_dir})")
        overall |= 1
    print()

    # Per-repo path-exists
    print("### repos")
    depgraph_proj = proj.depgraph_dir / "project.toml"
    if depgraph_proj.exists():
        import tomllib
        cfg = tomllib.loads(depgraph_proj.read_text())
        repos = cfg.get("repos") or {}
        if repos:
            for key, val in repos.items():
                if not isinstance(val, dict):
                    continue
                path = Path(str(val.get("path", ""))).expanduser()
                ok = path.exists()
                mark = "✓" if ok else "✗"
                print(f"  {mark} {key:<20} {path}")
                if not ok:
                    overall |= 1
        else:
            print("  (no repos configured)")
    else:
        print(f"  (no depgraph project.toml at {depgraph_proj})")

    return overall


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("project", help="Per-project config and registry.")
    p.add_argument("--project", help="Project name (overrides env/cwd/default).")
    p.add_argument("--data-dir", help="Project data dir path (escape hatch for unregistered).")
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

    p_remove = proj_sub.add_parser("remove", help="Unregister a project (does not delete on disk).")
    p_remove.add_argument("name")
    p_remove.set_defaults(func=_cmd_remove)

    p_init = proj_sub.add_parser("init", help="Scaffold a fresh project's data layout.")
    p_init.add_argument("path", help="Project root (knowledge-graph subdir will be created here).")
    p_init.set_defaults(func=_cmd_init)

    p_ar = proj_sub.add_parser("add-repo", help="Add a [repos.<key>] entry to project.toml.")
    p_ar.add_argument("key")
    p_ar.add_argument("path")
    p_ar.add_argument("--extractor", nargs="+")
    p_ar.add_argument("--detector", action="append", default=[])
    p_ar.add_argument("--files-arg", default=None)
    p_ar.add_argument("--force", action="store_true")
    p_ar.set_defaults(func=_cmd_add_repo)

    p_lr = proj_sub.add_parser("list-repos", help="List configured [repos.*] entries.")
    p_lr.set_defaults(func=_cmd_list_repos)

    p_rr = proj_sub.add_parser("remove-repo", help="Remove a [repos.<key>] entry.")
    p_rr.add_argument("key")
    p_rr.set_defaults(func=_cmd_remove_repo)

    p_set = proj_sub.add_parser(
        "set",
        help=f"Set a project.toml field. Whitelisted: {', '.join(sorted(_SET_WHITELIST))}.",
    )
    p_set.add_argument("field")
    p_set.add_argument("value")
    p_set.set_defaults(func=_cmd_set)

    p_health = proj_sub.add_parser("health", help="Cross-subsystem health (depgraph + logigraph + repo paths).")
    p_health.set_defaults(func=_cmd_health)
