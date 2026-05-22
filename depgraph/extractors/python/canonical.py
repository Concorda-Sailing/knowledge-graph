"""Canonical id / slug / hash helpers for the v2 Python extractor."""
from __future__ import annotations

import hashlib
import json


def canonical_id(repo: str, path: str, symbol: str) -> str:
    return f"{repo}::{path}::{symbol}"


# Per-id slug. Must stay bit-identical with
# depgraph/lib/primitives.py::slugify_id_for_filename (writer/reader both use
# the lib function; this mirror exists for extractor-language consistency).
# Appends an 8-char sha1 suffix when the id contains characters outside the
# structurally-safe set `[a-zA-Z0-9_/.:]` so that ids like `r::v4-mini` and
# `r::v4/mini`, or `m.ts` and `m.ts::$`, get distinct on-disk filenames (#87).
_SAFE_SLUG_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.:"
)


def slugify_id(node_id: str) -> str:
    out = node_id.replace("::", "__")
    out = "".join(c if c.isalnum() or c == "_" else "_" for c in out)
    bare = out.strip("_")
    if any(c not in _SAFE_SLUG_CHARS for c in node_id):
        h = hashlib.sha1(node_id.encode("utf-8")).hexdigest()[:8]
        return f"{bare}_{h}" if bare else h
    return bare


# Note: corpus-wide slug-collision detection lives in depgraph/lib/primitives.py
# as `check_slug_collisions()` — reconcile invokes it during regen so two
# distinct primitive ids that slugify to the same filename get flagged
# (e.g., when a repo path contains spaces or unusual chars).


def structural_hash(payload: object) -> str:
    blob = json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()
