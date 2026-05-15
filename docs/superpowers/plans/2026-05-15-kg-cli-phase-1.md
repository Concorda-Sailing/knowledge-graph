# Consolidated `kg` CLI — Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a single discoverable `kg` CLI entry point with `kg project / kg depgraph / kg logigraph / kg install / kg hook` groups, a project selector (`kg project use <name>` + 7-step resolution), and back-compat aliases so `depgraph`, `logigraph`, and `install.sh` keep working unchanged.

**Architecture:** Convert `kg/cli.py` (flat module, 128 LOC) into the `kg.cli` package. Extract the existing 4 orchestrator commands into `kg.cli.orchestrator`. Add `kg.cli.resolve` (project resolver returning a `Project` dataclass). Implement `kg.cli.project` natively (writes/reads `project.toml` + registry). Implement `kg.cli.depgraph` / `kg.cli.logigraph` / `kg.cli.install` as subprocess shims that forward argv to the existing CLIs after exporting `DEPGRAPH_DATA_DIR` / `LOGIGRAPH_DATA_DIR` from the resolved project. Extend `kg.registry` with a top-level `default = "..."` key in `kg-graphs.toml`. Add `depgraph repo-remove` to round out the `add-repo` / `list-repos` / `remove-repo` triple.

**Tech Stack:** Python 3.11+, argparse, stdlib `tomllib` (read), text-append writes for TOML mutation, pytest with `KG_REGISTRY_PATH`-override fixture pattern (existing in `tests/kg/test_registry.py`), subprocess shims via `os.execvpe` for transparent argv forwarding.

---

## File Structure

**New files (in `~/tools/knowledge-graph/`):**
- `kg/cli/__init__.py` — top-level dispatcher; registers 5 groups + 4 back-compat aliases
- `kg/cli/orchestrator.py` — existing `kg list / add / remove / hook` extracted from old `kg/cli.py`
- `kg/cli/resolve.py` — `Project` dataclass + `resolve_project()` (the 7-step order)
- `kg/cli/project.py` — `kg project` group: list / show / current / use / add / remove / init / add-repo / list-repos / remove-repo / set / health
- `kg/cli/depgraph.py` — subprocess shim for `kg depgraph <argv>`
- `kg/cli/logigraph.py` — subprocess shim for `kg logigraph <argv>`
- `kg/cli/install.py` — subprocess shim for `kg install <argv>`
- `docs/CLI.md` — user-facing command reference
- `tests/kg/test_resolve.py` — resolver tests (7-rule coverage)
- `tests/kg/test_cli_project.py` — `kg project` group tests
- `tests/kg/test_cli_subprocess_shims.py` — shim smoke tests

**Modified files:**
- `kg/cli.py` — **deleted** (content moves to `kg/cli/__init__.py` + `kg/cli/orchestrator.py`)
- `kg/registry.py` — adds `load_default()`, `save_default(name)`, `clear_default()`; `save(entries)` preserves the default key
- `depgraph/bin/depgraph` — adds `repo-remove <key>` subcommand
- `tests/kg/test_registry.py` — adds tests for default-key roundtrip

**Memory files (in `~/.claude/projects/-home-lgreenlee/memory/`):**
- `reference_kg_cli.md` — cross-session aide (structure, recall hooks, gotchas)
- `MEMORY.md` — append one-line pointer to the above

---

## Task 1: Convert `kg/cli.py` to package layout (no behavior change)

**Files:**
- Delete: `kg/cli.py`
- Create: `kg/cli/__init__.py` (verbatim content of old `kg/cli.py`)
- Verify: `bin/kg` still works; tests still pass.

- [ ] **Step 1: Move the file into a package directory**

```bash
mkdir kg/cli
git mv kg/cli.py kg/cli/__init__.py
```

- [ ] **Step 2: Run the existing test suite — must stay green**

Run: `python3 -m pytest tests/kg/ -q`
Expected: `45 passed`. Same count as before the move.

- [ ] **Step 3: Smoke-test the bin/kg dispatcher**

Run: `KG_REGISTRY_PATH=/tmp/kg-test.toml bin/kg list`
Expected: `No graphs registered. Use 'kg add <path>' to register one.`

- [ ] **Step 4: Commit**

```bash
git add kg/cli.py kg/cli/__init__.py
git commit -m "$(cat <<'EOF'
kg/cli: promote to package (no behavior change)

Phase 1 of the consolidated-kg-CLI plan needs kg/cli/ to host
multiple submodules (resolve, project, depgraph, logigraph, install).
Moves the existing kg/cli.py verbatim into kg/cli/__init__.py.
bin/kg's `from kg.cli import main` continues to resolve.

All 45 existing tests pass; no behavior change.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: `kg.registry` — top-level `default` key

**Files:**
- Modify: `kg/registry.py`
- Modify: `tests/kg/test_registry.py`

- [ ] **Step 1: Add failing tests**

Append to `tests/kg/test_registry.py`:

```python
def test_load_default_returns_none_when_unset(tmp_registry: Path) -> None:
    assert registry.load_default() is None


def test_load_default_returns_none_when_file_missing(tmp_registry: Path) -> None:
    assert not tmp_registry.exists()
    assert registry.load_default() is None


def test_save_default_then_load(tmp_registry: Path, tmp_path: Path) -> None:
    graph_dir = tmp_path / "concorda-knowledge-graph"
    graph_dir.mkdir()
    registry.add(name="concorda", path=graph_dir)

    registry.save_default("concorda")
    assert registry.load_default() == "concorda"


def test_save_default_rejects_unregistered_name(tmp_registry: Path) -> None:
    with pytest.raises(ValueError, match="not registered"):
        registry.save_default("nope")


def test_clear_default(tmp_registry: Path, tmp_path: Path) -> None:
    graph_dir = tmp_path / "g"
    graph_dir.mkdir()
    registry.add(name="g", path=graph_dir)
    registry.save_default("g")
    assert registry.load_default() == "g"

    registry.clear_default()
    assert registry.load_default() is None


