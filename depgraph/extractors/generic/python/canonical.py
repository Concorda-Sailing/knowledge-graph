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


WEBSOCKET_SYMBOLS = frozenset({
    "broadcast_event", "broadcast_to_room", "send_to_user",
})


def build_symbol_index(primitives: list[dict], *, repo_key: str) -> dict[str, dict]:
    """Top-level symbol short-name -> {file, kind, line}.

    extract_api.py:511-533. Used by walk_handler_body to resolve imported
    names to canonical targets. Last definition wins on collision.
    """
    out: dict[str, dict] = {}
    for n in primitives:
        if n["kind"] not in ("class", "function"):
            continue
        # Top-level: parent is the module
        if n.get("parent_id") and not n["parent_id"].endswith(":<module>"):
            continue
        out[n["name"]] = {
            "file": n["file"], "kind": n["kind"],
            "line": n.get("line"),
        }
    return out


def resolve_endpoint_depends_on(
    *, host_id: str, host_file: str,
    primitives: list[dict], symbol_index: dict[str, dict],
    repo_key: str,
) -> list[dict]:
    """Reproduce walk_handler_body (extract_api.py:734-811).

    For each call_edge from host_id, look up the call target in the host
    module's import aliases, then in symbol_index. Emit edge with via:
      class -> db_query
      WEBSOCKET_SYMBOLS -> websocket
      otherwise -> import
    """
    module_id = f"{repo_key}:{host_file}:<module>"
    aliases: dict[str, str] = {}
    for n in primitives:
        if n["kind"] != "import_edge" or n["from_id"] != module_id:
            continue
        target = n["target"]
        local = target.rsplit(".", 1)[-1]
        aliases[local] = local  # local name maps to imported short name

    edges: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for n in primitives:
        if n["kind"] != "call_edge" or n["from_id"] != host_id:
            continue
        callee = n["target"].split(".", 1)[0]
        if callee not in aliases:
            continue
        imported_name = aliases[callee]
        sym = symbol_index.get(imported_name)
        if not sym:
            continue
        target_id = (
            f"{repo_key}::{sym['file']}::{imported_name}"
        )
        if sym["kind"] == "class":
            via = "db_query"
        elif imported_name in WEBSOCKET_SYMBOLS:
            via = "websocket"
        else:
            via = "import"
        key = (target_id, via)
        if key in seen:
            continue
        seen.add(key)
        edges.append({
            "target": target_id, "via": via,
            "where": f"{host_file}:{n['line']}",
            "confidence": "exact",
        })
    return edges
