"""Shared utilities used by multiple logigraph subcommand handlers.

Every function takes `ctx: Context` as its first parameter so handlers
don't reach for module globals. This is the refactor that unblocks
native import-and-register from kg.cli.logigraph.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_LOGIGRAPH_LIB = Path(__file__).resolve().parents[1]
if str(_LOGIGRAPH_LIB) not in sys.path:
    sys.path.insert(0, str(_LOGIGRAPH_LIB))
from config import (  # noqa: E402
    project_repos,
    path_to_repo_relative,
    load_project_config,
)

# P5T3: lifted to kg.shared for cross-graph reuse.
_TOOL_ROOT_FOR_KG = Path(__file__).resolve().parents[3]
if str(_TOOL_ROOT_FOR_KG) not in sys.path:
    sys.path.insert(0, str(_TOOL_ROOT_FOR_KG))
from kg.shared.git import git_commit_if_changed as _kg_git_commit, default_actor  # noqa: E402
from kg.shared.telemetry import load_telemetry_events  # noqa: E402

from .context import Context

# Domain id prefixes — used by _resolve_node_path and the path helpers.
_DOMAIN_PREFIXES = ("role", "resource", "attribute", "relationship", "action")


# ---------------------------------------------------------------------------
# Node loading
# ---------------------------------------------------------------------------

def _is_node_file(path: Path) -> bool:
    if path.name.startswith("_"):
        return False
    if any(p.startswith("_") for p in path.parts):
        return False
    return True


def load_all_nodes(ctx: Context) -> dict[str, tuple[Path, dict]]:
    """Return id -> (file_path, node_dict) for every authored logigraph node."""
    out: dict[str, tuple[Path, dict]] = {}
    for path in ctx.NODES.rglob("*.json"):
        if not _is_node_file(path):
            continue
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            print(f"WARN: invalid JSON {path}: {e}", file=sys.stderr)
            continue
        nid = data.get("id")
        if not nid:
            continue
        out[nid] = (path, data)
    return out


def load_depgraph_corpus(ctx: Context) -> dict[str, dict]:
    """Read depgraph nodes once. Returns id -> node dict."""
    by_id: dict[str, dict] = {}
    dnodes = ctx.depgraph_dir / "nodes"
    if not dnodes.exists():
        return by_id
    for path in dnodes.rglob("*.json"):
        if path.name.startswith("_") or any(p.startswith("_") for p in path.parts):
            continue
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        nid = data.get("id")
        if nid:
            by_id[nid] = data
    return by_id


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_json_schema(data: dict, schema_path: Path) -> str | None:
    """Return None if valid, else error message."""
    try:
        import jsonschema
    except ImportError:
        return "jsonschema not installed; pip install jsonschema"
    try:
        schema = json.loads(schema_path.read_text())
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        return str(e.message)
    except json.JSONDecodeError as e:
        return f"schema parse error: {e}"
    return None


# ---------------------------------------------------------------------------
# Path / target resolution
# ---------------------------------------------------------------------------

def repo_relative(ctx: Context, abs_path: str) -> tuple[str, str] | None:
    """Resolve any absolute path under a configured [repos.*].path to
    (basename, rel). Same shape as depgraph's helper."""
    return path_to_repo_relative(abs_path, ctx.LOGIGRAPH)


def find_rules_for_target(ctx: Context, target: str) -> list[str]:
    """If target looks like a file path, return rule_ids that claim any
    depgraph node living in that file. If target looks like a node id
    (rule:: or domain subkind prefix), return [target] verbatim. If target
    looks like a depgraph node id (contains '::' but is not a domain subkind
    prefix), look it up in the by_code index."""
    by_code_index = ctx.NODES / "_index" / "by_code.json"
    by_file_index = ctx.NODES / "_index" / "by_file.json"

    if target.startswith(("rule::", "role::", "resource::", "action::", "attribute::")):
        return [target]
    # Depgraph node IDs contain '::' (e.g. "concorda-api::models/foo.py::Foo").
    if "::" in target:
        if not by_code_index.exists():
            print("by_code index not built — run `bin/logigraph regen`", file=sys.stderr)
            return []
        idx = json.loads(by_code_index.read_text())
        return idx.get("by_target", {}).get(target, [])
    if not by_file_index.exists():
        print("by_file index not built — run `bin/logigraph regen`", file=sys.stderr)
        return []
    idx = json.loads(by_file_index.read_text())
    rr = repo_relative(ctx, target)
    if not rr:
        repos = project_repos(ctx.LOGIGRAPH)
        for info in repos.values():
            basename = info["basename"]
            if target.startswith(f"{basename}/"):
                rel = target[len(basename) + 1:]
                if (info["path"] / rel).exists():
                    rr = (basename, rel)
                    break
            elif (info["path"] / target).exists():
                rr = (info["basename"], target)
                break
    if not rr:
        return []
    key = f"{rr[0]}/{rr[1]}"
    return idx.get("by_file", {}).get(key, [])


# ---------------------------------------------------------------------------
# Node path resolution
# ---------------------------------------------------------------------------

