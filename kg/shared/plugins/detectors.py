"""Manifest-reading detectors for plugin activation.

These helpers check a repo's dependency manifests or marker files to
decide whether a plugin should activate. They're language- and
subsystem-agnostic — `has_npm_dep` works the same way whether it's
being called by a depgraph plugin (looking for `react`) or a logigraph
plugin (looking for `express`).

Each function is robust to missing files, malformed JSON / TOML, and
permission errors: returns False rather than raising. A broken
manifest in a target repo shouldn't break `kg depgraph regen` for the
rest of the corpus.
"""
from __future__ import annotations

import json
import re
from pathlib import Path


def has_npm_dep(repo_path: Path, package: str) -> bool:
    """True if `package` appears in `dependencies`, `devDependencies`, or
    `peerDependencies` of the nearest `package.json`.

    Walks upward from `repo_path` to handle monorepos where the
    `package.json` lives at the root but extractors run against a
    subdir. The first `package.json` found wins; this matches how npm
    resolves dependencies for a directory.
    """
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
    """True if `package` appears in `pyproject.toml` dependencies (PEP 621
    or Poetry layout) or in `requirements.txt` / `requirements-*.txt`.

    Case-insensitive on the package name; ignores version specifiers.
    Uses cheap regex matching against the file text rather than a TOML
    parser dependency for a plugin-level check.
    """
    pkg_lower = package.lower()

    pyproject = repo_path / "pyproject.toml"
    if pyproject.is_file():
        try:
            text = pyproject.read_text()
        except OSError:
            text = ""
        # Match `package` as a quoted entry (PEP 621 list) or as a TOML
        # key (Poetry's `dependencies` table).
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
    """True if any of the given globs (relative to `repo_path`) matches
    at least one existing file.

    Useful for tool configs that signal usage even when the tool isn't
    in dependencies (e.g. `vitest.config.ts`, `pytest.ini`, or a
    `prisma/schema.prisma` checked into the repo).
    """
    for pattern in globs:
        for _ in repo_path.glob(pattern):
            return True
    return False
