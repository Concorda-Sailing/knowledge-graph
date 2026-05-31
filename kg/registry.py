"""Registry of knowledge-graph repos installed on this machine.

The registry is looked up in this order (first match wins):
  1. $KG_REGISTRY_PATH (explicit override)
  2. ~/.grok/kg-graphs.toml   — when ~/.grok/ exists or running under Grok
  3. ~/.claude/kg-graphs.toml — Claude Code + Grok compatibility fallback

It is plain TOML, machine-maintained by ``kg add`` / ``kg remove``.
Manual edits are tolerated but `kg` (and `kg project`) are the documented interface.

Format on disk::

    # Managed by `kg add` and `kg remove`.
    # Lives in ~/.grok/kg-graphs.toml (or ~/.claude/ for legacy installs).

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


# Preferred registry locations (checked in order).
_GROK_REGISTRY = Path.home() / ".grok" / "kg-graphs.toml"
_CLAUDE_REGISTRY = Path.home() / ".claude" / "kg-graphs.toml"

DEFAULT_REGISTRY = _CLAUDE_REGISTRY  # legacy name for tests / external readers

_SENTINEL = object()  # marker for "argument not supplied" in save()


def _effective_registry_path() -> Path:
    """Return the registry file to use on this machine.

    Resolution order:
    1. $KG_REGISTRY_PATH (explicit override, for tests and advanced use)
    2. ~/.grok/kg-graphs.toml if the ~/.grok dir exists or GROK_* env vars are set
    3. ~/.claude/kg-graphs.toml (Claude Code + Grok compatibility layer)
    4. Fall back to creating the Grok location when neither exists and ~/.grok is present.
    """
    override = os.environ.get("KG_REGISTRY_PATH")
    if override:
        return Path(override).expanduser()

    # Resolve all candidates from the *current* home so the result honors a
    # runtime $HOME (tests, and any env that relocates home). The module-level
    # _GROK_REGISTRY / _CLAUDE_REGISTRY constants remain the import-time export
    # (DEFAULT_REGISTRY) for external readers.
    home = Path.home()
    grok_registry = home / ".grok" / "kg-graphs.toml"
    claude_registry = home / ".claude" / "kg-graphs.toml"
    grok_exists = (home / ".grok").exists()
    is_grok_session = bool(os.environ.get("GROK_SESSION_ID") or os.environ.get("GROK_HOOK_EVENT"))

    if grok_exists or is_grok_session:
        # Prefer the Grok-native location when the user has a Grok environment,
        # but don't orphan an existing Claude registry: only switch to Grok if
        # it already holds the registry, or Claude has none yet.
        if grok_registry.exists():
            return grok_registry
        if not claude_registry.exists():
            return grok_registry

    # Default / backward-compat: Claude location (Grok also reads ~/.claude/settings.json)
    return claude_registry


def _registry_header() -> str:
    p = _effective_registry_path()
    loc = f"~/{p.relative_to(Path.home())}" if p.is_relative_to(Path.home()) else str(p)
    return (
        "# Managed by `kg add` and `kg remove`.\n"
        f"# Lives in {loc}.\n"
        "# Both Claude Code and Grok read this file (Grok also reads ~/.claude/settings.json hooks).\n"
        "# Manual edits are allowed but `kg` is the documented interface.\n"
        "\n"
    )


# Back-compat alias used by older call sites
_DEFAULT_HEADER = (
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
    """Return the registry path, honoring ``KG_REGISTRY_PATH`` and preferring Grok location when appropriate."""
    return _effective_registry_path()


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

    body = _registry_header()
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
