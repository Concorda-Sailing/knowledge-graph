"""Pure helpers for converting AST primitives into canonical depgraph nodes.

Pinned to pre-flip extract_api.py output byte-for-byte. See plan doc:
docs/superpowers/plans/2026-05-15-framework-canonicalization.md.
"""
from __future__ import annotations

import hashlib
import json


def slugify_id_py(node_id: str) -> str:
    """Python-extractor slugify (extract_api.py:446-453)."""
    return (
        node_id.replace("::", "__")
        .replace("/", "_")
        .replace("{", "")
        .replace("}", "")
        .strip("_")
    )


def structural_hash(payload: dict) -> str:
    """extract_api.py:499-501 — sha256 of sort_keys JSON with default=str."""
    blob = json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()


def canonical_path(path: str) -> str:
    """extract_api.py:425-443 — named params -> positional placeholders."""
    out, depth, idx = [], 0, 0
    for ch in path:
        if ch == "{":
            depth = 1; out.append("{"); continue
        if ch == "}" and depth:
            depth = 0; out.append(f"{idx}}}"); idx += 1; continue
        if depth:
            continue
        out.append(ch)
    return "".join(out)


def canonical_id_for_endpoint(method: str, path: str) -> str:
    """Return canonical node ID for an HTTP endpoint."""
    return f"{method.upper()}::{canonical_path(path)}"


def canonical_id_for_repo_symbol(repo_key: str, rel_path: str, symbol: str) -> str:
    """Return canonical node ID for a symbol within a repository."""
    return f"{repo_key}::{rel_path}::{symbol}"
