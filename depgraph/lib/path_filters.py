"""Path-glob filtering shared across language extractors.

Project.toml exposes per-repo `include_paths` and `exclude_paths` lists.
Every extractor that walks files must apply the same filter semantics so
the corpus boundary is decided by configuration, not by the extractor's
language. The TypeScript extractor ships an independent JS port of
`compile_glob` for ndjson-subprocess use; the two must stay in sync.

Glob syntax (gitignore-flavoured):
    **/   zero or more leading path segments (including none)
    **    any characters, including `/`
    *     any characters except `/` (one segment)
    ?     any single character except `/`

Patterns are matched against forward-slash rel-paths and anchored to the
full string.
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Sequence


@lru_cache(maxsize=256)
def compile_glob(pattern: str) -> re.Pattern[str]:
    pat = pattern.replace("\\", "/").lstrip("/")
    parts: list[str] = []
    i = 0
    while i < len(pat):
        if pat[i:i + 3] == "**/":
            parts.append("(?:.*/)?")
            i += 3
        elif pat[i:i + 2] == "**":
            parts.append(".*")
            i += 2
        elif pat[i] == "*":
            parts.append("[^/]*")
            i += 1
        elif pat[i] == "?":
            parts.append("[^/]")
            i += 1
        else:
            parts.append(re.escape(pat[i]))
            i += 1
    return re.compile(f"^{''.join(parts)}$")


def matches_any(rel_path: str, patterns: Sequence[str]) -> bool:
    """True if rel_path matches any glob pattern. See `compile_glob` for
    supported syntax."""
    norm = rel_path.replace("\\", "/")
    return any(compile_glob(p).match(norm) for p in patterns)


def included(
    rel_path: str,
    *,
    include_paths: Sequence[str] = (),
    exclude_paths: Sequence[str] = (),
) -> bool:
    """Apply include/exclude lists in the canonical order:
      1. If `include_paths` is non-empty, the path must match at least one.
      2. The path must not match any `exclude_paths` pattern.
    """
    if include_paths and not matches_any(rel_path, include_paths):
        return False
    if exclude_paths and matches_any(rel_path, exclude_paths):
        return False
    return True
