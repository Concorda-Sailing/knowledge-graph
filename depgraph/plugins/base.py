"""Plugin protocol + detection helpers.

A `Plugin` bundles a stable name, a detector (`is repo using this framework?`),
and a contribution of `LanguageCues` per language. Plugins are discovered by
walking `depgraph.plugins.*` subpackages — each plugin module exports a
`make_plugin() -> Plugin` factory.

Pattern: registry of self-detecting strategies, same shape as Vite/ESLint
plugins. Activation is data-driven (read `package.json` / `pyproject.toml` /
marker files) rather than imperative, so adding a new framework is one new
plugin module — no edits to the engine or other plugins.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from depgraph.lib.classification.config import LanguageCues


@dataclass
class Plugin:
    """A framework or convention pack the classifier can activate."""

    name: str
    """Stable identifier (e.g. 'react', 'fastapi'). Used in project.toml
    enable/disable lists and in the plugin-active log line."""

    detect: Callable[[Path], bool]
    """Predicate that returns True when this plugin should be active for the
    given repo path. Usually reads dependency manifests or marker files."""

    cues: dict[str, LanguageCues] = field(default_factory=dict)
    """Per-language cue contributions, keyed by language name
    (`python` / `typescript`). Unioned with other active plugins' cues."""


# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------

def has_npm_dep(repo_path: Path, package: str) -> bool:
    """True if `package` appears in package.json dependencies, devDependencies,
    or peerDependencies. Walks up from repo_path to find the nearest
    package.json (monorepo-friendly)."""
    import json

    for candidate in [repo_path, *repo_path.parents]:
        pkg = candidate / "package.json"
        if not pkg.is_file():
            continue
        try:
            data = json.loads(pkg.read_text())
        except (json.JSONDecodeError, OSError):
            return False
        for section in ("dependencies", "devDependencies", "peerDependencies"):
            if package in (data.get(section) or {}):
                return True
        return False
    return False


def has_pypi_dep(repo_path: Path, package: str) -> bool:
    """True if `package` appears in pyproject.toml dependencies (PEP 621 or
    Poetry layout) or in requirements.txt / requirements-*.txt at repo_path.
    Case-insensitive on the package name; ignores version specifiers."""
    import re

    pkg_lower = package.lower()

    pyproject = repo_path / "pyproject.toml"
    if pyproject.is_file():
        try:
            text = pyproject.read_text()
        except OSError:
            text = ""
        # Cheap textual match — robust against both [project.dependencies]
        # and [tool.poetry.dependencies] layouts without pulling in a TOML
        # parser dependency for a plugin-level check.
        # Match `package` as a bare token at the start of a quoted entry or
        # as a TOML key.
        patterns = [
            rf'"{re.escape(package)}"',
            rf"'{re.escape(package)}'",
            rf'"{re.escape(package)}[<>=!~ ]',
            rf"'{re.escape(package)}[<>=!~ ]",
            rf"^\s*{re.escape(package)}\s*=",
        ]
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE | re.MULTILINE):
                return True

    for req in [repo_path / "requirements.txt", *repo_path.glob("requirements-*.txt")]:
        if not req.is_file():
            continue
        try:
            for line in req.read_text().splitlines():
                line = line.split("#", 1)[0].strip()
                if not line:
                    continue
                name = re.split(r"[<>=!~ \[]", line, maxsplit=1)[0].strip()
                if name.lower() == pkg_lower:
                    return True
        except OSError:
            continue
    return False


def has_marker_file(repo_path: Path, *globs: str) -> bool:
    """True if any of the given globs (relative to repo_path) matches at
    least one existing file. Useful for tool configs like `vitest.config.ts`
    or `pytest.ini` that signal use even when not in deps."""
    for pattern in globs:
        for _ in repo_path.glob(pattern):
            return True
    return False