def test_default_persists_through_add(tmp_registry: Path, tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    registry.add(name="a", path=tmp_path / "a")
    registry.save_default("a")

    registry.add(name="b", path=tmp_path / "b")
    assert registry.load_default() == "a"


def test_default_cleared_when_target_removed(tmp_registry: Path, tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    registry.add(name="a", path=tmp_path / "a")
    registry.save_default("a")

    registry.remove("a")
    assert registry.load_default() is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/kg/test_registry.py -q -k default`
Expected: 7 failures (`AttributeError: module 'kg.registry' has no attribute 'load_default'`)

- [ ] **Step 3: Implement in `kg/registry.py`**

After the existing `_HEADER` constant, add the default-tracking module:

```python
def _read_raw() -> dict:
    """Read the registry file as parsed TOML. Returns {} if missing."""
    p = path()
    if not p.exists():
        return {}
    return tomllib.loads(p.read_text())


def load_default() -> Optional[str]:
    """Return the name of the default project, or None if unset/missing."""
    data = _read_raw()
    val = data.get("default")
    if isinstance(val, str) and val:
        # Only honor it if the target is still registered.
        if find(val) is not None:
            return val
    return None
```

Replace the existing `save()` function with:

```python
def save(entries: list[GraphEntry], *, default: Optional[str] = _SENTINEL) -> None:
    """Write entries (and optionally the default) to the registry path.

    `default` semantics:
      - omitted / _SENTINEL: preserve the existing default key (if any).
      - None: explicitly clear the default key.
      - str: set the default to this name.
    """
    p = path()
    p.parent.mkdir(parents=True, exist_ok=True)

    if default is _SENTINEL:
        # Preserve whatever was there before this write.
        current = _read_raw().get("default")
        default_to_write = current if isinstance(current, str) else None
    else:
        default_to_write = default

    body = _HEADER
    if default_to_write:
        body += f'default = "{default_to_write}"\n\n'
    for e in entries:
        body += "[[graph]]\n"
        body += f'name = "{e.name}"\n'
        body += f'path = "{e.path}"\n'
        body += "\n"
    p.write_text(body)
```

Add the sentinel near the top of the file (after `DEFAULT_REGISTRY`):

```python
_SENTINEL = object()  # marker for "argument not supplied" in save()
```

Add `save_default` and `clear_default`:

```python
def save_default(name: str) -> None:
    """Set the default project to `name`. Raises ValueError if not registered."""
    if find(name) is None:
        raise ValueError(f"Cannot set default — '{name}' is not registered")
    entries = load()
    save(entries, default=name)


def clear_default() -> None:
    """Unset the default project. No-op if no default was set."""
    entries = load()
    save(entries, default=None)
```

Modify `remove()` so it clears the default if the removed entry was the default:

```python
def remove(name: str) -> bool:
    """Remove a graph by name. Returns True if removed, False if not present.

    If the removed entry was the default, the default key is cleared.
    """
    entries = load()
    keep = [e for e in entries if e.name != name]
    if len(keep) == len(entries):
        return False
    current_default = _read_raw().get("default")
    new_default: Optional[str]
    if current_default == name:
        new_default = None
    elif isinstance(current_default, str):
        new_default = current_default
    else:
        new_default = None
    save(keep, default=new_default)
    return True
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/kg/test_registry.py -q`
Expected: All tests pass (existing + 7 new = ~22 total in this file)

- [ ] **Step 5: Commit**

```bash
git add kg/registry.py tests/kg/test_registry.py
git commit -m "$(cat <<'EOF'
kg/registry: persistent default-project key in kg-graphs.toml

Adds a top-level `default = "..."` field to ~/.claude/kg-graphs.toml.
Lets `kg project use <name>` persist a default so bare commands like
`kg depgraph regen` (Phase 1 follow-on) resolve a project without
needing --project on every invocation.

New surface:
  registry.load_default() -> Optional[str]
  registry.save_default(name)        — raises if name not registered
  registry.clear_default()
  registry.save(entries, *, default=...)  — preserves default by default;
                                           pass None to clear, str to set.
  registry.remove(name)              — auto-clears default if target removed

Backward-compat: older kg versions that don't know about `default` will
ignore the key (tomllib.get returns None on unknown top-level fields).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: `kg.cli.resolve` — project resolver

**Files:**
- Create: `kg/cli/resolve.py`
- Create: `tests/kg/test_resolve.py`

- [ ] **Step 1: Write the resolver tests**

Create `tests/kg/test_resolve.py`:

```python
"""Tests for kg.cli.resolve — the 7-step project resolver."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

TOOL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TOOL_ROOT))

from kg import registry  # noqa: E402
from kg.cli import resolve  # noqa: E402


@pytest.fixture
def two_projects(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    """Set up two registered projects with full data-dir layouts."""
    monkeypatch.setenv("KG_REGISTRY_PATH", str(tmp_path / "kg-graphs.toml"))
    monkeypatch.delenv("KG_PROJECT", raising=False)
    monkeypatch.delenv("DEPGRAPH_DATA_DIR", raising=False)
    monkeypatch.delenv("LOGIGRAPH_DATA_DIR", raising=False)

    def make(name: str) -> Path:
        root = tmp_path / f"{name}-knowledge-graph"
        (root / "depgraph" / "nodes").mkdir(parents=True)
        (root / "logigraph" / "nodes").mkdir(parents=True)
        (root / "project.toml").write_text(
            f'[project]\nname = "{name}"\nsubsystems = ["depgraph", "logigraph"]\n'
        )
        (root / "depgraph" / "project.toml").write_text(
            f'[project]\nname = "{name}"\n'
        )
        (root / "logigraph" / "project.toml").write_text(
            f'[project]\nname = "{name}"\n'
        )
        registry.add(name=name, path=root)
        return root

    return {
        "concorda": make("concorda"),
        "demo": make("demo"),
        "tmp_path": tmp_path,
    }


def test_rule_1_data_dir_flag_wins(two_projects: dict) -> None:
    proj = resolve.resolve_project(data_dir=two_projects["concorda"] / "depgraph")
    assert proj.name == "concorda"
    assert proj.source == "--data-dir flag"


def test_rule_1_project_flag(two_projects: dict) -> None:
    proj = resolve.resolve_project(project_name="demo")
    assert proj.name == "demo"
    assert proj.source == "--project flag"


def test_rule_1_project_flag_unknown_errors(two_projects: dict) -> None:
    with pytest.raises(resolve.UnknownProject):
        resolve.resolve_project(project_name="ghost")


def test_rule_2_KG_PROJECT_env(two_projects: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KG_PROJECT", "demo")
    proj = resolve.resolve_project()
    assert proj.name == "demo"
    assert proj.source == "$KG_PROJECT"


def test_rule_3_DEPGRAPH_DATA_DIR_env(two_projects: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEPGRAPH_DATA_DIR", str(two_projects["concorda"] / "depgraph"))
    proj = resolve.resolve_project()
    assert proj.name == "concorda"
    assert proj.source == "$DEPGRAPH_DATA_DIR"


def test_rule_4_cwd_ancestor_walk(two_projects: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(two_projects["concorda"] / "depgraph")
    proj = resolve.resolve_project()
    assert proj.name == "concorda"
    assert proj.source == "cwd ancestor walk"


def test_rule_5_default_in_registry(two_projects: dict) -> None:
    registry.save_default("demo")
    proj = resolve.resolve_project()
    assert proj.name == "demo"
    assert proj.source == "kg-graphs.toml default"


def test_rule_6_single_registered_used_implicitly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KG_REGISTRY_PATH", str(tmp_path / "kg-graphs.toml"))
    monkeypatch.delenv("KG_PROJECT", raising=False)
    monkeypatch.delenv("DEPGRAPH_DATA_DIR", raising=False)
    monkeypatch.delenv("LOGIGRAPH_DATA_DIR", raising=False)
    monkeypatch.chdir(tmp_path)

    root = tmp_path / "solo-knowledge-graph"
    (root / "depgraph" / "nodes").mkdir(parents=True)
    (root / "logigraph" / "nodes").mkdir(parents=True)
    (root / "project.toml").write_text(
        '[project]\nname = "solo"\nsubsystems = ["depgraph", "logigraph"]\n'
    )
    registry.add(name="solo", path=root)

    proj = resolve.resolve_project()
    assert proj.name == "solo"
    assert proj.source == "only registered project"


def test_rule_7_ambiguous_errors_with_list(two_projects: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(two_projects["tmp_path"])
    with pytest.raises(resolve.AmbiguousProject) as exc:
        resolve.resolve_project()
    msg = str(exc.value)
    assert "concorda" in msg
    assert "demo" in msg
    assert "--project" in msg


def test_project_dataclass_paths(two_projects: dict) -> None:
    proj = resolve.resolve_project(project_name="concorda")
    assert proj.data_dir == (two_projects["concorda"]).resolve()
    assert proj.depgraph_dir == (two_projects["concorda"] / "depgraph").resolve()
    assert proj.logigraph_dir == (two_projects["concorda"] / "logigraph").resolve()
```

- [ ] **Step 2: Run tests — expect failures**

Run: `python3 -m pytest tests/kg/test_resolve.py -q`
Expected: `ImportError: cannot import name 'resolve' from 'kg.cli'`

- [ ] **Step 3: Implement `kg/cli/resolve.py`**

```python
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
    for var in ("DEPGRAPH_DATA_DIR", "LOGIGRAPH_DATA_DIR"):
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
    lines = ["Multiple projects registered — pick one with --project <name>:"]
    for e in entries:
        lines.append(f"  --project {e.name}      ({e.path})")
    raise AmbiguousProject("\n".join(lines))
```

- [ ] **Step 4: Run tests — expect pass**

Run: `python3 -m pytest tests/kg/test_resolve.py -q`
Expected: 10 passed

- [ ] **Step 5: Commit**

```bash
git add kg/cli/resolve.py tests/kg/test_resolve.py
git commit -m "$(cat <<'EOF'
kg/cli: project resolver with 7-step order

Every kg subsystem command needs to know which project to operate on.
This resolver runs at the start of every handler and returns a
Project dataclass (name, data_dir, depgraph_dir, logigraph_dir,
source).

Resolution order (first match wins):
  1. --data-dir / --project flag
  2. $KG_PROJECT env var
  3. $DEPGRAPH_DATA_DIR / $LOGIGRAPH_DATA_DIR env vars (hook compat)
  4. cwd-ancestor walk (project.toml + depgraph/nodes/)
  5. kg-graphs.toml `default` key
  6. Single registered project (implicit)
  7. Error with the list of registered projects + --project flag for each

The `source` field carries which rule fired — surfaced by
`kg project current` so users can tell why a given project was picked.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Extract orchestrator commands

**Files:**
- Create: `kg/cli/orchestrator.py` (move `_cmd_list / _cmd_add / _cmd_remove / _cmd_hook` + `build_parser` content out of `__init__.py`)
- Modify: `kg/cli/__init__.py` — keep `main()`, delegate to orchestrator for the existing 4 commands.

- [ ] **Step 1: Create `kg/cli/orchestrator.py`**

```python
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
```

- [ ] **Step 2: Rewrite `kg/cli/__init__.py` to delegate**

Replace the whole file with:

```python
"""Top-level kg CLI dispatcher.

Groups under `kg`:
  project    — registry + per-project config (kg.cli.project)
  depgraph   — code-graph operations (kg.cli.depgraph, subprocess shim Phase 1)
  logigraph  — rules-graph operations (kg.cli.logigraph, subprocess shim Phase 1)
  install    — machine setup (kg.cli.install, subprocess shim Phase 1)
  hook       — Claude Code hook dispatcher (kg.cli.orchestrator)

Top-level back-compat aliases (kg list / add / remove) delegate into
kg.cli.orchestrator so the legacy surface keeps working.
"""
from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="kg",
        description="Knowledge-graph orchestrator and lifecycle CLI.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    from kg.cli import orchestrator, project, depgraph, logigraph, install
    project.register(sub)
    depgraph.register(sub)
    logigraph.register(sub)
    install.register(sub)
    orchestrator.register_alias(sub)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args, extra = parser.parse_known_args(argv)
    # Subprocess shims (depgraph/logigraph/install) need raw argv to forward;
    # they stash a `forward_argv` attribute via their handler.
    return args.func(args, extra) if getattr(args, "wants_extra", False) else args.func(args)


if __name__ == "__main__":
    sys.exit(main())
```

(Note: the `wants_extra` mechanism is used by Tasks 11–13 — subprocess shims need to forward unrecognized argv. Native handlers don't.)

- [ ] **Step 3: Create stub registration functions for the not-yet-built groups**

Until Tasks 5–13 land, the package import in `build_parser` will fail because `project`, `depgraph`, `logigraph`, `install` don't exist yet. Add minimal stubs as part of this task so Step 4 passes:

Create `kg/cli/project.py`:
```python
def register(sub):
    p = sub.add_parser("project", help="Per-project config and registry.")
    p.set_defaults(func=lambda args: (print("kg project — not implemented yet"), 1)[1])
```

Create `kg/cli/depgraph.py`:
```python
def register(sub):
    p = sub.add_parser("depgraph", help="Code-graph operations.")
    p.set_defaults(func=lambda args, extra: 1, wants_extra=True)
```

Create `kg/cli/logigraph.py`:
```python
def register(sub):
    p = sub.add_parser("logigraph", help="Rules-graph operations.")
    p.set_defaults(func=lambda args, extra: 1, wants_extra=True)
```

Create `kg/cli/install.py`:
```python
def register(sub):
    p = sub.add_parser("install", help="Machine setup (tools, hooks, systemd, etc.).")
    p.set_defaults(func=lambda args, extra: 1, wants_extra=True)
```

- [ ] **Step 4: Run tests — back-compat must hold**

Run: `python3 -m pytest tests/kg/ -q`
Expected: All previously-passing tests still pass.

- [ ] **Step 5: Smoke test the new help surface**

Run: `KG_REGISTRY_PATH=/tmp/kg-test.toml bin/kg --help`
Expected output (groups listed):
```
positional arguments:
  {project,depgraph,logigraph,install,list,add,remove,hook}
```

- [ ] **Step 6: Commit**

```bash
git add kg/cli/__init__.py kg/cli/orchestrator.py kg/cli/project.py kg/cli/depgraph.py kg/cli/logigraph.py kg/cli/install.py
git commit -m "$(cat <<'EOF'
kg/cli: top-level dispatcher with 5 groups + back-compat aliases

Restructures kg/cli/__init__.py as a thin dispatcher that registers
five top-level groups (project, depgraph, logigraph, install, hook)
via per-group submodules' `register(sub)` functions.

The original kg list / add / remove / hook commands move into
kg.cli.orchestrator and are re-registered as top-level back-compat
aliases — bin/kg list still works.

Tasks 5-13 fill in the group submodule bodies; this commit ships
working stubs that route correctly but print "not implemented yet"
for the real groups.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: `kg project list / show / current / use`

**Files:**
- Modify: `kg/cli/project.py`
- Create: `tests/kg/test_cli_project.py`

- [ ] **Step 1: Write failing tests**

Create `tests/kg/test_cli_project.py`:

```python
"""Tests for kg project subcommand group."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

TOOL_ROOT = Path(__file__).resolve().parents[2]
KG_BIN = TOOL_ROOT / "bin" / "kg"


@pytest.fixture
def two_projects(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    """Register two projects with full data-dir layouts."""
    reg = tmp_path / "kg-graphs.toml"
    monkeypatch.setenv("KG_REGISTRY_PATH", str(reg))
    monkeypatch.delenv("KG_PROJECT", raising=False)
    monkeypatch.delenv("DEPGRAPH_DATA_DIR", raising=False)
    monkeypatch.delenv("LOGIGRAPH_DATA_DIR", raising=False)

    def make(name: str) -> Path:
        root = tmp_path / f"{name}-knowledge-graph"
        (root / "depgraph" / "nodes").mkdir(parents=True)
        (root / "logigraph" / "nodes").mkdir(parents=True)
        (root / "project.toml").write_text(
            f'[project]\nname = "{name}"\nsubsystems = ["depgraph", "logigraph"]\n'
        )
        (root / "depgraph" / "project.toml").write_text(
            f'[project]\nname = "{name}"\n'
        )
        (root / "logigraph" / "project.toml").write_text(
            f'[project]\nname = "{name}"\n'
        )
        return root

    a = make("alpha")
    b = make("beta")
    subprocess.run([sys.executable, str(KG_BIN), "project", "add", str(a)], check=True,
                   env={**os.environ, "KG_REGISTRY_PATH": str(reg)})
    subprocess.run([sys.executable, str(KG_BIN), "project", "add", str(b)], check=True,
                   env={**os.environ, "KG_REGISTRY_PATH": str(reg)})
    return {"alpha": a, "beta": b, "registry": reg, "tmp_path": tmp_path}


def _run(env_reg: Path, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "KG_REGISTRY_PATH": str(env_reg)}
    return subprocess.run(
        [sys.executable, str(KG_BIN), *args],
        capture_output=True, text=True, env=env, cwd=cwd,
    )


def test_list_shows_two_projects(two_projects: dict) -> None:
    res = _run(two_projects["registry"], "project", "list")
    assert res.returncode == 0
    assert "alpha" in res.stdout
    assert "beta" in res.stdout


def test_use_then_list_marks_default(two_projects: dict) -> None:
    _run(two_projects["registry"], "project", "use", "alpha")
    res = _run(two_projects["registry"], "project", "list")
    assert "* alpha" in res.stdout
    assert "  beta" in res.stdout  # 2-space prefix = not default


def test_use_clear_unsets_default(two_projects: dict) -> None:
    _run(two_projects["registry"], "project", "use", "alpha")
    res = _run(two_projects["registry"], "project", "use", "--clear")
    assert res.returncode == 0
    res = _run(two_projects["registry"], "project", "list")
    assert "* alpha" not in res.stdout


def test_use_unknown_project_errors(two_projects: dict) -> None:
    res = _run(two_projects["registry"], "project", "use", "ghost")
    assert res.returncode != 0
    assert "not registered" in res.stderr


def test_current_reports_source(two_projects: dict) -> None:
    _run(two_projects["registry"], "project", "use", "beta")
    res = _run(two_projects["registry"], "project", "current")
    assert "beta" in res.stdout
    assert "kg-graphs.toml default" in res.stdout


def test_show_prints_resolved_project(two_projects: dict) -> None:
    _run(two_projects["registry"], "project", "use", "alpha")
    res = _run(two_projects["registry"], "project", "show")
    assert res.returncode == 0
    assert "alpha" in res.stdout
    assert str(two_projects["alpha"]) in res.stdout


def test_show_named_project_overrides_default(two_projects: dict) -> None:
    _run(two_projects["registry"], "project", "use", "alpha")
    res = _run(two_projects["registry"], "project", "show", "beta")
    assert "beta" in res.stdout
    assert str(two_projects["beta"]) in res.stdout
```

- [ ] **Step 2: Run tests — expect failures**

Run: `python3 -m pytest tests/kg/test_cli_project.py -q`
Expected: 7 failures — `project --help` shows "not implemented yet"

- [ ] **Step 3: Implement `kg/cli/project.py`**

Replace the stub with:

```python
"""kg project — registry + per-project config commands.

Phase 1 verbs:
  list / show / current / use  ← this task
  add / remove / init           (Task 6)
  add-repo / list-repos / remove-repo (Task 7)
  set                          (Task 9)
  health                       (Task 10)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from kg import project as project_loader, registry
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
    # Surface repos if the project.toml has a depgraph configured.
    repos_toml = proj.depgraph_dir / "project.toml"
    if repos_toml.exists():
        import tomllib
        cfg = tomllib.loads(repos_toml.read_text())
        repos = cfg.get("repos") or {}
        if repos:
            print(f"  repos ({len(repos)}):")
            for key, val in repos.items():
                if isinstance(val, dict):
                    print(f"    {key:<20}  {val.get('path', '?')}")
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
```

- [ ] **Step 4: Run tests — expect pass**

Run: `python3 -m pytest tests/kg/test_cli_project.py -q -k "list or use or current or show"`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add kg/cli/project.py tests/kg/test_cli_project.py
git commit -m "$(cat <<'EOF'
kg project: list / show / current / use (incl. --clear)

First slice of the kg project group. Registry-only commands:

  kg project list          — registered projects, default marked *
  kg project show [name]   — resolved paths + repos summary
  kg project current       — active project + which resolution rule fired
  kg project use <name>    — persist default in kg-graphs.toml
  kg project use --clear   — unset default

list/use/show defer to kg.registry + kg.cli.resolve; no new TOML
writing here beyond registry.save_default.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: `kg project add / remove / init`

**Files:**
- Modify: `kg/cli/project.py`
- Modify: `tests/kg/test_cli_project.py`

- [ ] **Step 1: Add failing tests**

Append to `tests/kg/test_cli_project.py`:

```python
def test_add_registers_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    reg = tmp_path / "kg-graphs.toml"
    monkeypatch.setenv("KG_REGISTRY_PATH", str(reg))
    root = tmp_path / "new-knowledge-graph"
    (root / "depgraph" / "nodes").mkdir(parents=True)
    (root / "logigraph" / "nodes").mkdir(parents=True)
    (root / "project.toml").write_text(
        '[project]\nname = "new"\nsubsystems = ["depgraph", "logigraph"]\n'
    )
    res = _run(reg, "project", "add", str(root))
    assert res.returncode == 0
    list_res = _run(reg, "project", "list")
    assert "new" in list_res.stdout


def test_remove_unregisters(two_projects: dict) -> None:
    res = _run(two_projects["registry"], "project", "remove", "alpha")
    assert res.returncode == 0
    list_res = _run(two_projects["registry"], "project", "list")
    assert "alpha" not in list_res.stdout


def test_init_scaffolds_layout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    reg = tmp_path / "kg-graphs.toml"
    monkeypatch.setenv("KG_REGISTRY_PATH", str(reg))
    project_root = tmp_path / "fresh"
    res = _run(reg, "project", "init", str(project_root))
    assert res.returncode == 0
    assert (project_root / "knowledge-graph" / "depgraph" / "project.toml").exists()
    assert (project_root / "knowledge-graph" / "logigraph" / "project.toml").exists()
```

- [ ] **Step 2: Run tests — expect failures**

Run: `python3 -m pytest tests/kg/test_cli_project.py -q -k "add or remove or init"`
Expected: 3 failures (subcommands don't exist)

- [ ] **Step 3: Add handlers + registration**

In `kg/cli/project.py`, after `_cmd_show` add:

```python
def _cmd_add(args: argparse.Namespace) -> int:
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
    print(f"Registered '{entry.name}' at {entry.path}")
    return 0


def _cmd_remove(args: argparse.Namespace) -> int:
    if registry.remove(args.name):
        print(f"Removed '{args.name}'")
        return 0
    print(f"Error: '{args.name}' is not registered", file=sys.stderr)
    return 1


def _cmd_init(args: argparse.Namespace) -> int:
    """Phase 1: shell out to install.sh init <path>."""
    import subprocess
    tool_root = Path(__file__).resolve().parents[2]
    installer = tool_root / "install.sh"
    return subprocess.run([str(installer), "init", args.path]).returncode
```

In `register(sub)`, after the `p_show` block:

```python
    p_add = proj_sub.add_parser("add", help="Register a project's data dir with the orchestrator.")
    p_add.add_argument("path", help="Path to the project's knowledge-graph dir.")
    p_add.set_defaults(func=_cmd_add)

    p_remove = proj_sub.add_parser("remove", help="Unregister a project (does not delete on disk).")
    p_remove.add_argument("name")
    p_remove.set_defaults(func=_cmd_remove)

    p_init = proj_sub.add_parser("init", help="Scaffold a fresh project's data layout.")
    p_init.add_argument("path", help="Project root (knowledge-graph subdir will be created here).")
    p_init.set_defaults(func=_cmd_init)
```

- [ ] **Step 4: Run tests — expect pass**

Run: `python3 -m pytest tests/kg/test_cli_project.py -q`
Expected: All tests pass.

- [ ] **Step 5: Commit**

```bash
git add kg/cli/project.py tests/kg/test_cli_project.py
git commit -m "$(cat <<'EOF'
kg project: add / remove / init (registration + scaffolding)

  kg project add <path>     — register an existing data dir
  kg project remove <name>  — unregister
  kg project init <path>    — scaffold a fresh project layout

`add` and `remove` are wrappers around kg.registry. `init` shells out
to install.sh init for Phase 1 — Phase 4 ports the bash logic to
Python under kg.cli.install.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: `kg project add-repo / list-repos / remove-repo`

**Files:**
- Modify: `kg/cli/project.py`
- Modify: `tests/kg/test_cli_project.py`

Phase 1 strategy: shell out to `depgraph repo-add` / `repo-list` / `repo-remove`. The depgraph CLI already has `repo-add` and `repo-list` (added in commit `6231cb24`). `repo-remove` is added in Task 8.

- [ ] **Step 1: Append failing tests**

```python
def test_add_repo_via_kg_project_writes_subtable(two_projects: dict) -> None:
    # Make sure depgraph CLI finds the project — use --project flag.
    res = _run(
        two_projects["registry"], "project", "--project", "alpha",
        "add-repo", "api", str(two_projects["tmp_path"] / "fake-repo"),
    )
    assert res.returncode == 0, f"stderr: {res.stderr}"
    cfg_text = (two_projects["alpha"] / "depgraph" / "project.toml").read_text()
    assert "[repos.api]" in cfg_text
    assert "path = " in cfg_text


def test_list_repos_via_kg_project(two_projects: dict) -> None:
    _run(
        two_projects["registry"], "project", "--project", "alpha",
        "add-repo", "api", str(two_projects["tmp_path"] / "fake-repo"),
    )
    res = _run(two_projects["registry"], "project", "--project", "alpha", "list-repos")
    assert res.returncode == 0
    assert "api" in res.stdout


def test_remove_repo_via_kg_project(two_projects: dict) -> None:
    _run(
        two_projects["registry"], "project", "--project", "alpha",
        "add-repo", "api", str(two_projects["tmp_path"] / "fake-repo"),
    )
    res = _run(two_projects["registry"], "project", "--project", "alpha", "remove-repo", "api")
    assert res.returncode == 0
    cfg_text = (two_projects["alpha"] / "depgraph" / "project.toml").read_text()
    assert "[repos.api]" not in cfg_text
```

- [ ] **Step 2: Run tests — expect failures**

Run: `python3 -m pytest tests/kg/test_cli_project.py -q -k "repo"`
Expected: 3 failures.

- [ ] **Step 3: Add `--project` / `--data-dir` flags + repo handlers**

In `kg/cli/project.py`, **add a shared helper** at the top:

```python
def _delegate_to_depgraph(proj: resolve.Project, *args: str) -> int:
    """Run `depgraph <args>` against `proj`'s depgraph dir."""
    import os
    import subprocess
    tool_root = Path(__file__).resolve().parents[2]
    depgraph_bin = tool_root / "depgraph" / "bin" / "depgraph"
    env = {**os.environ, "DEPGRAPH_DATA_DIR": str(proj.depgraph_dir)}
    return subprocess.run([str(depgraph_bin), *args], env=env).returncode


def _resolved(args: argparse.Namespace) -> resolve.Project:
    """Resolve project from --project / --data-dir flags or fall through."""
    return resolve.resolve_project(
        project_name=getattr(args, "project", None),
        data_dir=Path(args.data_dir).expanduser() if getattr(args, "data_dir", None) else None,
    )
```

Add handlers:

```python
def _cmd_add_repo(args: argparse.Namespace) -> int:
    try:
        proj = _resolved(args)
    except resolve.ProjectResolutionError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    cli_args = ["repo-add", args.key, args.path]
    for tok in args.extractor or []:
        cli_args.extend(["--extractor", *args.extractor])
        break
    for det in args.detector or []:
        cli_args.extend(["--detector", det])
    if args.files_arg:
        cli_args.append(f"--files-arg={args.files_arg}")
    if args.force:
        cli_args.append("--force")
    return _delegate_to_depgraph(proj, *cli_args)


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
    return _delegate_to_depgraph(proj, "repo-remove", args.key)
```

Modify the existing `register(sub)` to add a `--project` / `--data-dir` group at the `kg project` level:

```python
def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("project", help="Per-project config and registry.")
    p.add_argument("--project", help="Project name (overrides env/cwd/default).")
    p.add_argument("--data-dir", help="Project data dir path (escape hatch for unregistered).")
    proj_sub = p.add_subparsers(dest="project_cmd", required=True)
    # ... existing list/use/current/show/add/remove/init registrations unchanged ...
```

Then add the repo subcommands inside `register`:

```python
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
```

- [ ] **Step 4: Run tests — expect 1 still failing (remove-repo needs Task 8)**

Run: `python3 -m pytest tests/kg/test_cli_project.py -q -k "repo"`
Expected: `add-repo` and `list-repos` pass; `remove-repo` fails because `depgraph repo-remove` doesn't exist yet.

- [ ] **Step 5: Commit (partial — Task 8 completes the triple)**

```bash
git add kg/cli/project.py tests/kg/test_cli_project.py
git commit -m "$(cat <<'EOF'
kg project: add-repo / list-repos / remove-repo + --project flag

Delegates to `depgraph repo-add` / `repo-list` / `repo-remove` via
subprocess, setting DEPGRAPH_DATA_DIR from the resolved project.

`--project <name>` and `--data-dir <path>` flags on `kg project` let
users target a non-default project without `cd`-ing or setting env.

remove-repo's test still fails — depgraph CLI doesn't have repo-remove
yet. Task 8 adds it.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: `depgraph repo-remove` subcommand

**Files:**
- Modify: `depgraph/bin/depgraph`
- Modify: `tests/kg/test_cli_project.py` (the failing test should now pass)

- [ ] **Step 1: Add `cmd_repo_remove` handler in `depgraph/bin/depgraph`**

Insert this function right after `cmd_repo_list`:

```python
def cmd_repo_remove(args: argparse.Namespace) -> int:
    cfg_path = DEPGRAPH / "project.toml"
    if not cfg_path.exists():
        print(f"no project.toml at {cfg_path}", file=sys.stderr)
        return 1
    repos = project_repos(DEPGRAPH)
    if args.key not in repos:
        print(f"[repos.{args.key}] not found in {cfg_path}", file=sys.stderr)
        return 1
    text = cfg_path.read_text()
    text = _strip_existing_repo_block(text, args.key).rstrip() + "\n"
    cfg_path.write_text(text)
    print(f"removed [repos.{args.key}] from {cfg_path}")
    return 0
```

- [ ] **Step 2: Register the subcommand**

Locate the `p_rlist = sub.add_parser("repo-list", ...)` block and add right after it:

```python
    p_rrm = sub.add_parser("repo-remove", help="Remove a [repos.<key>] entry from project.toml")
    p_rrm.add_argument("key", help="Repo key to remove")
    p_rrm.set_defaults(func=cmd_repo_remove)
```

- [ ] **Step 3: Smoke-test the new subcommand**

```bash
SBOX=$(mktemp -d) && mkdir -p "$SBOX/nodes" && cat > "$SBOX/project.toml" <<'EOF'
[project]
name = "sb"

[repos.api]
path = "~/foo"
EOF
DEPGRAPH_DATA_DIR="$SBOX" depgraph/bin/depgraph repo-remove api
cat "$SBOX/project.toml"
rm -rf "$SBOX"
```

Expected: `[repos.api]` block is gone from the printed output; only `[project]` remains.

- [ ] **Step 4: Run the previously-failing test — expect pass**

Run: `python3 -m pytest tests/kg/test_cli_project.py -q -k remove_repo`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add depgraph/bin/depgraph
git commit -m "$(cat <<'EOF'
depgraph: repo-remove subcommand

Completes the repo-add/list/remove triple. Strips a [repos.<key>]
table from <DEPGRAPH>/project.toml via the same regex helper that
--force replace uses.

Required by `kg project remove-repo` (Task 7 in the Phase 1 plan).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: `kg project set <field> <value>`

**Files:**
- Modify: `kg/cli/project.py`
- Modify: `tests/kg/test_cli_project.py`

Whitelisted fields: `primary_repo`, `logigraph.data_dir`, `memory.dir`. Other fields rejected to prevent users from breaking schema.

- [ ] **Step 1: Add failing tests**

```python
def test_set_primary_repo(two_projects: dict) -> None:
    # Add a repo first so primary_repo has a valid target.
    _run(
        two_projects["registry"], "project", "--project", "alpha",
        "add-repo", "api", str(two_projects["tmp_path"] / "fake"),
    )
    res = _run(
        two_projects["registry"], "project", "--project", "alpha",
        "set", "primary_repo", "api",
    )
    assert res.returncode == 0
    cfg = (two_projects["alpha"] / "depgraph" / "project.toml").read_text()
    assert 'primary_repo = "api"' in cfg


def test_set_rejects_non_whitelist_field(two_projects: dict) -> None:
    res = _run(
        two_projects["registry"], "project", "--project", "alpha",
        "set", "wild_field", "value",
    )
    assert res.returncode != 0
    assert "not in whitelist" in res.stderr.lower()


def test_set_primary_repo_rejects_unknown_key(two_projects: dict) -> None:
    res = _run(
        two_projects["registry"], "project", "--project", "alpha",
        "set", "primary_repo", "missing-key",
    )
    assert res.returncode != 0
```

- [ ] **Step 2: Run tests — expect failures**

Run: `python3 -m pytest tests/kg/test_cli_project.py -q -k set`
Expected: 3 failures.

- [ ] **Step 3: Implement `_cmd_set`**

```python
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
        import tomllib
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
    """Idempotently set [section] key = "value" in cfg_path. Preserves other content."""
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

    # Find the section and check whether the key already exists in it.
    # Section body = lines from the header up to the next top-level [ or EOF.
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
        new_body = body.rstrip() + ("\n" if body.rstrip() else "") + new_line + "\n"
    text = text[: m.start(2)] + new_body + text[m.end(2):]
    cfg_path.write_text(text)
```

Register it:

```python
    p_set = proj_sub.add_parser(
        "set",
        help=f"Set a project.toml field. Whitelisted: {', '.join(sorted(_SET_WHITELIST))}.",
    )
    p_set.add_argument("field")
    p_set.add_argument("value")
    p_set.set_defaults(func=_cmd_set)
```

- [ ] **Step 4: Run tests — expect pass**

Run: `python3 -m pytest tests/kg/test_cli_project.py -q -k set`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add kg/cli/project.py tests/kg/test_cli_project.py
git commit -m "$(cat <<'EOF'
kg project: set <field> <value> with whitelist

Generic project.toml mutator with a whitelist:
  - primary_repo            ([project] primary_repo)
  - logigraph.data_dir      ([logigraph] data_dir)
  - memory.dir              ([memory] dir)

primary_repo additionally validates that the named repo has a
[repos.<key>] table — prevents setting a primary that doesn't
exist.

Writes are idempotent text edits (TOML stdlib is read-only).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: `kg project health`

**Files:**
- Modify: `kg/cli/project.py`
- Modify: `tests/kg/test_cli_project.py`

Composes `depgraph health` + `logigraph health` + per-repo path-exists checks. Exits non-zero if any subsystem health fails.

- [ ] **Step 1: Add failing test**

```python
def test_health_runs_subsystem_checks(two_projects: dict) -> None:
    res = _run(two_projects["registry"], "project", "--project", "alpha", "health")
    # Exit code is allowed to be 0 or 1 depending on whether subsystems are
    # populated — but the output must mention both subsystems.
    out = res.stdout + res.stderr
    assert "depgraph" in out.lower()
    assert "logigraph" in out.lower()
```

- [ ] **Step 2: Run — expect failure**

Run: `python3 -m pytest tests/kg/test_cli_project.py -q -k health`
Expected: 1 failure.

- [ ] **Step 3: Implement `_cmd_health`**

```python
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
```

Register:

```python
    p_health = proj_sub.add_parser("health", help="Cross-subsystem health (depgraph + logigraph + repo paths).")
    p_health.set_defaults(func=_cmd_health)
```

- [ ] **Step 4: Run — expect pass**

Run: `python3 -m pytest tests/kg/test_cli_project.py -q -k health`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add kg/cli/project.py tests/kg/test_cli_project.py
git commit -m "$(cat <<'EOF'
kg project: health — cross-subsystem one-shot

Runs depgraph health + logigraph health + per-repo path-exists checks
against the resolved project, prints a sectioned report, and exits
non-zero if any subsystem fails.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 11: `kg depgraph` — subprocess shim

**Files:**
- Modify: `kg/cli/depgraph.py`
- Create: `tests/kg/test_cli_subprocess_shims.py`

Strategy: `kg depgraph <argv>` → resolve project, then `os.execvpe(depgraph_bin, [depgraph_bin, *argv], env_with_DEPGRAPH_DATA_DIR)`. `os.execvpe` replaces the current process so the user sees identical output and signals.

- [ ] **Step 1: Create shim smoke-tests**

```python
"""Smoke tests for kg's subprocess shims to depgraph / logigraph / install.sh."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

TOOL_ROOT = Path(__file__).resolve().parents[2]
KG_BIN = TOOL_ROOT / "bin" / "kg"


@pytest.fixture
def single_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    reg = tmp_path / "kg-graphs.toml"
    monkeypatch.setenv("KG_REGISTRY_PATH", str(reg))
    root = tmp_path / "solo-knowledge-graph"
    (root / "depgraph" / "nodes").mkdir(parents=True)
    (root / "logigraph" / "nodes").mkdir(parents=True)
    (root / "project.toml").write_text(
        '[project]\nname = "solo"\nsubsystems = ["depgraph", "logigraph"]\n'
    )
    (root / "depgraph" / "project.toml").write_text('[project]\nname = "solo"\n')
    (root / "logigraph" / "project.toml").write_text('[project]\nname = "solo"\n')
    subprocess.run(
        [sys.executable, str(KG_BIN), "project", "add", str(root)],
        check=True, env={**os.environ, "KG_REGISTRY_PATH": str(reg)},
    )
    return {"root": root, "registry": reg}


def _run(env_reg: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KG_BIN), *args],
        capture_output=True, text=True,
        env={**os.environ, "KG_REGISTRY_PATH": str(env_reg)},
    )


def test_kg_depgraph_help_reaches_depgraph(single_project: dict) -> None:
    res = _run(single_project["registry"], "depgraph", "--help")
    assert res.returncode == 0
    # depgraph's --help mentions a subcommand we know exists.
    assert "regen" in res.stdout


def test_kg_depgraph_validate_runs_against_resolved_project(single_project: dict) -> None:
    res = _run(single_project["registry"], "depgraph", "validate")
    # Validate on an empty graph should succeed with no errors.
    assert res.returncode == 0, f"stderr: {res.stderr}"


def test_kg_logigraph_help_reaches_logigraph(single_project: dict) -> None:
    res = _run(single_project["registry"], "logigraph", "--help")
    assert res.returncode == 0
    assert "regen" in res.stdout


def test_kg_install_help_reaches_install_sh(single_project: dict) -> None:
    res = _run(single_project["registry"], "install", "--help")
    assert res.returncode == 0
    # install.sh --help mentions a known subcommand.
    assert "bootstrap" in res.stdout or "systemd" in res.stdout
```

- [ ] **Step 2: Run — expect failures**

Run: `python3 -m pytest tests/kg/test_cli_subprocess_shims.py -q`
Expected: 4 failures (shims return 1 + no output).

- [ ] **Step 3: Implement `kg/cli/depgraph.py`**

Replace the stub:

```python
"""kg depgraph — subprocess shim into the depgraph CLI.

Phase 1: resolves a project, exports DEPGRAPH_DATA_DIR, then execs
the existing depgraph binary with the remaining argv. The user sees
identical output and signals.

Phase 2 replaces this with native subcommand registration that imports
from depgraph.lib.cli.* modules.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from kg.cli import resolve


def _run_depgraph(args: argparse.Namespace, extra: list[str]) -> int:
    try:
        proj = resolve.resolve_project(
            project_name=getattr(args, "project", None),
            data_dir=Path(args.data_dir).expanduser() if getattr(args, "data_dir", None) else None,
        )
    except resolve.ProjectResolutionError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    tool_root = Path(__file__).resolve().parents[2]
    depgraph_bin = tool_root / "depgraph" / "bin" / "depgraph"
    env = {**os.environ, "DEPGRAPH_DATA_DIR": str(proj.depgraph_dir)}
    # Use os.execvpe so signals (Ctrl-C, etc.) and exit codes are transparent.
    os.execvpe(str(depgraph_bin), [str(depgraph_bin), *extra], env)


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "depgraph",
        help="Code-graph operations (regen, dependents, dossiers, ...).",
        add_help=False,  # let depgraph CLI handle --help so it reaches the actual command tree
    )
    p.add_argument("--project", help="Project name (overrides env/cwd/default).")
    p.add_argument("--data-dir", help="Depgraph data dir path.")
    p.set_defaults(func=_run_depgraph, wants_extra=True)
```

- [ ] **Step 4: Run — expect 2 of 4 pass** (depgraph + validate; logigraph and install fail until Tasks 12-13)

Run: `python3 -m pytest tests/kg/test_cli_subprocess_shims.py -q -k depgraph`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add kg/cli/depgraph.py tests/kg/test_cli_subprocess_shims.py
git commit -m "$(cat <<'EOF'
kg depgraph: subprocess shim into the depgraph CLI

`kg depgraph <argv>` resolves the project from --project / --data-dir /
env / cwd / default, exports DEPGRAPH_DATA_DIR, then execs the existing
depgraph binary via os.execvpe so signals + exit codes pass through.

Argparse uses add_help=False on the kg depgraph subparser so --help
falls through to the actual depgraph CLI's subcommand tree instead of
being intercepted at the kg layer.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 12: `kg logigraph` — subprocess shim

**Files:**
- Modify: `kg/cli/logigraph.py`

Identical pattern to Task 11.

- [ ] **Step 1: Implement**

Replace the stub in `kg/cli/logigraph.py`:

```python
"""kg logigraph — subprocess shim into the logigraph CLI.

Phase 1: resolves a project, exports LOGIGRAPH_DATA_DIR, then execs the
existing logigraph binary with the remaining argv.

Phase 3 replaces this with native subcommand registration that imports
from logigraph.lib.cli.* modules.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from kg.cli import resolve


def _run_logigraph(args: argparse.Namespace, extra: list[str]) -> int:
    try:
        proj = resolve.resolve_project(
            project_name=getattr(args, "project", None),
            data_dir=Path(args.data_dir).expanduser() if getattr(args, "data_dir", None) else None,
        )
    except resolve.ProjectResolutionError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    tool_root = Path(__file__).resolve().parents[2]
    logi_bin = tool_root / "logigraph" / "bin" / "logigraph"
    env = {**os.environ, "LOGIGRAPH_DATA_DIR": str(proj.logigraph_dir)}
    os.execvpe(str(logi_bin), [str(logi_bin), *extra], env)


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "logigraph",
        help="Rules-graph operations (regen, rules-for, rule/process/domain lifecycle, ...).",
        add_help=False,
    )
    p.add_argument("--project")
    p.add_argument("--data-dir")
    p.set_defaults(func=_run_logigraph, wants_extra=True)
```

- [ ] **Step 2: Run — expect pass**

Run: `python3 -m pytest tests/kg/test_cli_subprocess_shims.py -q -k logigraph`
Expected: 1 passed.

- [ ] **Step 3: Commit**

```bash
git add kg/cli/logigraph.py
git commit -m "$(cat <<'EOF'
kg logigraph: subprocess shim into the logigraph CLI

Mirrors kg.cli.depgraph: resolve project, export LOGIGRAPH_DATA_DIR,
os.execvpe the existing logigraph binary.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 13: `kg install` — subprocess shim into `install.sh`

**Files:**
- Modify: `kg/cli/install.py`

Same pattern but no DEPGRAPH/LOGIGRAPH env injection — install.sh takes a `--project <dir>` arg.

- [ ] **Step 1: Implement**

Replace the stub:

```python
"""kg install — subprocess shim into install.sh.

Phase 1: forwards argv to install.sh (which lives next to the kg/
package). install.sh handles --project / --apply / --target itself,
so kg.cli.install does no project resolution — it's a transparent
wrapper that unifies the help surface.

Phase 4 ports install.sh's logic to Python under this module.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path


def _run_installer(args: argparse.Namespace, extra: list[str]) -> int:
    tool_root = Path(__file__).resolve().parents[2]
    installer = tool_root / "install.sh"
    os.execvpe(str(installer), [str(installer), *extra], os.environ.copy())


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "install",
        help="Machine setup: tools, hooks, systemd, PATH, cascade, bootstrap.",
        add_help=False,
    )
    p.set_defaults(func=_run_installer, wants_extra=True)
```

- [ ] **Step 2: Run — expect pass**

Run: `python3 -m pytest tests/kg/test_cli_subprocess_shims.py -q`
Expected: All 4 pass.

- [ ] **Step 3: Commit**

```bash
git add kg/cli/install.py
git commit -m "$(cat <<'EOF'
kg install: subprocess shim into install.sh

Transparent wrapper: `kg install <args>` execs install.sh with the
remaining argv. install.sh handles its own --project / --apply /
--target parsing.

Phase 4 ports install.sh to Python under this module.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 14: `docs/CLI.md`

**Files:**
- Create: `docs/CLI.md`

- [ ] **Step 1: Write the doc**

Create `docs/CLI.md`:

```markdown
# `kg` CLI reference

Single entry point for the knowledge-graph framework. Five groups
under `kg`; legacy `depgraph` / `logigraph` / `install.sh` scripts
still work and behave identically.

## Quick start

    kg project add ~/my-project-knowledge-graph    # register
    kg project use my-project                       # set as default
    kg depgraph regen                               # now uses the default

## Project resolution

Every command picks a project via this 7-step order (first match wins):

1. `--project <name>` or `--data-dir <path>` flag
2. `$KG_PROJECT` env var
3. `$DEPGRAPH_DATA_DIR` / `$LOGIGRAPH_DATA_DIR` env var (hook compat)
4. cwd-ancestor walk for `project.toml` + `nodes/`
5. `default = "..."` in `~/.claude/kg-graphs.toml`
6. The only registered project (implicit)
7. Error — lists registered projects + the right `--project` flag

`kg project current` prints the active project and which rule fired.

## Commands

### `kg project` — registry + per-project config

| Command | Description |
|---|---|
| `kg project list` | List registered projects (default marked `*`) |
| `kg project show [<name>]` | Inspect a project (defaults to current) |
| `kg project current` | Print active project + how it was resolved |
| `kg project use <name>` | Set persistent default in `kg-graphs.toml` |
| `kg project use --clear` | Unset the default |
| `kg project add <path>` | Register a data dir with the orchestrator |
| `kg project remove <name>` | Unregister (does not delete on disk) |
| `kg project init <path>` | Scaffold a fresh project layout |
| `kg project add-repo <key> <path> [--extractor ... --detector ... --files-arg=... --force]` | Add a `[repos.<key>]` entry |
| `kg project list-repos` | List configured repos |
| `kg project remove-repo <key>` | Remove a `[repos.<key>]` entry |
| `kg project set <field> <value>` | Set a whitelisted project.toml field |
| `kg project health` | Cross-subsystem health (depgraph + logigraph + repo paths) |

#### `kg project set` — whitelisted fields

- `primary_repo` — `[project] primary_repo`. Validated against `[repos.*]` keys.
- `logigraph.data_dir` — `[logigraph] data_dir`. Cross-graph pointer.
- `memory.dir` — `[memory] dir`. Where memory-sync mirrors `~/.claude` files.

### `kg depgraph` — code-graph operations

`kg depgraph <subcommand>` resolves a project, exports
`DEPGRAPH_DATA_DIR`, and runs the existing depgraph CLI. Pass
`--project <name>` or `--data-dir <path>` for non-default targets.

Subcommands: `regen`, `validate`, `health`, `self-check`, `stats`,
`context`, `dependents`, `orphans`, `commit-summary`, `memory-sync`,
`dossier-rank`, `dossier-draft`, `dossier-finalize`, `dossier-bump`,
`flag`, `unflag`, `repo-add`, `repo-list`, `repo-remove`.

See `kg depgraph <cmd> --help` for full options.

### `kg logigraph` — rules-graph operations

Same shim pattern as `kg depgraph`, with `LOGIGRAPH_DATA_DIR` set.

Subcommands: `regen`, `validate`, `health`, `self-check`, `stats`,
`context`, `rules-for`, `fan-out`, `gaps`, `rollup`, `dossiers`,
`rule-rank`, `rule-draft`, `rule-finalize`, `rule-bump`, `rule-stub`,
`process-rank`, `process-draft`, `process-finalize`, `process-bump`,
`process-stub`, `domain-bump`, `flag`, `unflag`.

### `kg install` — machine setup

Forwards argv to `install.sh`. Subcommands: `tools`, `hooks`,
`systemd`, `path`, `cascade`, `bootstrap`. See `kg install --help`.

### `kg hook <phase>`

Invoked by Claude Code via `~/.claude/settings.json`, not by humans.
Phases: `pre-edit`, `post-edit`, `session-start`, `session-end`,
`pre-irreversible`.

## Migration table

| Old command | New canonical |
|---|---|
| `kg list` | `kg project list` |
| `kg add <path>` | `kg project add <path>` |
| `kg remove <name>` | `kg project remove <name>` |
| `depgraph regen` | `kg depgraph regen` (or unchanged) |
| `logigraph rules-for X` | `kg logigraph rules-for X` (or unchanged) |
| `install.sh init <dir>` | `kg project init <dir>` (or `kg install ...`) |

Legacy `kg list` / `depgraph regen` / `install.sh init` keep working
as aliases — no migration required for muscle memory.

## Common errors

**"Multiple projects registered — pick one with --project"** — set a
default once: `kg project use <name>`.

**"Project not registered"** — list available: `kg project list`,
then `kg project add <path>` if missing.

**`argparse` error on `--files-arg --only`** — use `=` syntax:
`--files-arg=--only`. Argparse can't distinguish a value starting with
`--` from a flag.

## File locations

- Registry: `~/.claude/kg-graphs.toml` (machine-maintained, manual edits tolerated)
- Tools: `~/tools/knowledge-graph/{kg,depgraph,logigraph,graphui,install.sh}`
- Per-project data: `<project>/knowledge-graph/{depgraph,logigraph}/` (or the sibling-with-hyphen layout `<project>-knowledge-graph/`)
```

- [ ] **Step 2: Commit**

```bash
git add docs/CLI.md
git commit -m "$(cat <<'EOF'
docs: CLI.md — single-page reference for the consolidated kg CLI

Full command tree, project-resolution rules, migration table from
legacy command names, and common errors (the --files-arg=--only
argparse gotcha makes the cut).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 15: Memory entry `reference_kg_cli.md`

**Files:**
- Create: `/home/lgreenlee/.claude/projects/-home-lgreenlee/memory/reference_kg_cli.md`
- Modify: `/home/lgreenlee/.claude/projects/-home-lgreenlee/memory/MEMORY.md`

- [ ] **Step 1: Write the memory file**

Write to `/home/lgreenlee/.claude/projects/-home-lgreenlee/memory/reference_kg_cli.md`:

```markdown
---
name: reference-kg-cli
description: kg-framework's consolidated CLI — group structure, project resolution order, gotchas. Source of truth lives in ~/tools/knowledge-graph/docs/CLI.md.
metadata:
  type: reference
---

The kg framework collapsed 4 CLIs (kg, depgraph, logigraph, install.sh)
into one entry point with five groups. Source of truth: `~/tools/knowledge-graph/docs/CLI.md` (read it before recommending specific commands — names may evolve).

**Groups under `kg`:**
- `kg project` — registry + per-project config (`list / show / current / use / add / remove / init / add-repo / list-repos / remove-repo / set / health`)
- `kg depgraph` — code graph (subprocess shim to depgraph CLI in Phase 1)
- `kg logigraph` — rules graph (subprocess shim in Phase 1)
- `kg install` — machine setup (subprocess shim to install.sh)
- `kg hook` — Claude Code dispatcher (called by settings.json)

**Project resolution (every subsystem cmd runs this first):**
1. `--project <name>` / `--data-dir <path>` flag
2. `$KG_PROJECT` env var
3. `$DEPGRAPH_DATA_DIR` / `$LOGIGRAPH_DATA_DIR` (hook compat)
4. cwd-ancestor walk (`project.toml` + `nodes/`)
5. `default = "..."` in `~/.claude/kg-graphs.toml`
6. Single registered project (implicit)
7. Error with list

**Common recall hooks:**
- "Where are repos managed?" → `kg project add-repo / list-repos / remove-repo`
- "How do I switch project?" → `kg project use <name>` (persistent) or `--project <name>` (one-off)
- "Which project is active?" → `kg project current`
- "How do I see all projects?" → `kg project list` (default marked `*`)

**Gotchas:**
- `--files-arg --only` fails in argparse (parses `--only` as a flag). Use `--files-arg=--only`.
- Legacy `depgraph regen` / `logigraph regen` / `install.sh init` still work — they're aliases, not deprecated.
- `kg hook` is invoked BY Claude Code via settings.json. Don't run it manually.

**Related:** [[reference-depgraph]], [[reference-logigraph]], [[reference-kg-orchestrator]]
```

- [ ] **Step 2: Add the pointer in MEMORY.md**

Append one line to `/home/lgreenlee/.claude/projects/-home-lgreenlee/memory/MEMORY.md`:

```
- [Consolidated kg CLI](reference_kg_cli.md) — 5 groups + 7-step project resolver; see ~/tools/knowledge-graph/docs/CLI.md for source of truth
```

- [ ] **Step 3: Verify memory loads correctly next session**

(This step is implicit — the auto-memory system loads on session start. No verification command.)

---

## Task 16: Final verification

- [ ] **Step 1: Full test suite**

Run: `python3 -m pytest tests/kg/ -q`
Expected: All tests pass (existing 45 + new ~30 = ~75 total).

- [ ] **Step 2: Manual smoke tests**

```bash
# Help surface
KG_REGISTRY_PATH=/tmp/kg-smoke.toml bin/kg --help
KG_REGISTRY_PATH=/tmp/kg-smoke.toml bin/kg project --help

# End-to-end against live concorda
bin/kg project list
bin/kg project use concorda
bin/kg project current
bin/kg project list-repos
bin/kg depgraph health
bin/kg logigraph health
bin/kg project health

# Back-compat: legacy CLIs unchanged
depgraph health  # equivalent to `bin/kg depgraph health` with same DEPGRAPH_DATA_DIR
```

Expected output: project list shows `* concorda` after `use`; `current` reports "kg-graphs.toml default"; subsystem healths report cleanly; legacy `depgraph health` matches `kg depgraph health` byte-for-byte.

- [ ] **Step 3: Diff legacy vs kg output**

```bash
diff <(DEPGRAPH_DATA_DIR=/home/lgreenlee/concorda-knowledge-graph/depgraph depgraph health 2>&1) \
     <(bin/kg depgraph --project concorda health 2>&1)
```

Expected: identical output (empty diff).

- [ ] **Step 4: Commit the memory pointer (if anything's untracked in repo)**

```bash
cd ~/tools/knowledge-graph && git status --short
```

Expected: clean working tree. All previous tasks committed.

---

## Self-review

**Spec coverage check** (this plan vs `2026-05-15-kg-cli-consolidation-design.md`):

- Top-level shape (5 groups + back-compat aliases) → Task 4 ✓
- `kg project` 13 commands → Tasks 5–10 ✓
- Project resolver 7-step order → Task 3 ✓
- `default` key in kg-graphs.toml → Task 2 ✓
- `kg depgraph` / `kg logigraph` / `kg install` subprocess shims → Tasks 11–13 ✓
- `kg hook` unchanged → no task needed ✓
- `depgraph repo-remove` (gap I noticed during planning) → Task 8 ✓
- `docs/CLI.md` → Task 14 ✓
- Memory entry → Task 15 ✓
- Smoke tests for shims (diff `kg depgraph X` vs `depgraph X`) → Task 16 step 3 ✓

**Placeholder scan:** no `TBD`, `TODO`, "handle edge cases", or "similar to Task N" — every code block is concrete.

**Type consistency:** `Project` dataclass fields (`name`, `data_dir`, `depgraph_dir`, `logigraph_dir`, `source`) referenced identically across resolve.py and project.py. `_resolved(args)` signature consistent in project.py helpers. `register(sub)` signature uniform across kg.cli.{project,depgraph,logigraph,install,orchestrator}.

**Scope check:** 16 tasks; each is a single commit. Phase 1 only. Phases 2–5 will get their own design+plan when scheduled.
