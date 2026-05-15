"""Python language extractor.

Five-stage contract: discover -> parse -> emit primitives -> run
detectors -> write. This file lands in stages across tasks 3, 4, 5.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterator


DEFAULT_EXCLUDES = (
    ".venv", "venv", "__pycache__", ".git", ".tox", "node_modules",
    "dist", "build", "target", ".mypy_cache", ".pytest_cache",
)


def discover_files(
    root: Path,
    extra_excludes: list[str] | None = None,
) -> Iterator[Path]:
    """Yield `.py` files under `root`, skipping common build/vendor dirs."""
    excludes = set(DEFAULT_EXCLUDES) | set(extra_excludes or ())
    for path in sorted(root.rglob("*.py")):
        if any(part in excludes for part in path.relative_to(root).parts):
            continue
        yield path


def parse_file(path: Path) -> tuple[ast.AST | None, str | None]:
    """Parse a single file. Returns (tree, None) on success or
    (None, diagnostic_message) on syntax error."""
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        return ast.parse(source, filename=str(path)), None
    except SyntaxError as e:
        return None, f"parse_error: {path}:{e.lineno}: {e.msg}"
