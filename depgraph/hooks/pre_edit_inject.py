#!/usr/bin/env python3
"""
pre_edit_inject.py — Claude Code PreToolUse hook for Edit / Write / MultiEdit.

Reads the tool input from stdin (JSON), looks up every node whose source.path
matches the target file(s), and emits a JSON envelope with `additionalContext`
containing:

  • For each affected node: dossier (truncated), direct dependents,
    transitive dependents grouped by depth, drift warnings, and external-
    consumer banner.

  • A single trailing reminder that the graph reduces but does not eliminate
    blind spots.

Performance: the entire node corpus is loaded once per invocation and re-used
across every file in the (Multi)Edit. This is O(N) reads regardless of how
many files are touched. For the hook's latency budget we still want O(<200ms)
end-to-end; if the corpus grows past ~5000 nodes, switch to a single
nodes/index.json built by reconcile.

Failure modes:
  • If lookup fails or the depgraph is missing entirely, the hook emits a
    visible warning rather than silent no-op (DRIFT.md scenario 13).
  • Transitive closure is bounded by depth and a seen-set so cycles in the
    reverse graph cannot blow up the injection.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Framework code lives two levels up from this script.
TOOL_ROOT = Path(__file__).resolve().parent.parent
_FRAMEWORK_ROOT = TOOL_ROOT.parent  # ~/tools/knowledge-graph
sys.path.insert(0, str(_FRAMEWORK_ROOT))
from depgraph.lib.config import (  # noqa: E402
    resolve_data_dir,
    load_project_config,
    project_repos,
    render_extractor,
    repo_basenames,
    path_to_repo_relative,
)

DEPGRAPH = resolve_data_dir("DEPGRAPH_DATA_DIR")
NODES = DEPGRAPH / "nodes"
DEPENDENTS_INDEX = NODES / "_index" / "dependents.json"
CORPUS_META = NODES / "_meta.json"
MANIFESTS_DIR = NODES / "_manifests"
TELEMETRY_DIR = DEPGRAPH / "telemetry"
INJECTIONS_LOG = TELEMETRY_DIR / "injections.jsonl"
DOSSIER_LINE_LIMIT = 200
TRANSITIVE_DEPTH = 3
DEPENDENTS_PER_DEPTH_CAP = 30
NODE_SCHEMA_VERSION = 1


_SCRIPT_SUFFIXES = (".py", ".ts", ".tsx", ".js", ".mjs", ".sh")


def expected_extractor_stems() -> list[str]:
    """Manifest stems we expect to exist after a clean regen, derived from
    each [repos.<key>].extractor command. Heuristic: find the FIRST token
    in the command that resolves to a script-shaped filename (suffix in
    _SCRIPT_SUFFIXES); the stem of that filename is the expected manifest
    name.

    For multi-repo extractors (one script serving N repos with different
    args), this returns one stem matching the script name; the actual
    manifests are typically named `<stem>_<repo>` per repo. We accept any
    manifest whose name STARTS WITH the derived stem, so multi-repo
    extractors don't false-positive."""
    out: list[str] = []
    for info in project_repos(DEPGRAPH).values():
        rendered = render_extractor(info, DEPGRAPH)
        if not rendered:
            continue
        for tok in rendered:
            if any(tok.endswith(s) for s in _SCRIPT_SUFFIXES):
                stem = Path(tok).stem
                if stem and stem not in out:
                    out.append(stem)
                break
    return out


def _log_injection(tool: str, file_path: str, node_ids: list[str]) -> None:
    """Append one JSONL line per node whose context was injected. Mirror of
    the logigraph telemetry pattern: lets us answer "did the depgraph hook
    actually fire for this file" post-hoc, and is the input data for a
    future ack-rate / consumption-rate metric. Failure is silently swallowed
    — telemetry must NEVER block the hook."""
    try:
        import datetime as _dt
        TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
        ts = _dt.datetime.now(_dt.timezone.utc).isoformat()
        with INJECTIONS_LOG.open("a") as f:
            for nid in node_ids:
                f.write(json.dumps({
                    "ts": ts,
                    "kind": "injection",
                    "tool": tool,
                    "file_path": file_path,
                    "node_id": nid,
                }) + "\n")
    except Exception:
        # Telemetry failure must not propagate. Silent swallow is the policy.
        pass


