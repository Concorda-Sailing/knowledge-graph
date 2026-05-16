"""Canonical id / slug / hash helpers for the v2 Python extractor."""
from __future__ import annotations

import hashlib
import json


def canonical_id(repo: str, path: str, symbol: str) -> str:
    return f"{repo}::{path}::{symbol}"


def slugify_id(node_id: str) -> str:
    out = node_id.replace("::", "__")
    out = "".join(c if c.isalnum() or c == "_" else "_" for c in out)
    return out.strip("_")

# Note: corpus-wide slug-collision detection lives in depgraph/lib/primitives.py
# as `check_slug_collisions()` — reconcile invokes it during regen so two
# distinct primitive ids that slugify to the same filename get flagged
# (e.g., when a repo path contains spaces or unusual chars).


def structural_hash(payload: object) -> str:
    blob = json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()
