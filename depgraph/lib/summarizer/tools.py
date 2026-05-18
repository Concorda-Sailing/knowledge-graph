"""Built-in tools the agent can call when drafting a dossier.

These are the operations the model needs to walk dependencies and read
source — the same data the existing `dossier-draft` bundle materializes
all at once, but exposed as on-demand calls so the agent can be selective.

Each tool is registered as (ToolDefinition, ToolHandler). The handler is
a closure over a ToolContext that carries the framework data dir, the
configured repo paths, etc. Tools never write — they're read-only views.

Keep this set small. The dossier task doesn't need a shell or a file
writer; everything the agent should reach for is here.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from depgraph.lib.summarizer.agent import ToolHandler
from depgraph.lib.summarizer.types import ToolDefinition


_MAX_SOURCE_LINES = 400  # hard cap per read; agent can re-call for more
_MAX_DEPENDENTS_PER_CALL = 50
_MAX_GIT_LOG_ENTRIES = 25


@dataclass
class ToolContext:
    """The state tools read from. Built once per agent run.

    `data_dir` is the depgraph data dir (e.g. ~/project-knowledge-graph/depgraph).
    `repos` maps `[repos.<key>]` keys → on-disk checkout paths (already
    `~`-expanded).
    `dependents_index` is the parsed `nodes/_index/by_target.json`.
    `nodes_by_id` maps node-id → the parsed node dict; tools use it for
    `node_info` and to translate ids back into source locations.
    """
    data_dir: Path
    repos: dict[str, Path]
    dependents_index: dict[str, list[dict]]
    nodes_by_id: dict[str, dict]


# ---------------------------------------------------------------------------
# read_source
# ---------------------------------------------------------------------------

_READ_SOURCE_DEF = ToolDefinition(
    name="read_source",
    description=(
        "Read a window of source code from one of the project's tracked "
        "repos. Returns up to 400 lines as a numbered string. Use this to "
        "look at the body of the symbol you're documenting and at the "
        "definitions of its dependencies."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "repo": {"type": "string", "description": "Repo key (e.g. 'api', 'web')."},
            "path": {"type": "string", "description": "Repo-relative file path."},
            "start_line": {"type": "integer", "description": "1-based start line.", "minimum": 1},
            "end_line": {"type": "integer", "description": "1-based end line (inclusive).", "minimum": 1},
        },
        "required": ["repo", "path", "start_line", "end_line"],
    },
)


def _make_read_source(ctx: ToolContext) -> ToolHandler:
    def handler(args: dict[str, Any]) -> str:
        repo_key = args.get("repo")
        rel = args.get("path")
        start = int(args.get("start_line") or 1)
        end = int(args.get("end_line") or start)
        if repo_key not in ctx.repos:
            return f"error: repo {repo_key!r} not in [repos.*]; available: {sorted(ctx.repos)}"
        full = (ctx.repos[repo_key] / rel).resolve()
        # Refuse path-escape attempts (`../`-style traversal out of the repo root).
        repo_root = ctx.repos[repo_key].resolve()
        if not str(full).startswith(str(repo_root) + "/") and full != repo_root:
            return f"error: path escapes repo root: {rel!r}"
        if not full.exists():
            return f"error: file not found: {repo_key}::{rel}"
        try:
            text = full.read_text()
        except OSError as e:
            return f"error: could not read {repo_key}::{rel}: {e}"
        lines = text.splitlines()
        if end < start:
            return "error: end_line must be >= start_line"
        if end - start + 1 > _MAX_SOURCE_LINES:
            end = start + _MAX_SOURCE_LINES - 1
            note = f"\n... [truncated to {_MAX_SOURCE_LINES} lines; re-call with a smaller window or step]"
        else:
            note = ""
        # 1-based slicing.
        chunk = lines[max(0, start - 1):end]
        numbered = "\n".join(f"{i + start:>5}  {l}" for i, l in enumerate(chunk))
        return numbered + note
    return handler


# ---------------------------------------------------------------------------
# dependents_of
# ---------------------------------------------------------------------------

_DEPENDENTS_DEF = ToolDefinition(
    name="dependents_of",
    description=(
        "List the nodes that depend on a given node id. Each entry includes "
        "the dependent node id, edge kind (calls/imports/reads/etc.), and "
        "the source location of the dependency. Use this to learn who relies "
        "on the symbol you're documenting — which informs the 'External "
        "consumers' and 'Invariants' sections of the dossier."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "node_id": {
                "type": "string",
                "description": "Canonical node id (e.g. 'api::routers/auth.py::login').",
            },
            "limit": {
                "type": "integer",
                "description": f"Cap on entries returned (default and max: {_MAX_DEPENDENTS_PER_CALL}).",
                "minimum": 1, "maximum": _MAX_DEPENDENTS_PER_CALL,
            },
        },
        "required": ["node_id"],
    },
)


def _make_dependents_of(ctx: ToolContext) -> ToolHandler:
    def handler(args: dict[str, Any]) -> str:
        nid = args.get("node_id")
        if not nid:
            return "error: node_id is required"
        limit = int(args.get("limit") or _MAX_DEPENDENTS_PER_CALL)
        limit = min(limit, _MAX_DEPENDENTS_PER_CALL)
        deps = ctx.dependents_index.get(nid) or []
        if not deps:
            return f"(no dependents recorded for {nid})"
        lines = [f"{len(deps)} dependent(s) recorded for {nid}:"]
        for d in deps[:limit]:
            src = d.get("source") or "?"
            kind = d.get("kind") or "?"
            via = d.get("via") or "?"
            where = d.get("where") or "?"
            conf = d.get("confidence") or "?"
            lines.append(f"  - {src}  [{kind}/{via}, {conf}] @ {where}")
        if len(deps) > limit:
            lines.append(f"  ... +{len(deps) - limit} more (raise `limit` to see more)")
        return "\n".join(lines)
    return handler


# ---------------------------------------------------------------------------
# node_info
# ---------------------------------------------------------------------------

_NODE_INFO_DEF = ToolDefinition(
    name="node_info",
    description=(
        "Return structural metadata for a node by id: primitive kind, "
        "classification kind, signature, source location, attributes, "
        "and its outbound edge summary. Use this when you want to "
        "ground yourself in a symbol before reading its source."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "node_id": {"type": "string"},
        },
        "required": ["node_id"],
    },
)


def _make_node_info(ctx: ToolContext) -> ToolHandler:
    def handler(args: dict[str, Any]) -> str:
        nid = args.get("node_id")
        if not nid:
            return "error: node_id is required"
        node = ctx.nodes_by_id.get(nid)
        if node is None:
            return f"error: no node with id {nid!r}"
        src = node.get("source") or {}
        edges = node.get("edges_out") or []
        edge_kinds: dict[str, int] = {}
        for e in edges:
            edge_kinds[e.get("kind") or "?"] = edge_kinds.get(e.get("kind") or "?", 0) + 1
        summary = {
            "id": nid,
            "primitive": node.get("primitive"),
            "kind": node.get("kind"),
            "name": node.get("name"),
            "owner": node.get("owner"),
            "source": {
                "repo": src.get("repo"),
                "path": src.get("path"),
                "line": src.get("line"),
                "end_line": src.get("end_line"),
            },
            "signature": node.get("signature") or {},
            "attributes": node.get("attributes") or {},
            "edges_out_summary": edge_kinds,
        }
        return json.dumps(summary, indent=2)
    return handler


# ---------------------------------------------------------------------------
# recent_history
# ---------------------------------------------------------------------------

_RECENT_HISTORY_DEF = ToolDefinition(
    name="recent_history",
    description=(
        "Recent git commits touching a file in one of the project's "
        "tracked repos (default: last 25, oneline). Use to learn how the "
        "symbol has evolved and which incidents / refactors shaped its "
        "current shape."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "repo": {"type": "string"},
            "path": {"type": "string"},
            "limit": {
                "type": "integer", "minimum": 1, "maximum": _MAX_GIT_LOG_ENTRIES,
            },
        },
        "required": ["repo", "path"],
    },
)


def _make_recent_history(ctx: ToolContext) -> ToolHandler:
    def handler(args: dict[str, Any]) -> str:
        repo_key = args.get("repo")
        rel = args.get("path")
        limit = int(args.get("limit") or _MAX_GIT_LOG_ENTRIES)
        limit = min(limit, _MAX_GIT_LOG_ENTRIES)
        if repo_key not in ctx.repos:
            return f"error: repo {repo_key!r} not in [repos.*]"
        try:
            out = subprocess.run(
                ["git", "log", f"-{limit}", "--oneline", "--", rel or "."],
                cwd=str(ctx.repos[repo_key]),
                capture_output=True, text=True, timeout=10,
            )
        except (OSError, subprocess.SubprocessError) as e:
            return f"error: git failed: {e}"
        text = (out.stdout or "").strip() or "(no commits in window)"
        return text
    return handler


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


def builtin_tool_definitions() -> list[ToolDefinition]:
    """The definitions only — useful for tests / one-shot prompts that
    want to list the tools to the user without actually wiring up
    handlers."""
    return [_READ_SOURCE_DEF, _DEPENDENTS_DEF, _NODE_INFO_DEF, _RECENT_HISTORY_DEF]


def builtin_tool_handlers(ctx: ToolContext) -> dict[str, ToolHandler]:
    """Wire up handlers against a concrete ToolContext."""
    return {
        _READ_SOURCE_DEF.name: _make_read_source(ctx),
        _DEPENDENTS_DEF.name: _make_dependents_of(ctx),
        _NODE_INFO_DEF.name: _make_node_info(ctx),
        _RECENT_HISTORY_DEF.name: _make_recent_history(ctx),
    }