def load_meta_and_status() -> tuple[dict, list[str]]:
    """Defect #2: read _meta.json + manifests, surface 'regen torn' state.
       Returns (meta_dict, banners). banners are strings to render in the
       PreToolUse output before any node-specific blocks."""
    banners: list[str] = []
    meta: dict = {}
    if CORPUS_META.exists():
        try:
            meta = json.loads(CORPUS_META.read_text())
        except (OSError, json.JSONDecodeError):
            banners.append("> ⚠ Corpus metadata unreadable — graph state unknown. Run `bin/depgraph regen`.")
            return meta, banners
        status = meta.get("regen_status")
        if status != "complete":
            banners.append(
                f"> ⚠ Regen `{status or 'unknown'}` — the depgraph may be in a torn state. "
                "Re-run `bin/depgraph regen` before trusting dependents."
            )
    else:
        banners.append("> ⚠ Corpus metadata missing (`nodes/_meta.json`). Run `bin/depgraph regen`.")

    # Defect #5: if any expected extractor's manifest is missing, surface it.
    # Accept manifests whose name STARTS WITH the derived stem so multi-repo
    # extractors (one script writing <stem>_<repo>.json per repo) don't
    # false-positive.
    if MANIFESTS_DIR.exists():
        present = {f.stem for f in MANIFESTS_DIR.glob("*.json")}
        missing = []
        for expected in expected_extractor_stems():
            if not any(p == expected or p.startswith(expected + "_") for p in present):
                missing.append(expected)
        if missing:
            banners.append(
                "> ⚠ Missing extractor manifest(s): " + ", ".join(missing) +
                " — that extractor did not run this round, so its surface is not represented in the graph."
            )
    return meta, banners


def emit(envelope: dict) -> None:
    json.dump(envelope, sys.stdout)
    sys.stdout.write("\n")
    sys.stdout.flush()


def emit_warning(message: str) -> None:
    emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": f"⚠ depgraph hook: {message}",
            }
        }
    )


def target_files(tool_name: str, tool_input: dict) -> list[str]:
    """Return absolute paths of files the tool is about to touch."""
    out: list[str] = []
    if tool_name in ("Edit", "Write"):
        p = tool_input.get("file_path")
        if p:
            out.append(p)
    elif tool_name == "MultiEdit":
        # MultiEdit shape: top-level file_path + array of edits
        p = tool_input.get("file_path")
        if p:
            out.append(p)
    return list(dict.fromkeys(out))


def repo_relative(abs_path: str) -> tuple[str, str] | None:
    """Resolve an absolute filesystem path to (repo_basename, repo_relative_path)
    by consulting [repos.*].path. Works for both flat (~/<basename>/) and
    nested (~/projects/<group>/<basename>/) checkouts."""
    return path_to_repo_relative(abs_path, DEPGRAPH)


