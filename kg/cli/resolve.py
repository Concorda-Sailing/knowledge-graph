"""Project resolver — the 7-step order for picking a project.

Every kg subsystem command calls `resolve_project()` at the start
of its handler. The result is a `Project` dataclass that handlers
use to set DEPGRAPH_DATA_DIR / LOGIGRAPH_DATA_DIR on subprocess
shims or pass into native Python handlers.

Resolution order (first match wins):

  1. --data-dir <path> or --project <name> flag
  2. $KG_PROJECT env var
  3. $DEPGRAPH_DATA_DIR / $LOGIGRAPH_DATA_DIR env vars (hook compat)
  4. Walk cwd ancestors for project.toml + nodes/
  5. `default = "..."` in kg-graphs.toml
  6. If exactly one project is registered, use it
  7. Error — list registered projects + --project flag for each
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from kg import registry
from kg.shared.env import DEPGRAPH_DATA_DIR, LOGIGRAPH_DATA_DIR


class ProjectResolutionError(Exception):
    """Base class for resolver failures."""


class UnknownProject(ProjectResolutionError):
    """A --project name or $KG_PROJECT value isn't registered."""


class AmbiguousProject(ProjectResolutionError):
    """Multiple projects registered and no signal picked one."""


class NoProject(ProjectResolutionError):
    """No projects registered and no flag/env gave us a path."""


@dataclass(frozen=True)
class Project:
    """Resolved project paths.

    `name` may be None if resolved by --data-dir flag to an unregistered path.
    `source` describes which resolution rule fired (for `kg project current`).
    """
    name: Optional[str]
    data_dir: Path           # the graph root containing project.toml + depgraph/ + logigraph/
    depgraph_dir: Path
    logigraph_dir: Path
    source: str


def _project_from_data_dir(data_dir: Path, source: str, name: Optional[str] = None) -> Project:
    """Build a Project from a data dir, looking up name in the registry if absent."""
    dd = data_dir.expanduser().resolve()
    # If `data_dir` points at a sub-dir (e.g. .../depgraph), step up to the umbrella root.
    if dd.name in ("depgraph", "logigraph") and (dd.parent / "project.toml").exists():
        dd = dd.parent
    if name is None:
        for e in registry.load():
            if e.path == dd:
                name = e.name
                break
    return Project(
        name=name,
        data_dir=dd,
        depgraph_dir=dd / "depgraph",
        logigraph_dir=dd / "logigraph",
        source=source,
    )


def _project_from_entry(entry: registry.GraphEntry, source: str) -> Project:
    return _project_from_data_dir(entry.path, source, name=entry.name)


def resolve_project(
    *,
    data_dir: Optional[Path] = None,
    project_name: Optional[str] = None,
) -> Project:
    """Resolve which project a command should operate on.

    Raises UnknownProject if a flag/env names an unregistered project.
    Raises AmbiguousProject if multiple are registered and nothing picked one.
    Raises NoProject if nothing is registered and nothing else gave us a path.
    """
    # Rule 1a: --data-dir flag
    if data_dir is not None:
        return _project_from_data_dir(data_dir, "--data-dir flag")

    # Rule 1b: --project flag
    if project_name is not None:
        entry = registry.find(project_name)
        if entry is None:
            raise UnknownProject(
                f"Project not registered: {project_name!r}. "
                f"Registered: {[e.name for e in registry.load()]}"
            )
        return _project_from_entry(entry, "--project flag")

    # Rule 2: $KG_PROJECT env var
    env_proj = os.environ.get("KG_PROJECT")
    if env_proj:
        entry = registry.find(env_proj)
        if entry is None:
            raise UnknownProject(
                f"$KG_PROJECT={env_proj!r} but that project is not registered."
            )
        return _project_from_entry(entry, "$KG_PROJECT")

    # Rule 3: $DEPGRAPH_DATA_DIR / $LOGIGRAPH_DATA_DIR env vars
    for var in (DEPGRAPH_DATA_DIR, LOGIGRAPH_DATA_DIR):
        val = os.environ.get(var)
        if val:
            return _project_from_data_dir(Path(val), f"${var}")

    # Rule 4: Walk cwd ancestors
    cwd = Path.cwd().resolve()
    for d in [cwd, *cwd.parents]:
        if (d / "project.toml").exists() and (d / "depgraph" / "nodes").is_dir():
            return _project_from_data_dir(d, "cwd ancestor walk")

    # Rule 5: default in registry
    default = registry.load_default()
    if default is not None:
        entry = registry.find(default)
        if entry is not None:
            return _project_from_entry(entry, "kg-graphs.toml default")

    # Rule 6: single registered
    entries = registry.load()
    if len(entries) == 1:
        return _project_from_entry(entries[0], "only registered project")

    # Rule 7: error
    if not entries:
        raise NoProject(
            "No projects registered and no --project / --data-dir / env / cwd hint.\n"
            "Register one with: kg project add <path>"
        )
    # The --project flag lives on each subcommand parser
    # (`kg depgraph --project <name> ...`, `kg logigraph --project <name> ...`),
    # not on the top-level `kg`. Spell out the canonical position so the
    # user doesn't try `kg --project <name> depgraph X` (which argparse
    # rejects).
    lines = [
        "Multiple projects registered — pass --project <name> AFTER the "
        "subcommand (e.g. `kg depgraph --project <name> regen`):",
    ]
    for e in entries:
        lines.append(f"  --project {e.name}      ({e.path})")
    raise AmbiguousProject("\n".join(lines))
