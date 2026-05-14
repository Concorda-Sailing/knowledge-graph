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


def save(entries: list[GraphEntry]) -> None:
    """Write ``entries`` to the registry path, replacing any prior content.

    Creates the parent directory if it does not exist.
    """
    p = path()
    p.parent.mkdir(parents=True, exist_ok=True)
    body = _HEADER
    for e in entries:
        body += "[[graph]]\n"
        body += f'name = "{e.name}"\n'
        body += f'path = "{e.path}"\n'
        body += "\n"
    p.write_text(body)


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
    """Remove a graph by name. Returns True if removed, False if not present."""
    entries = load()
    keep = [e for e in entries if e.name != name]
    if len(keep) == len(entries):
        return False
    save(keep)
    return True


def find(name: str) -> Optional[GraphEntry]:
    """Return the entry with the given name, or None."""
    for e in load():
        if e.name == name:
            return e
    return None
