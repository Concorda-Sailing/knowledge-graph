"""Registry of knowledge-graph repos installed on this machine.

The registry lives at ``~/.claude/kg-graphs.toml`` (overridable via
``KG_REGISTRY_PATH`` for tests). It is plain TOML, machine-maintained by
``kg add`` / ``kg remove``. The file header tells a human reader where it
lives and why; manual edits are tolerated but not the documented path.

Format on disk::

    # Managed by `kg add` and `kg remove`.
    # Lives in ~/.claude/ because Claude Code hooks consume it.

    [[graph]]
    name = "example"
    path = "/home/user/projects/example-knowledge-graph"

Paths may be written with ``~``; ``load()`` always returns absolute,
resolved paths.
"""
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


DEFAULT_REGISTRY = Path.home() / ".claude" / "kg-graphs.toml"

_SENTINEL = object()  # marker for "argument not supplied" in save()

_HEADER = (
    "# Managed by `kg add` and `kg remove`.\n"
    "# Lives in ~/.claude/ because Claude Code hooks consume it.\n"
    "# Manual edits are allowed but `kg` is the documented interface.\n"
    "\n"
)


@dataclass(frozen=True)
class GraphEntry:
    """One row in the registry."""

    name: str
    path: Path  # absolute, resolved


def path() -> Path:
    """Return the registry path, honoring ``KG_REGISTRY_PATH``."""
    override = os.environ.get("KG_REGISTRY_PATH")
    if override:
        return Path(override).expanduser()
    return DEFAULT_REGISTRY


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
        if find(val) is not None:
            return val
    return None


def load() -> list[GraphEntry]:
    """Read the registry. Returns ``[]`` if the file is missing."""
    p = path()
    if not p.exists():
        return []
    data = tomllib.loads(p.read_text())
    entries: list[GraphEntry] = []
    for row in data.get("graph", []) or []:
        name = row.get("name")
        raw_path = row.get("path")
        if not name or not raw_path:
            continue
        entries.append(
            GraphEntry(name=name, path=Path(raw_path).expanduser().resolve())
        )
    return entries


def save(entries: list[GraphEntry], *, default=_SENTINEL) -> None:
    """Write entries (and optionally the default) to the registry path.

    `default` semantics:
      - omitted / _SENTINEL: preserve the existing default key (if any).
      - None: explicitly clear the default key.
      - str: set the default to this name.
    """
    p = path()
    p.parent.mkdir(parents=True, exist_ok=True)

    if default is _SENTINEL:
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


def add(*, name: str, path: Path) -> GraphEntry:
    """Register a graph. Raises if the path is missing or the name is taken."""
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Graph path does not exist: {resolved}")
    entries = load()
    if any(e.name == name for e in entries):
        raise ValueError(f"Graph name already registered: {name!r}")
    new_entry = GraphEntry(name=name, path=resolved)
    entries.append(new_entry)
    save(entries)
    return new_entry


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


def find(name: str) -> Optional[GraphEntry]:
    """Return the entry with the given name, or None."""
    for e in load():
        if e.name == name:
            return e
    return None