def load_corpus() -> tuple[
    dict[str, dict],
    dict[tuple[str, str], list[str]],
    dict[str, list[dict]],
    list[str],
]:
    """Load every node JSON once and the reverse-dependency index.
       Returns (by_id, by_source, dependents_index, version_mismatches).
         by_id              : id -> node dict
         by_source          : (repo, path) -> [ids] for source-path lookup
         dependents_index   : id -> [{source, via, where, confidence}, ...]
                              from nodes/_index/dependents.json (defect #1 fix)
         version_mismatches : ids of nodes with wrong schema_version (defect #7
                              gate). These are skipped from by_id; the hook
                              surfaces a banner so we don't silently miss them."""
    by_id: dict[str, dict] = {}
    by_source: dict[tuple[str, str], list[str]] = {}
    dependents_index: dict[str, list[dict]] = {}

    if not NODES.exists():
        return by_id, by_source, dependents_index, []

    version_mismatches: list[str] = []
    for node_file in NODES.rglob("*.json"):
        # Any path component starting with `_` is metadata or operational
        # state (_index/, _archive/, _meta.json, _staging/) — not a node.
        if node_file.name.startswith("_") or any(p.startswith("_") for p in node_file.parts):
            continue
        try:
            data = json.loads(node_file.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        nid = data.get("id")
        if not nid:
            continue
        # Schema-version gate: reject nodes from a different format. The hook
        # would otherwise read fields that may have moved or been renamed.
        node_ver = data.get("schema_version")
        if node_ver != NODE_SCHEMA_VERSION:
            version_mismatches.append(f"{nid} (version={node_ver})")
            continue
        by_id[nid] = data
        src = data.get("source") or {}
        repo, p = src.get("repo"), src.get("path")
        if repo and p:
            by_source.setdefault((repo, p), []).append(nid)
    if DEPENDENTS_INDEX.exists():
        try:
            idx = json.loads(DEPENDENTS_INDEX.read_text())
            if idx.get("schema_version") == 1 and isinstance(idx.get("by_target"), dict):
                dependents_index = idx["by_target"]
        except (OSError, json.JSONDecodeError):
            pass

    return by_id, by_source, dependents_index, version_mismatches


def walk_transitive(
    start_id: str,
    dependents_index: dict[str, list[dict]],
    max_depth: int,
) -> dict[int, list[dict]]:
    """BFS up the reverse-dependency graph. Reads from the dependents index
    (defect #1: dependents are not stored on node JSON anymore). Returns
    depth -> list of {target_id, edge_path}. Cycles broken by seen-set."""
    seen: set[str] = {start_id}
    out: dict[int, list[dict]] = {}
    frontier: list[tuple[str, int, list[dict]]] = [(start_id, 0, [])]
    while frontier:
        nid, depth, path = frontier.pop(0)
        if depth >= max_depth:
            continue
        for d in dependents_index.get(nid) or []:
            src = d.get("source")
            if not src or src in seen:
                continue
            seen.add(src)
            edge = {
                "from": nid,
                "to": src,
                "via": d.get("via"),
                "where": d.get("where"),
                "confidence": d.get("confidence", "exact"),
            }
            new_path = path + [edge]
            out.setdefault(depth + 1, []).append({"target": src, "path": new_path})
            frontier.append((src, depth + 1, new_path))
    return out


def load_dossier(node: dict) -> tuple[str, str]:
    rel = node.get("dossier")
    if not rel:
        return ("", "_No dossier registered for this node._")
    path = DEPGRAPH / rel
    if not path.exists():
        return ("", "_No dossier yet — run `bin/depgraph stub-dossiers` to auto-stub, or write one by hand._")
    text = path.read_text()
    pinned_hash = None
    status = "current"
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("last_reviewed_against_hash:"):
            pinned_hash = s.split(":", 1)[1].strip().strip('"').strip("'")
        if s.startswith("status:"):
            status = s.split(":", 1)[1].strip()
        if s == "---" and pinned_hash is not None:
            break
    banner = ""
    if pinned_hash and pinned_hash != node.get("structural_hash"):
        banner = (
            f"⚠ STALE DOSSIER — last reviewed against hash {pinned_hash[:12]}, "
            f"current is {(node.get('structural_hash') or '')[:12]}. Treat invariants below as advisory."
        )
    elif status == "unreviewed":
        banner = "⚠ UNREVIEWED DOSSIER — only auto-stub content present."

    lines = text.splitlines()
    total = len(lines)
    if total > DOSSIER_LINE_LIMIT:
        lines = lines[:DOSSIER_LINE_LIMIT] + [
            f"... ({total - DOSSIER_LINE_LIMIT} more lines truncated; open dossier for full text)"
        ]
    return banner, "\n".join(lines)


def _is_fuzzy_edge(edge: dict) -> bool:
    """An edge is 'fuzzy' if it was matched by URL canonicalization rather than
    a verified import — `string_url` via or `fuzzy`/`inferred` confidence.
    Defect #3: rendering exact and fuzzy edges in the same list lets the hook
    silently overstate certainty. We surface them in separate blocks instead."""
    return edge.get("via") == "string_url" or edge.get("confidence") in ("fuzzy", "inferred")


def format_direct_dependents(node_id: str, dependents_index: dict[str, list[dict]]) -> str:
    deps = dependents_index.get(node_id) or []
    if not deps:
        return "_No direct dependents._"
    exact = [d for d in deps if not _is_fuzzy_edge(d)]
    fuzzy = [d for d in deps if _is_fuzzy_edge(d)]

    sections: list[str] = []

    def _table(rows: list[dict]) -> str:
        out = ["| Caller | Via | Where | Confidence |", "|---|---|---|---|"]
        for d in rows[:DEPENDENTS_PER_DEPTH_CAP]:
            out.append(
                f"| `{d.get('source','?')}` | {d.get('via','?')} | {d.get('where') or '—'} | {d.get('confidence','exact')} |"
            )
        if len(rows) > DEPENDENTS_PER_DEPTH_CAP:
            out.append(f"| ... | ... | ... | _{len(rows) - DEPENDENTS_PER_DEPTH_CAP} more truncated_ |")
        return "\n".join(out)

    if exact:
        sections.append("**Verified callers** (compiler-resolved import or HTTP method+path match):\n\n" + _table(exact))
    if fuzzy:
        sections.append(
            "\n**Probable callers** ⚠ (URL string-match — verify before relying):\n\n" + _table(fuzzy)
        )
    if not exact and not fuzzy:
        return "_No direct dependents._"
    return "\n".join(sections)


def _path_is_fuzzy(path: list[dict]) -> bool:
    """A reverse-walk path is fuzzy as soon as any edge along it is fuzzy."""
    return any(_is_fuzzy_edge(e) for e in path)


def format_transitive(by_depth: dict[int, list[dict]]) -> str:
    """Defect #3: split paths by whether any edge along the chain was fuzzy.
    A path that's exact end-to-end is verified. A path that traverses one or
    more URL string-matches is surfaced separately so the hook can't claim
    certainty it doesn't have."""
    if not by_depth:
        return ""
    sections = []

    def _table(rows: list[dict]) -> str:
        out = ["| Caller | Path |", "|---|---|"]
        for r in rows[:DEPENDENTS_PER_DEPTH_CAP]:
            path_str = " ← ".join(
                f"`{e['from']}` ({e.get('via','?')})" for e in reversed(r["path"])
            )
            out.append(f"| `{r['target']}` | {path_str} |")
        if len(rows) > DEPENDENTS_PER_DEPTH_CAP:
            out.append(f"| ... | _{len(rows) - DEPENDENTS_PER_DEPTH_CAP} more truncated_ |")
        return "\n".join(out)

    for depth in sorted(by_depth.keys()):
        if depth <= 1:
            continue
        rows = by_depth[depth]
        if not rows:
            continue
        exact = [r for r in rows if not _path_is_fuzzy(r["path"])]
        fuzzy = [r for r in rows if _path_is_fuzzy(r["path"])]
        block = [f"### Transitive dependents (depth {depth})"]
        if exact:
            block.append("\n**Verified paths**:\n\n" + _table(exact))
        if fuzzy:
            block.append(
                "\n**Probable paths** ⚠ (chain crosses a string-URL match):\n\n" + _table(fuzzy)
            )
        sections.append("\n".join(block))
    return "\n\n".join(sections)


def format_external_consumers(node: dict) -> str:
    ext = node.get("external_consumers") or []
    if not ext:
        return ""
    rows = "\n".join(f"- **{c.get('name','?')}** — {c.get('note','')}" for c in ext)
    return f"\n### ⚠ External consumers (out-of-band; cannot be statically verified)\n\n{rows}\n"


def format_warnings(node: dict) -> str:
    w = node.get("warnings") or []
    if not w:
        return ""
    rows = "\n".join(
        f"- `{x.get('code','?')}`: {x.get('message','')}" + (f" ({x['where']})" if x.get("where") else "")
        for x in w
    )
    return f"\n### Extractor warnings\n\n{rows}\n"


def render_for_node(node: dict, dependents_index: dict[str, list[dict]]) -> str:
    banner, dossier = load_dossier(node)
    parts = [
        f"## {node.get('title', node['id'])}",
        f"**id:** `{node['id']}`  ·  **kind:** {node.get('kind','?')}",
    ]
    if banner:
        parts.append(f"\n> {banner}\n")
    parts.append("\n### Dossier\n\n" + dossier)

    parts.append("\n### Direct dependents\n\n" + format_direct_dependents(node["id"], dependents_index))

    transitive = walk_transitive(node["id"], dependents_index, TRANSITIVE_DEPTH)
    transitive_block = format_transitive(transitive)
    if transitive_block:
        parts.append("\n" + transitive_block)

    ext = format_external_consumers(node)
    if ext:
        parts.append(ext)
    warns = format_warnings(node)
    if warns:
        parts.append(warns)
    return "\n".join(parts)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        emit_warning("could not parse hook input")
        return 0

    tool_name = payload.get("tool_name") or ""
    tool_input = payload.get("tool_input") or {}
    targets = target_files(tool_name, tool_input)
    if not targets:
        return 0

    by_id, by_source, dependents_index, version_mismatches = load_corpus()
    if not by_id:
        emit_warning(f"depgraph not initialized at {DEPGRAPH}; run bin/depgraph regen")
        return 0

    rendered_blocks: list[str] = []
    _, status_banners = load_meta_and_status()
    rendered_blocks.extend(status_banners)
    if version_mismatches:
        sample = ", ".join(version_mismatches[:3])
        more = f" (+{len(version_mismatches) - 3} more)" if len(version_mismatches) > 3 else ""
        rendered_blocks.append(
            f"> ⚠ {len(version_mismatches)} node(s) skipped due to schema_version mismatch — "
            f"`bin/depgraph regen` to refresh. Examples: {sample}{more}"
        )
    if not dependents_index:
        rendered_blocks.append(
            "> ⚠ Reverse-dependency index missing or unreadable — direct callers will not show. "
            "Run `bin/depgraph regen` to rebuild `nodes/_index/dependents.json`."
        )
    injected_node_ids: list[str] = []
    primary_target: str | None = targets[0] if targets else None
    for abs_path in targets:
        rr = repo_relative(abs_path)
        if not rr:
            continue
        repo, rel = rr
        ids = by_source.get((repo, rel)) or []
        if not ids:
            rendered_blocks.append(
                f"## {abs_path}\n\n_No tracked nodes for this file. Either it's untracked (extractor doesn't cover it yet) or the file is new and pending regen._"
            )
            continue
        for nid in ids:
            node = by_id.get(nid)
            if node:
                rendered_blocks.append(render_for_node(node, dependents_index))
                injected_node_ids.append(nid)

    if not rendered_blocks:
        return 0

    cfg = load_project_config(DEPGRAPH)
    project_name = (cfg.get("project") or {}).get("name", "")
    header = f"# 📍 {project_name} depgraph context\n\n" if project_name else "# 📍 depgraph context\n\n"
    body = (
        header
        + "\n\n---\n\n".join(rendered_blocks)
        + "\n\n---\n\n"
        "_Reminder: this graph reduces blind spots, it does not make the change safe._ "
        "_Read PROCESS.md if you need a refresher._"
    )

    emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": body,
            }
        }
    )

    if injected_node_ids and primary_target:
        _log_injection(tool_name, primary_target, injected_node_ids)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        emit_warning(f"pre_edit_inject crashed: {type(e).__name__}: {e}")
        sys.exit(0)