def _rule_node_path(ctx: Context, rule_id: str) -> Path:
    """rule::category::short_name → nodes/rules/category__short_name.json"""
    if not rule_id.startswith("rule::"):
        raise ValueError(f"not a rule id: {rule_id}")
    parts = rule_id.split("::", 2)
    if len(parts) != 3:
        raise ValueError(f"malformed rule id (expected 3 segments): {rule_id}")
    return ctx.NODES / "rules" / f"{parts[1]}__{parts[2]}.json"


def _domain_node_path(ctx: Context, domain_id: str) -> Path:
    """<subkind>::<category>::<short_name> → nodes/domain/<subkind>__<category>__<short_name>.json"""
    parts = domain_id.split("::")
    if len(parts) != 3 or parts[0] not in _DOMAIN_PREFIXES:
        raise ValueError(f"not a valid domain id: {domain_id}")
    return ctx.NODES / "domain" / f"{parts[0]}__{parts[1]}__{parts[2]}.json"


def _process_node_path(ctx: Context, process_id: str) -> Path:
    """process::<category>::<short_name> → nodes/processes/<category>__<short_name>.json"""
    parts = process_id.split("::")
    if len(parts) != 3 or parts[0] != "process":
        raise ValueError(f"not a valid process id: {process_id}")
    return ctx.NODES / "processes" / f"{parts[1]}__{parts[2]}.json"


def resolve_node_path(ctx: Context, node_id: str) -> Path | None:
    """Resolve a logigraph node id to its JSON path. Supports rule / domain
    (resource, role, attribute, relationship) / process prefixes."""
    if node_id.startswith("rule::"):
        try:
            return _rule_node_path(ctx, node_id)
        except ValueError:
            return None
    if any(node_id.startswith(p + "::") for p in _DOMAIN_PREFIXES):
        try:
            return _domain_node_path(ctx, node_id)
        except ValueError:
            return None
    if node_id.startswith("process::"):
        try:
            return _process_node_path(ctx, node_id)
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def git_commit_if_changed(ctx: Context, paths: list[Path], message: str) -> bool:
    """Backward-compat: delegates to kg.shared.git.git_commit_if_changed with ctx.LOGIGRAPH."""
    return _kg_git_commit(ctx.LOGIGRAPH, paths, message)


# default_actor is a direct re-export from kg.shared.git (imported above).
# load_telemetry_events is a direct re-export from kg.shared.telemetry (imported above).
_load_telemetry_events = load_telemetry_events  # backward-compat alias (underscore prefix)


# ---------------------------------------------------------------------------
# Dossier frontmatter rewrite (used by rule-bump, domain-bump, process-bump)
# ---------------------------------------------------------------------------

def rewrite_dossier_frontmatter(
    dossier_path: Path,
    structural_hash: str,
    new_status: str,
    actor: str | None,
) -> None:
    """Rewrite a dossier's frontmatter for a bump action.

    - Sets definition_status to new_status.
    - When new_status == 'human_reviewed': sets last_reviewed +
      last_reviewed_against_hash + reviewed_by + reviewed_at.
    - When new_status != 'human_reviewed': drops those fields if present.
    - Preserves every other frontmatter field (notably authored_by).
    """
    import datetime as _dt
    text = dossier_path.read_text()
    if not text.startswith("---"):
        return
    end = text.index("\n---\n", 4)
    fm_block = text[4:end]
    body = text[end + 5:]
    today = _dt.date.today().isoformat()
    reviewed = (new_status == "human_reviewed")
    handled: set[str] = set()
    out: list[str] = []
    for line in fm_block.splitlines():
        s = line.strip()
        if s.startswith("definition_status:"):
            out.append(f"definition_status: {new_status}")
            handled.add("definition_status")
        elif s.startswith("last_reviewed:"):
            if reviewed:
                out.append(f"last_reviewed: {today}")
                handled.add("last_reviewed")
            # else: drop
        elif s.startswith("last_reviewed_against_hash:"):
            if reviewed:
                out.append(f"last_reviewed_against_hash: {structural_hash}")
                handled.add("last_reviewed_against_hash")
        elif s.startswith("reviewed_by:"):
            if reviewed and actor:
                out.append(f"reviewed_by: {actor}")
                handled.add("reviewed_by")
        elif s.startswith("reviewed_at:"):
            if reviewed:
                out.append(f"reviewed_at: {today}")
                handled.add("reviewed_at")
        else:
            out.append(line)
    if "definition_status" not in handled:
        out.append(f"definition_status: {new_status}")
    if reviewed:
        if "last_reviewed" not in handled:
            out.append(f"last_reviewed: {today}")
        if "last_reviewed_against_hash" not in handled:
            out.append(f"last_reviewed_against_hash: {structural_hash}")
        if actor and "reviewed_by" not in handled:
            out.append(f"reviewed_by: {actor}")
        if "reviewed_at" not in handled:
            out.append(f"reviewed_at: {today}")
    dossier_path.write_text("---\n" + "\n".join(out).strip("\n") + "\n---\n" + body)
