"""Load depgraph + logigraph indexes into in-memory dicts.

Single source of truth: the JSON files on disk at the data dirs pointed
at by DEPGRAPH_DATA_DIR and LOGIGRAPH_DATA_DIR. We re-read on each
request so the UI tracks regen output without restart. At ~1500 nodes
the cost is negligible (~50ms cold).
"""
from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
import os
import sys
import time
from pathlib import Path
from typing import Any

HOME = Path.home()


def _resolve(env_var: str) -> Path:
    """Resolve a graph data dir from env var, else fail loud. Graphui
    is meant to be run as a systemd service that sets the env vars
    explicitly (see install.sh)."""
    val = os.environ.get(env_var)
    if not val:
        sys.exit(
            f"{env_var} is not set — graphui needs both DEPGRAPH_DATA_DIR "
            f"and LOGIGRAPH_DATA_DIR pointing at the project's data dirs."
        )
    return Path(val).expanduser().resolve()


DEPGRAPH = _resolve("DEPGRAPH_DATA_DIR")
LOGIGRAPH = _resolve("LOGIGRAPH_DATA_DIR")

DEPGRAPH_NODES = DEPGRAPH / "nodes"
LOGIGRAPH_NODES = LOGIGRAPH / "nodes"

# Rollup logic is shared with depgraph + logigraph; import from the
# sibling depgraph repo. Graphui has no `lib` package of its own, so a
# plain sys.path.insert is sufficient (unlike logigraph, which has
# lib.config and needs lib.__path__ extension instead).
#
# Anchor to __file__ (not Path.home()) so the path stays valid even
# when graphui is checked out somewhere other than ~/tools/knowledge-graph/
# — the three-level parent walks app/loader.py → app/ → graphui/ → kg/,
# then steps into the sibling depgraph/ directory.
_GRAPHUI_TOOL_ROOT = Path(__file__).resolve().parent.parent
_DEPGRAPH_TOOL_ROOT = _GRAPHUI_TOOL_ROOT.parent / "depgraph"
if str(_DEPGRAPH_TOOL_ROOT) not in sys.path:
    sys.path.insert(0, str(_DEPGRAPH_TOOL_ROOT))
from lib.rollup import (  # noqa: E402
    resolve_anchor,
    compute_rollup,
    Rollup,
    AnchorResult,
)


def _tier_of(fan_out: int) -> str:
    if fan_out >= 10:
        return "A"
    if fan_out >= 3:
        return "B"
    return "C"


def _dossier_state(node: dict, root: Path) -> str:
    """Read dossier frontmatter to determine state.

    Depgraph dossiers use `status:` (current|llm_drafted|unreviewed).
    Logigraph dossiers use `definition_status:` (human_reviewed|llm_drafted|stub).
    Both are accepted; logigraph's `human_reviewed` maps to "current"
    for unified state-ordering across the UI.
    """
    rel = node.get("dossier")
    if not rel:
        return "missing"
    full = root / rel
    if not full.exists():
        return "missing"
    text = full.read_text()
    pinned = None
    status = None
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("status:"):
            status = s.split(":", 1)[1].strip()
        elif s.startswith("definition_status:"):
            status = s.split(":", 1)[1].strip()
        if s.startswith("last_reviewed_against_hash:"):
            pinned = s.split(":", 1)[1].strip().strip('"').strip("'")
        if s == "---" and pinned is not None:
            break
    if pinned and pinned != node.get("structural_hash"):
        return "stale"
    if status == "unreviewed":
        return "unreviewed"
    if status == "llm_drafted":
        return "llm_drafted"
    if status == "stub":
        return "llm_drafted"  # logigraph stubs surface in the same queue
    return "current"


_COMMITS_CACHE: dict[tuple[str, str], tuple[float, int]] = {}


def commits_30d(repo: str, rel_path: str) -> int:
    """Count commits in the last 30d touching a file. Cached for 5 minutes."""
    if not repo or not rel_path:
        return 0
    key = (repo, rel_path)
    now = time.time()
    if key in _COMMITS_CACHE:
        ts, val = _COMMITS_CACHE[key]
        if now - ts < 300:
            return val
    repo_root = HOME / repo
    if not (repo_root / ".git").exists():
        _COMMITS_CACHE[key] = (now, 0)
        return 0
    try:
        out = subprocess.run(
            ["git", "log", "--since=30.days.ago", "--oneline", "--", rel_path],
            cwd=str(repo_root),
            capture_output=True, text=True, timeout=10,
        )
        n = len([l for l in out.stdout.splitlines() if l.strip()])
    except (OSError, subprocess.SubprocessError):
        n = 0
    _COMMITS_CACHE[key] = (now, n)
    return n


# ----- Commit history (per-node card) -----------------------------------------

_HISTORY_CACHE: dict[tuple[str, tuple[str, ...]], tuple[float, list[dict]]] = {}
_REMOTE_CACHE: dict[str, tuple[float, str | None]] = {}

# Matches `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
# and any other `Co-Authored-By:` trailer.
_COAUTHOR_RE = re.compile(r"^Co-Authored-By:\s*(.+?)\s*<([^>]+)>\s*$", re.MULTILINE | re.IGNORECASE)
_CLAUDE_MODEL_RE = re.compile(r"\bClaude\s+([A-Za-z]+\s+\d+(?:\.\d+)?(?:\s*\([^)]+\))?)", re.IGNORECASE)


def _model_from_commit(author: str, body: str) -> str:
    """Pull the most informative model/author label from a commit.

    Priority:
      1. Claude `Co-Authored-By:` trailer  → e.g. "Opus 4.7 (1M context)".
      2. Any other `Co-Authored-By:`        → that human's name.
      3. Fall back to the commit author.
    """
    matches = _COAUTHOR_RE.findall(body or "")
    for name, _email in matches:
        m = _CLAUDE_MODEL_RE.search(name)
        if m:
            return m.group(1).strip()
    if matches:
        # First co-author is usually the "primary" collaborator.
        return matches[0][0].strip()
    return author or "—"


def git_remote_url(repo_root: Path) -> str | None:
    """Return the canonical https://github.com/owner/name for `repo_root`,
    or None if no GitHub remote is configured. Cached for 5 minutes."""
    key = str(repo_root)
    now = time.time()
    if key in _REMOTE_CACHE:
        ts, val = _REMOTE_CACHE[key]
        if now - ts < 300:
            return val
    url: str | None = None
    try:
        out = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=str(repo_root),
            capture_output=True, text=True, timeout=5,
        )
        raw = out.stdout.strip()
        if raw.startswith("git@github.com:"):
            raw = "https://github.com/" + raw[len("git@github.com:"):]
        if raw.endswith(".git"):
            raw = raw[:-4]
        if raw.startswith("https://github.com/"):
            url = raw
    except (OSError, subprocess.SubprocessError):
        url = None
    _REMOTE_CACHE[key] = (now, url)
    return url


def commit_history(repo_root: Path, rel_paths: list[str], limit: int = 20) -> list[dict]:
    """Return the last `limit` commits touching any of `rel_paths` in
    `repo_root`. Each entry: {sha, short, date, author, model, subject,
    url|None}. Cached for 5 minutes per (repo, paths) tuple."""
    paths = tuple(sorted(p for p in rel_paths if p))
    if not paths or not (repo_root / ".git").exists():
        return []
    key = (str(repo_root), paths)
    now = time.time()
    if key in _HISTORY_CACHE:
        ts, val = _HISTORY_CACHE[key]
        if now - ts < 300:
            return val
    remote = git_remote_url(repo_root)
    out_rows: list[dict] = []
    # NUL-separated records; \x1f-separated fields. Body is last field.
    fmt = "%H%x1f%h%x1f%aI%x1f%an%x1f%s%x1f%B"
    try:
        proc = subprocess.run(
            ["git", "log", "-z", f"-n{limit}", f"--pretty=format:{fmt}", "--", *paths],
            cwd=str(repo_root),
            capture_output=True, text=True, timeout=10,
        )
        raw = proc.stdout
    except (OSError, subprocess.SubprocessError):
        raw = ""
    for rec in raw.split("\x00"):
        rec = rec.strip()
        if not rec:
            continue
        parts = rec.split("\x1f", 5)
        if len(parts) < 6:
            continue
        sha, short, date, author, subject, body = parts
        out_rows.append({
            "sha": sha,
            "short": short,
            "date": date[:10],  # YYYY-MM-DD
            "author": author,
            "model": _model_from_commit(author, body),
            "subject": subject,
            "body": body,
            "url": f"{remote}/commit/{sha}" if remote else None,
        })
    _HISTORY_CACHE[key] = (now, out_rows)
    return out_rows


def load_dependents() -> dict[str, list[dict]]:
    p = DEPGRAPH_NODES / "_index" / "dependents.json"
    if not p.exists():
        return {}
    idx = json.loads(p.read_text())
    return idx.get("by_target") or {}


def load_logigraph_by_code() -> dict[str, list[str]]:
    """Map of depgraph node-id (or HTTP route) -> [rule_id, ...]."""
    p = LOGIGRAPH_NODES / "_index" / "by_code.json"
    if not p.exists():
        return {}
    idx = json.loads(p.read_text())
    return idx.get("by_target") or {}


def load_meta() -> dict[str, Any]:
    """Read both meta files."""
    out: dict[str, Any] = {"depgraph": {}, "logigraph": {}}
    for label, p in (
        ("depgraph", DEPGRAPH_NODES / "_meta.json"),
        ("logigraph", LOGIGRAPH_NODES / "_meta.json"),
    ):
        if p.exists():
            try:
                out[label] = json.loads(p.read_text())
            except (OSError, json.JSONDecodeError):
                pass
    return out


def load_depgraph_nodes() -> list[dict]:
    """Read every depgraph node file and enrich with derived fields:
    fan_out, tier, dossier_state, commits_30d. Sorted by id."""
    deps = load_dependents()
    nodes: list[dict] = []
    for nf in DEPGRAPH_NODES.rglob("*.json"):
        if nf.name.startswith("_") or any(p.startswith("_") for p in nf.parts):
            continue
        try:
            d = json.loads(nf.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        nid = d.get("id")
        if not nid:
            continue
        fan_out = len(deps.get(nid) or [])
        d["fan_out"] = fan_out
        d["tier"] = _tier_of(fan_out)
        d["dossier_state"] = _dossier_state(d, DEPGRAPH)
        d["_node_file"] = str(nf.relative_to(DEPGRAPH))
        src = d.get("source") or {}
        nodes.append(d)
    nodes.sort(key=lambda n: n["id"])
    return nodes


def load_logigraph_nodes() -> dict[str, list[dict]]:
    """Returns {'rules': [...], 'domain': [...], 'processes': [...]} with
    derived dossier_state."""
    out: dict[str, list[dict]] = {"rules": [], "domain": [], "processes": []}
    for kind, sub in (("rules", "rules"), ("domain", "domain"), ("processes", "processes")):
        d = LOGIGRAPH_NODES / sub
        if not d.is_dir():
            continue
        for nf in sorted(d.glob("*.json")):
            try:
                node = json.loads(nf.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            node["dossier_state"] = _dossier_state(node, LOGIGRAPH)
            node["_node_file"] = str(nf.relative_to(LOGIGRAPH))
            # Logigraph rules carry their own fan_out (claims count); use it.
            # Processes use total claim count across all steps + ui_surfaces.
            if "fan_out" not in node:
                if kind == "processes":
                    total = sum(len(s.get("claims_code") or []) for s in node.get("steps", []))
                    total += len(node.get("ui_surfaces") or [])
                    node["fan_out"] = total
                else:
                    node["fan_out"] = len(node.get("claims_code") or [])
            out[kind].append(node)
    return out


def load_process_by_id(process_id: str) -> dict | None:
    for n in load_logigraph_nodes()["processes"]:
        if n["id"] == process_id:
            return n
    return None


# ---------------------------------------------------------------------------
# Repo + kind summaries (for the gallery UI)
# ---------------------------------------------------------------------------

_STATES = ("current", "llm_drafted", "unreviewed", "stale", "missing")


def _empty_state_counts() -> dict[str, int]:
    return {s: 0 for s in _STATES}


def repo_summary() -> list[dict]:
    """One entry per source repo seen in depgraph nodes' source.repo field.
    Returns: [{basename, node_count, state_counts: {current: n, ...},
               current_pct, has_stale, kinds: [{kind, count}, ...]}]
    Sorted by node_count desc."""
    by_repo: dict[str, dict] = {}
    for n in load_depgraph_nodes():
        src = n.get("source") or {}
        basename = src.get("repo") or "(unrooted)"
        bucket = by_repo.setdefault(basename, {
            "basename": basename,
            "node_count": 0,
            "state_counts": _empty_state_counts(),
            "kinds": {},
        })
        bucket["node_count"] += 1
        state = n.get("dossier_state") or "current"
        if state not in bucket["state_counts"]:
            bucket["state_counts"][state] = 0
        bucket["state_counts"][state] += 1
        kind = n.get("kind") or "—"
        bucket["kinds"][kind] = bucket["kinds"].get(kind, 0) + 1

    out = []
    for r in by_repo.values():
        sc = r["state_counts"]
        current = sc.get("current", 0)
        total = r["node_count"]
        r["current_pct"] = round(100 * current / total) if total else 0
        r["has_stale"] = sc.get("stale", 0) > 0
        r["kinds"] = sorted(
            [{"kind": k, "count": v} for k, v in r["kinds"].items()],
            key=lambda x: -x["count"],
        )
        # --- enrichments added in Plan A ---
        r["activity"] = repo_activity(r["basename"])
        r["languages"] = repo_languages(r["basename"])
        r["areas"] = repo_areas(r["basename"])
        r["dep_counts"] = repo_dep_counts(r["basename"])
        r["cross_cuts"] = repo_cross_cuts(r["basename"])
        # dead_code_score: low push frequency + zero inbound + many stale claims.
        age = r["activity"]["last_push_age_days"] or 0
        inbound = r["dep_counts"]["inbound_repos"]
        stale = r["state_counts"].get("stale", 0)
        score = (age // 30) + (10 if inbound == 0 else 0) + stale
        r["dead_code_score"] = score
        # refine classification with inbound-deps signal.
        if r["activity"]["classification"] == "dormant" and age >= 180 and inbound == 0:
            r["activity"]["classification"] = "dead-candidate"
        out.append(r)
    out.sort(key=lambda r: -r["node_count"])
    return out


_KIND_ORDER_FLAGS = ["defect", "drift", "gap", "review_due", "incident"]


def _group_flags_by_kind(items: list[dict]) -> list[dict]:
    """Group warning objects by `kind`, preserving severity sort within each
    group. Returns list of {kind, count, items} in canonical kind order so the
    dashboard renders sections consistently."""
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    by_kind: dict[str, list[dict]] = {}
    for f in items:
        k = f.get("kind", "other")
        by_kind.setdefault(k, []).append(f)
    out = []
    for k in _KIND_ORDER_FLAGS + [k for k in by_kind if k not in _KIND_ORDER_FLAGS]:
        if k not in by_kind:
            continue
        flags = sorted(by_kind[k], key=lambda f: (severity_order.get(f.get("severity", "low"), 5), f.get("code", "")))
        out.append({"kind": k, "count": len(flags), "flags": flags})
    return out


def corpus_flags() -> dict:
    """Return the logigraph corpus's flags partitioned by tracked/fresh and
    grouped by kind within each. Reads _meta.json::flags written by reconcile.

    Shape:
      {
        "fresh":   [{kind, count, items}, ...],
        "tracked": [{kind, count, items}, ...],
        "count_fresh": N,
        "count_tracked": N,
      }
    """
    meta = load_meta()
    flags = (meta.get("logigraph") or {}).get("flags") or []
    if not isinstance(flags, list):
        flags = []
    fresh_flat = [f for f in flags if not f.get("tracked")]
    tracked_flat = [f for f in flags if f.get("tracked")]
    return {
        "fresh": _group_flags_by_kind(fresh_flat),
        "tracked": _group_flags_by_kind(tracked_flat),
        "count_fresh": len(fresh_flat),
        "count_tracked": len(tracked_flat),
    }


def warnings_for(node_id: str) -> list[dict]:
    """All flags from the corpus that mention `node_id` in their `affected`
    list. Used by detail-page renderers to surface warnings attached to or
    referencing this node."""
    meta = load_meta()
    flags = (meta.get("logigraph") or {}).get("flags") or []
    out = []
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    for f in flags:
        if node_id in (f.get("affected") or []):
            out.append(f)
    out.sort(key=lambda f: (severity_order.get(f.get("severity", "low"), 5), f.get("code", "")))
    return out


def kind_summary() -> list[dict]:
    """One entry per logigraph kind (rules / domain / processes).
    Same shape as repo_summary plus total_deps = sum of fan_out across
    nodes in that kind, so gallery cards can show dependency-weight."""
    lg = load_logigraph_nodes()
    out = []
    for kind, label in (("rules", "Rules"), ("domain", "Domain"), ("processes", "Processes")):
        nodes = lg.get(kind, [])
        if not nodes:
            continue
        sc = _empty_state_counts()
        for n in nodes:
            s = n.get("dossier_state") or "current"
            if s not in sc:
                sc[s] = 0
            sc[s] += 1
        total = len(nodes)
        total_deps = sum(n.get("fan_out", 0) for n in nodes)
        out.append({
            "kind": kind,
            "label": label,
            "node_count": total,
            "total_deps": total_deps,
            "state_counts": sc,
            "current_pct": round(100 * sc.get("current", 0) / total) if total else 0,
            "has_stale": sc.get("stale", 0) > 0,
        })
    return out


# ---------------------------------------------------------------------------
# Knowledge list page — unified rules + domain + processes with sort/filter
# ---------------------------------------------------------------------------

_KNOWLEDGE_HREF = {
    "rules": "/graph/rule/",
    "domain": "/graph/domain/",
    "processes": "/graph/process/",
}


def all_knowledge_nodes(
    sort: str = "id",
    kind_filter: str | None = None,
    state_filter: str | None = None,
    subkind_filter: str | None = None,
) -> list[dict]:
    """Flat list of all rules + domain + processes for the /graph/knowledge
    page. Filters: kind (rule|domain|process), state, subkind (domain).
    Sort: id (default), title, fan_out, state."""
    lg = load_logigraph_nodes()
    items: list[dict] = []
    for plural in ("rules", "domain", "processes"):
        singular = plural.rstrip("s")
        if kind_filter and kind_filter not in (plural, singular):
            continue
        for n in lg.get(plural, []):
            if state_filter and n.get("dossier_state") != state_filter:
                continue
            if subkind_filter and n.get("subkind") != subkind_filter:
                continue
            href_prefix = _KNOWLEDGE_HREF.get(plural, "/graph/node/")
            items.append({
                "id": n["id"],
                "title": n.get("title") or n["id"],
                "kind": singular,
                "subkind": n.get("subkind"),
                "state": n.get("dossier_state", "current"),
                "fan_out": n.get("fan_out", 0),
                "summary": (n.get("summary") or n.get("statement") or "")[:240],
                "href": f"{href_prefix}{n['id']}",
            })
    if sort == "fan_out":
        items.sort(key=lambda x: (-x["fan_out"], x["id"]))
    elif sort == "title":
        items.sort(key=lambda x: x["title"].lower())
    elif sort == "state":
        order = {"llm_drafted": 0, "stale": 1, "missing": 2, "unreviewed": 3, "current": 4}
        items.sort(key=lambda x: (order.get(x["state"], 5), x["id"]))
    else:
        items.sort(key=lambda x: x["id"])
    return items


def knowledge_filters() -> dict:
    """Available filter values for the /graph/knowledge UI."""
    lg = load_logigraph_nodes()
    subkinds = sorted({n.get("subkind") for n in lg.get("domain", []) if n.get("subkind")})
    states = set()
    for plural in ("rules", "domain", "processes"):
        for n in lg.get(plural, []):
            states.add(n.get("dossier_state") or "current")
    return {
        "kinds": ["rule", "domain", "process"],
        "subkinds": subkinds,
        "states": sorted(states),
    }


def nodes_for_repo(basename: str, kind: str | None = None, state: str | None = None) -> list[dict]:
    """Depgraph nodes for one source repo, optionally filtered by kind/state.
    Returns a flat list of dicts with the fields the card template renders."""
    out = []
    for n in load_depgraph_nodes():
        src = n.get("source") or {}
        if (src.get("repo") or "(unrooted)") != basename:
            continue
        if kind and n.get("kind") != kind:
            continue
        if state and n.get("dossier_state") != state:
            continue
        out.append({
            "id": n["id"],
            "title": n.get("title") or n["id"].rsplit("::", 1)[-1],
            "kind": n.get("kind", "—"),
            "state": n.get("dossier_state", "current"),
            "fan_out": n.get("fan_out", 0),
            "href": f"/graph/node/{n['id']}",
            "src": f"{src.get('repo','')}/{src.get('path','')}" if src.get("path") else "",
        })
    out.sort(key=lambda x: (-x["fan_out"], x["id"]))
    return out


def nodes_for_repo_grouped(basename: str, kind: str | None = None, state: str | None = None) -> list[dict]:
    """Like nodes_for_repo, but cluster by source.path. Returns:
        [{"path": "<relative path>", "nodes": [<flat-shape dicts>]}, ...]
    Sorted by path. Nodes within a path keep nodes_for_repo's sort order
    (highest fan_out first). Nodes without a source.path land under a
    synthetic "(no path)" group at the end.
    """
    flat = nodes_for_repo(basename, kind=kind, state=state)
    by_path: dict[str, list[dict]] = {}
    for n in flat:
        # n["src"] is "<repo>/<path>"; recover just the path tail
        repo_prefix = f"{basename}/"
        path = n["src"][len(repo_prefix):] if n["src"].startswith(repo_prefix) else (n["src"] or "(no path)")
        by_path.setdefault(path, []).append(n)
    sorted_paths = sorted([p for p in by_path if p != "(no path)"])
    if "(no path)" in by_path:
        sorted_paths.append("(no path)")
    return [{"path": p, "nodes": by_path[p]} for p in sorted_paths]


def nodes_for_kind(kind_name: str, subkind: str | None = None, state: str | None = None) -> list[dict]:
    """Logigraph nodes of one kind (rules / domain / processes). Subkind
    filter applies to domain (role / resource / attribute / relationship)."""
    lg = load_logigraph_nodes()
    nodes = lg.get(kind_name, [])
    out = []
    for n in nodes:
        if subkind and n.get("subkind") != subkind:
            continue
        if state and n.get("dossier_state") != state:
            continue
        # Route per kind.
        if kind_name == "rules":
            href = f"/graph/rule/{n['id']}"
        elif kind_name == "processes":
            href = f"/graph/process/{n['id']}"
        else:
            href = f"/graph/domain/{n['id']}"
        out.append({
            "id": n["id"],
            "title": n.get("title") or n["id"],
            "kind": kind_name.rstrip("s"),
            "subkind": n.get("subkind"),
            "state": n.get("dossier_state", "current"),
            "fan_out": n.get("fan_out", 0),
            "href": href,
            "summary": n.get("summary", "") or n.get("statement", ""),
        })
    out.sort(key=lambda x: (-x["fan_out"], x["id"]))
    return out


def load_node_by_id(node_id: str) -> dict | None:
    for n in load_depgraph_nodes():
        if n["id"] == node_id:
            return n
    return None


def siblings_in_file(node_id: str) -> list[dict]:
    """All other depgraph nodes whose source.path matches this node's,
    sorted by id. Excludes the node itself. Returns the same flat-shape
    dicts as nodes_for_repo so templates can reuse the node-card markup."""
    target = load_node_by_id(node_id)
    if not target:
        return []
    src = target.get("source") or {}
    path = src.get("path")
    repo = src.get("repo")
    if not path or not repo:
        return []
    out = []
    for n in load_depgraph_nodes():
        if n["id"] == node_id:
            continue
        s = n.get("source") or {}
        if s.get("path") != path or s.get("repo") != repo:
            continue
        out.append({
            "id": n["id"],
            "title": n.get("title") or n["id"].rsplit("::", 1)[-1],
            "kind": n.get("kind", "—"),
            "state": n.get("dossier_state", "current"),
            "fan_out": n.get("fan_out", 0),
            "href": f"/graph/node/{n['id']}",
        })
    out.sort(key=lambda x: x["id"])
    return out


def load_rule_by_id(rule_id: str) -> dict | None:
    for n in load_logigraph_nodes()["rules"]:
        if n["id"] == rule_id:
            return n
    return None


def load_domain_by_id(ont_id: str) -> dict | None:
    for n in load_logigraph_nodes()["domain"]:
        if n["id"] == ont_id:
            return n
    return None


def relationships_for(entity_id: str) -> dict[str, list[dict]]:
    """Return {'outgoing': [...], 'incoming': [...]} relationship entities
    that touch `entity_id`. Empty lists if entity_id is itself a
    relationship or has no edges."""
    out: dict[str, list[dict]] = {"outgoing": [], "incoming": []}
    for n in load_logigraph_nodes()["domain"]:
        if n.get("subkind") != "relationship":
            continue
        if n.get("from") == entity_id:
            out["outgoing"].append(n)
        if n.get("to") == entity_id:
            out["incoming"].append(n)
    return out


def mediation_collisions() -> list[dict]:
    """All current mediation collisions in the relationship corpus.
    Mirrors extractors/reconcile.py::detect_mediation_collisions but
    reads from the live in-memory node set so the UI doesn't depend on
    a regen run."""
    by_mech: dict[str, list[dict]] = {}
    for n in load_logigraph_nodes()["domain"]:
        if n.get("subkind") != "relationship":
            continue
        mech = n.get("mediated_by", "")
        if not mech:
            continue
        head = mech.split("(", 1)[0].strip().rstrip(",").lower()
        for piece in [p.strip() for p in head.split(" and ")]:
            if not piece:
                continue
            by_mech.setdefault(piece, []).append(n)
    return [
        {"mechanism": m, "relationships": rels}
        for m, rels in sorted(by_mech.items())
        if len({r["id"] for r in rels}) > 1
    ]


def collisions_for_relationship(rel_id: str) -> list[dict]:
    return [
        c for c in mediation_collisions()
        if any(r["id"] == rel_id for r in c["relationships"])
    ]


def read_dossier(rel_path: str | None, root: Path) -> str | None:
    if not rel_path:
        return None
    p = root / rel_path
    if not p.exists():
        return None
    return p.read_text()


# ----- Coverage matrix --------------------------------------------------------

KIND_LABELS = {
    "model": "models",
    "service": "services",
    "endpoint": "endpoints",
    "schema": "schemas",
    "component": "components",
    "hook": "hooks",
    "test": "tests",
    "rule": "rules",
    "domain": "domain",
}


def coverage_matrix() -> dict[str, dict[str, dict[str, int]]]:
    """{ kind: { tier: { state: count } } }
    states: current, llm_drafted, unreviewed, stale, missing
    Includes both depgraph kinds and logigraph kinds (rules+domain, all Tier ?).
    Logigraph kinds use a synthetic '*' tier slot since they're tier-independent.
    """
    out: dict[str, dict[str, dict[str, int]]] = {}
    for n in load_depgraph_nodes():
        kind = n.get("kind") or "unknown"
        tier = n["tier"]
        state = n["dossier_state"]
        out.setdefault(kind, {}).setdefault(tier, {}).setdefault(state, 0)
        out[kind][tier][state] += 1
    lg = load_logigraph_nodes()
    for kind in ("rules", "domain"):
        for n in lg[kind]:
            state = n["dossier_state"]
            out.setdefault(kind, {}).setdefault("*", {}).setdefault(state, 0)
            out[kind]["*"][state] += 1
    return out


# ----- Cross-refs -------------------------------------------------------------

def applicable_rules_for(node_id: str, source: dict | None = None) -> list[str]:
    """Return rule_ids whose `claims_code` or surfaces touch this node id (or
    its source path)."""
    by_code = load_logigraph_by_code()
    rules: set[str] = set()
    for r in by_code.get(node_id, []):
        rules.add(r)
    return sorted(rules)


def dependents_of(node_id: str) -> list[dict]:
    return load_dependents().get(node_id) or []


# ----- Telemetry --------------------------------------------------------------

LOGIGRAPH_INJECTIONS = LOGIGRAPH / "telemetry" / "injections.jsonl"
LOGIGRAPH_ACKS = LOGIGRAPH / "telemetry" / "acknowledgments.jsonl"
DEPGRAPH_INJECTIONS = DEPGRAPH / "telemetry" / "injections.jsonl"
DEPGRAPH_ACKS = DEPGRAPH / "telemetry" / "acknowledgments.jsonl"


def _telemetry_for_id(
    *,
    target_id: str,
    id_field: str,
    injections_path: Path,
    acks_path: Path,
    days: int = 7,
) -> dict[str, Any]:
    """Generic loader for the (injections, acks) JSONL pair. Used by both
    rule and node telemetry. Counts events from the last `days` against the
    given id (matched via `id_field`, e.g. 'rule_id' or 'node_id')."""
    cutoff = time.time() - days * 86400
    from datetime import datetime

    def _epoch(ts: str) -> float:
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
        except (ValueError, TypeError):
            return 0.0

    inj = 0
    ack = 0
    last_fired: str | None = None
    if injections_path.exists():
        for line in injections_path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get(id_field) != target_id:
                continue
            ts = row.get("ts", "")
            if _epoch(ts) < cutoff:
                continue
            inj += 1
            if not last_fired or ts > last_fired:
                last_fired = ts
    if acks_path.exists():
        for line in acks_path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get(id_field) != target_id:
                continue
            if _epoch(row.get("ts", "")) < cutoff:
                continue
            ack += 1
    return {
        "injections_7d": inj,
        "acked_7d": ack,
        "ack_rate": (ack / inj) if inj else None,
        "last_fired": last_fired,
    }


def telemetry_for_rule(rule_id: str, days: int = 7) -> dict[str, Any]:
    return _telemetry_for_id(
        target_id=rule_id,
        id_field="rule_id",
        injections_path=LOGIGRAPH_INJECTIONS,
        acks_path=LOGIGRAPH_ACKS,
        days=days,
    )


def telemetry_for_node(node_id: str, days: int = 7) -> dict[str, Any]:
    return _telemetry_for_id(
        target_id=node_id,
        id_field="node_id",
        injections_path=DEPGRAPH_INJECTIONS,
        acks_path=DEPGRAPH_ACKS,
        days=days,
    )


def compute_code_rollup(domain_node: dict, depth: int = 3) -> Rollup:
    """Build the rollup for a logigraph domain entity using the existing
    in-memory depgraph node + dependents indexes. Per-request cost is
    fine at the corpus size graphui targets.

    Returns a Rollup whose anchor is None when no model can be matched
    — the template renders a one-line "no anchor" signal in that case.
    """
    depgraph_nodes = load_depgraph_nodes()
    depgraph_index = {n["id"]: n for n in depgraph_nodes}
    dependents_index = load_dependents()

    lg = load_logigraph_nodes()
    logigraph_index = {n["id"]: n for n in lg["domain"]}

    anchor = resolve_anchor(domain_node, depgraph_index, logigraph_index=logigraph_index)
    return compute_rollup(
        anchor_id=anchor.model_id or "",
        depgraph_index=depgraph_index,
        dependents_index=dependents_index,
        depth=depth,
        anchor_result=anchor,
    )


# ----- Flag + attribution helpers (Tasks 12-14 templates) ---------------------

def flagged_state(node: dict) -> dict:
    """Extract flag fields from a node dict. Returns a uniform shape even
    when the node isn't flagged — templates can read `.flagged` reliably."""
    return {
        "flagged": bool(node.get("flagged")),
        "flagged_by": node.get("flagged_by"),
        "flagged_at": node.get("flagged_at"),
        "flagged_reason": node.get("flagged_reason"),
    }


def _parse_frontmatter(text: str) -> dict:
    """Minimal YAML-ish frontmatter parser. Handles the shape we write:
    scalar values and one-level lists (used for authored_by). Returns {}
    if no frontmatter."""
    if not text.startswith("---"):
        return {}
    try:
        end = text.index("\n---\n", 4)
    except ValueError:
        return {}
    fm = text[4:end]
    out: dict = {}
    current_list_key: str | None = None
    for raw in fm.splitlines():
        line = raw.rstrip()
        if not line:
            current_list_key = None
            continue
        if line.startswith("  - ") and current_list_key:
            out.setdefault(current_list_key, []).append(line[4:].strip())
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if not val:
            # Could be a list-start.
            current_list_key = key
            out[key] = []
        else:
            current_list_key = None
            out[key] = val
    return out


def authorship(dossier_text: str | None) -> dict:
    """Extract authored_by / reviewed_by / reviewed_at from dossier
    frontmatter. Returns a uniform dict even when fields are missing —
    empty list / None — so templates render without conditionals."""
    if not dossier_text:
        return {"authored_by": [], "reviewed_by": None, "reviewed_at": None}
    fm = _parse_frontmatter(dossier_text)
    authored = fm.get("authored_by", [])
    if isinstance(authored, str):
        authored = [authored]
    return {
        "authored_by": authored,
        "reviewed_by": fm.get("reviewed_by"),
        "reviewed_at": fm.get("reviewed_at"),
    }


_ACTION_PREFIX_RE = re.compile(
    r"^(feat|fix|review|flag|unflag|chore|docs|refactor)(?:\(([^)]*)\))?:\s*(.*)$"
)
_CO_AUTHOR_RE = re.compile(r"^Co-Authored-By:\s*(.+?)\s*<", re.M | re.I)


def parse_action_timeline(commits: list[dict]) -> list[dict]:
    """Classify each commit (output of commit_history) into an action row.
    Output is ordered newest-first (same order as input). Each row carries
    {action, actor, date, subject, body, sha}.

    Action is the commit-message prefix; 'edit' for unprefixed commits.
    Actor is the Co-Authored-By trailer when present, else the git author.
    """
    out: list[dict] = []
    for c in commits:
        subject = c.get("subject", "")
        body = c.get("body", "")
        m = _ACTION_PREFIX_RE.match(subject)
        action = m.group(1) if m else "edit"
        co = _CO_AUTHOR_RE.search(body or "")
        actor = co.group(1) if co else c.get("author", "—")
        out.append({
            "action": action,
            "actor": actor,
            "date": c.get("date"),
            "subject": subject,
            "body": body,
            "sha": c.get("sha", ""),
        })
    return out


def flagged_nodes() -> list[dict]:
    """Return every flagged node across depgraph + logigraph. Each row has
    {id, kind, title, flagged_by, flagged_at, flagged_reason, href}. Used
    by the Issues page Flagged section."""
    rows: list[dict] = []
    for n in load_depgraph_nodes():
        if not n.get("flagged"):
            continue
        rows.append({
            "id": n["id"],
            "kind": n.get("kind", "—"),
            "title": n.get("title") or n["id"].rsplit("::", 1)[-1],
            "flagged_by": n.get("flagged_by"),
            "flagged_at": n.get("flagged_at"),
            "flagged_reason": n.get("flagged_reason"),
            "href": f"/graph/node/{n['id']}",
        })
    lg = load_logigraph_nodes()
    for r in lg["rules"]:
        if not r.get("flagged"):
            continue
        rows.append({
            "id": r["id"],
            "kind": "rule",
            "title": r.get("title", r["id"]),
            "flagged_by": r.get("flagged_by"),
            "flagged_at": r.get("flagged_at"),
            "flagged_reason": r.get("flagged_reason"),
            "href": f"/graph/rule/{r['id']}",
        })
    for o in lg["domain"]:
        if not o.get("flagged"):
            continue
        rows.append({
            "id": o["id"],
            "kind": "domain",
            "title": o.get("title", o["id"]),
            "flagged_by": o.get("flagged_by"),
            "flagged_at": o.get("flagged_at"),
            "flagged_reason": o.get("flagged_reason"),
            "href": f"/graph/domain/{o['id']}",
        })
    for p in lg.get("processes", []):
        if not p.get("flagged"):
            continue
        rows.append({
            "id": p["id"],
            "kind": "process",
            "title": p.get("title", p["id"]),
            "flagged_by": p.get("flagged_by"),
            "flagged_at": p.get("flagged_at"),
            "flagged_reason": p.get("flagged_reason"),
            "href": f"/graph/process/{p['id']}",
        })
    rows.sort(key=lambda r: (r["kind"], r["id"]))
    return rows


def _start_of_day_utc(days_ago: int = 0) -> float:
    now = dt.datetime.now(dt.timezone.utc)
    start = dt.datetime(now.year, now.month, now.day, tzinfo=dt.timezone.utc)
    start -= dt.timedelta(days=days_ago)
    return start.timestamp()


def _count_node_files_since(root: Path, since_ts: float) -> int:
    """Count *.json node files under root with mtime >= since_ts."""
    if not root.exists():
        return 0
    return sum(
        1 for p in root.rglob("*.json")
        if "_index" not in p.parts and "_meta.json" != p.name and p.stat().st_mtime >= since_ts
    )


def _count_jsonl_since(path: Path, since_ts: float, predicate=None) -> int:
    if not path.exists():
        return 0
    n = 0
    for line in path.read_text(errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts_raw = row.get("ts")
        if not ts_raw:
            continue
        try:
            ts = dt.datetime.fromisoformat(ts_raw.replace("Z", "+00:00")).timestamp()
        except (TypeError, ValueError):
            continue
        if ts < since_ts:
            continue
        if predicate and not predicate(row):
            continue
        n += 1
    return n


def _drafts_authored_since(since_ts: float) -> int:
    """Dossiers whose status==llm_drafted whose file mtime is in window."""
    n = 0
    for kind_dir in (DEPGRAPH / "dossiers", LOGIGRAPH / "dossiers"):
        if not kind_dir.exists():
            continue
        for p in kind_dir.rglob("*.md"):
            if p.stat().st_mtime < since_ts:
                continue
            text = p.read_text(errors="ignore")[:512]
            if "llm_drafted" in text or "definition_status: llm_drafted" in text:
                n += 1
    return n


def _drift_events_since(since_ts: float) -> int:
    """Read _meta.json flags; count entries with discovered_at >= since_ts
    and kind in {drift, defect}."""
    meta = load_meta()
    n = 0
    for label in ("depgraph", "logigraph"):
        flags = meta.get(label, {}).get("flags") or []
        for f in flags:
            kind = f.get("kind")
            if kind not in ("drift", "defect"):
                continue
            ts_raw = f.get("discovered_at")
            if not ts_raw:
                continue
            try:
                ts = dt.datetime.fromisoformat(ts_raw.replace("Z", "+00:00")).timestamp()
            except (TypeError, ValueError):
                continue
            if ts >= since_ts:
                n += 1
    return n


def _rules_authored_since(since_ts: float) -> int:
    """Rule node files (kind=rule) with mtime in window."""
    rule_dir = LOGIGRAPH_NODES / "rules"
    return _count_node_files_since(rule_dir, since_ts)


def activity_summary() -> dict:
    """Today / 7-day sparkline / 30-day rollup for the dashboard activity strip."""
    today_start = _start_of_day_utc(0)
    today = {
        "nodes_added": _count_node_files_since(DEPGRAPH_NODES, today_start),
        "drafts_authored": _drafts_authored_since(today_start),
        "drift_events": _drift_events_since(today_start),
        "rules_authored": _rules_authored_since(today_start),
    }
    spark: list[int] = []
    for d in range(6, -1, -1):  # oldest first
        start = _start_of_day_utc(d)
        end = _start_of_day_utc(d - 1) if d > 0 else dt.datetime.now(dt.timezone.utc).timestamp() + 1
        n = sum(
            1 for p in DEPGRAPH_NODES.rglob("*.json")
            if "_index" not in p.parts and p.name != "_meta.json"
            and start <= p.stat().st_mtime < end
        )
        spark.append(n)
    thirty_start = _start_of_day_utc(30)
    thirty_day = {
        "nodes_added": _count_node_files_since(DEPGRAPH_NODES, thirty_start),
        "drafts_reviewed": _count_jsonl_since(
            LOGIGRAPH / "telemetry" / "acknowledgments.jsonl", thirty_start
        ),
        "drift_events": _drift_events_since(thirty_start),
    }
    return {"today": today, "week_sparkline": spark, "thirty_day": thirty_day}


def _read_jsonl(path: Path):
    if not path.exists():
        return
    for line in path.read_text(errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def _telemetry_stats(window_days: int = 30) -> dict:
    since = _start_of_day_utc(window_days)
    prev_since = _start_of_day_utc(window_days * 2)
    inj_count = 0
    prev_inj_count = 0
    ack_count = 0
    rule_fires: dict[str, int] = {}
    acked_keys: set[tuple[str, str]] = set()
    inj_keys_total: set[tuple[str, str]] = set()

    for src in (DEPGRAPH / "telemetry" / "injections.jsonl",
                LOGIGRAPH / "telemetry" / "injections.jsonl"):
        for row in _read_jsonl(src):
            ts_raw = row.get("ts")
            try:
                ts = dt.datetime.fromisoformat(ts_raw.replace("Z", "+00:00")).timestamp()
            except (TypeError, AttributeError, ValueError):
                continue
            rid = row.get("rule_id")
            nid = row.get("node_id")
            if ts >= since:
                inj_count += 1
                if rid:
                    rule_fires[rid] = rule_fires.get(rid, 0) + 1
                if nid and rid:
                    inj_keys_total.add((nid, rid))
            elif prev_since <= ts < since:
                prev_inj_count += 1

    for src in (DEPGRAPH / "telemetry" / "acknowledgments.jsonl",
                LOGIGRAPH / "telemetry" / "acknowledgments.jsonl"):
        for row in _read_jsonl(src):
            ts_raw = row.get("ts")
            try:
                ts = dt.datetime.fromisoformat(ts_raw.replace("Z", "+00:00")).timestamp()
            except (TypeError, AttributeError, ValueError):
                continue
            if ts < since:
                continue
            ack_count += 1
            nid, rid = row.get("node_id"), row.get("rule_id")
            if nid and rid:
                acked_keys.add((nid, rid))

    ack_rate = round((ack_count / inj_count) * 100) if inj_count else 0
    trend = round(((inj_count - prev_inj_count) / prev_inj_count) * 100) if prev_inj_count else 0

    # Dead rules: rule node files that never fired in the window.
    rules_dir = LOGIGRAPH_NODES / "rules"
    dead = 0
    if rules_dir.exists():
        for p in rules_dir.glob("*.json"):
            try:
                rid = json.loads(p.read_text()).get("id")
            except (OSError, json.JSONDecodeError):
                continue
            if rid and rid not in rule_fires:
                dead += 1

    # Never-acknowledged dossiers: nodes that have a dossier but never appear in acks.
    never_acked = 0
    acked_nids = {nid for (nid, _r) in acked_keys}
    for n in load_depgraph_nodes():
        if n.get("dossier") and n["id"] not in acked_nids:
            never_acked += 1

    hottest = sorted(rule_fires.items(), key=lambda kv: kv[1], reverse=True)[:3]
    return {
        "injections_30d": inj_count,
        "ack_rate_pct": ack_rate,
        "trend_pct": trend,
        "dead_rules": dead,
        "never_acked_dossiers": never_acked,
        "rule_fires": rule_fires,
        "hottest": [{"id": rid, "count": n} for rid, n in hottest],
    }


def _calibration_summary() -> dict:
    """Read the most-recent calibration run dir under LOGIGRAPH/calibration/runs/.
    Returns accuracy %, pass/fail counts, drifted rule ids, prev-run delta."""
    runs_dir = LOGIGRAPH / "calibration" / "runs"
    if not runs_dir.exists():
        return {"accuracy_pct": None, "regressions": 0, "last_run_id": None, "drifted_rules": [], "prev_delta_pp": 0}
    runs = sorted([p for p in runs_dir.iterdir() if p.is_dir()], reverse=True)
    if not runs:
        return {"accuracy_pct": None, "regressions": 0, "last_run_id": None, "drifted_rules": [], "prev_delta_pp": 0}

    def _score(run_dir: Path) -> tuple[int, int, list[str]]:
        passes = fails = 0
        drifted: list[str] = []
        for result_path in run_dir.glob("*/result.json"):
            try:
                row = json.loads(result_path.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            if row.get("overall") == "pass":
                passes += 1
            else:
                fails += 1
                pid = row.get("prompt_id")
                if pid:
                    drifted.append(pid)
        return passes, fails, drifted

    p, f, drifted = _score(runs[0])
    total = p + f
    acc = round((p / total) * 100) if total else 0
    prev_acc = None
    if len(runs) > 1:
        pp, pf, _ = _score(runs[1])
        prev_total = pp + pf
        if prev_total:
            prev_acc = round((pp / prev_total) * 100)
    return {
        "accuracy_pct": acc,
        "regressions": f,
        "last_run_id": runs[0].name,
        "drifted_rules": drifted,
        "prev_delta_pp": (acc - prev_acc) if prev_acc is not None else 0,
    }


def graph_health() -> dict:
    t = _telemetry_stats(30)
    return {
        "telemetry": {k: t[k] for k in ("injections_30d", "ack_rate_pct", "trend_pct", "dead_rules", "never_acked_dossiers")},
        "calibration": _calibration_summary(),
        "hottest_rules": t["hottest"],
    }


def _namespaces_from_ids(ids: list[str]) -> list[str]:
    """For ids of the form `kind::namespace::name`, return unique namespaces."""
    out: set[str] = set()
    for i in ids:
        parts = i.split("::")
        if len(parts) >= 3:
            out.add(parts[1])
    return sorted(out)


def _claimed_repos_for_rules(rules: list[dict]) -> int:
    """Count unique repos appearing in any rule's claims_code list."""
    repos: set[str] = set()
    for r in rules:
        for c in r.get("claims_code", []) or []:
            did = c.get("depgraph_id") or ""
            head = did.split("::", 1)[0]
            if head:
                repos.add(head)
    return len(repos)


def _spans_repos_for_processes(procs: list[dict]) -> int:
    """Count unique repos appearing in any process step's claims_code list."""
    repos: set[str] = set()
    for p in procs:
        for step in p.get("steps", []) or []:
            for c in step.get("claims_code", []) or []:
                did = c.get("depgraph_id") or ""
                head = did.split("::", 1)[0]
                if head:
                    repos.add(head)
    return len(repos)


def cross_cutting_summary() -> dict:
    lg = load_logigraph_nodes()
    rules = lg["rules"]
    domain = lg["domain"]
    procs = lg["processes"]
    referenced_by = 0
    for r in rules:
        if r.get("references_domain"):
            referenced_by += len(r["references_domain"])
    for p in procs:
        for step in p.get("steps", []) or []:
            if step.get("references_domain"):
                referenced_by += len(step["references_domain"])
    subkinds: dict[str, int] = {}
    for o in domain:
        sk = o.get("subkind") or "—"
        subkinds[sk] = subkinds.get(sk, 0) + 1
    return {
        "rules": {
            "count": len(rules),
            "claimed_repos": _claimed_repos_for_rules(rules),
            "namespaces": _namespaces_from_ids([r["id"] for r in rules]),
        },
        "domain": {
            "count": len(domain),
            "subkinds": subkinds,
            "referenced_by": referenced_by,
        },
        "processes": {
            "count": len(procs),
            "names": [p.get("title") or p["id"].rsplit("::", 1)[-1] for p in procs[:6]],
            "spans_repos": _spans_repos_for_processes(procs),
        },
    }


# ---------------------------------------------------------------------------
# Repo activity (commits, sparkline, classification)
# ---------------------------------------------------------------------------


def _repo_path(basename: str) -> Path | None:
    """Resolve a tracked-repo basename to its filesystem path.
    Convention: HOME/<basename> (matches `commits_30d` below)."""
    p = HOME / basename
    return p if (p / ".git").exists() else None


def _git_log_dates(repo: Path, since: str) -> list[str]:
    """Run `git log --since=<since> --format=%cd --date=format:%Y-%m-%d`. Best-effort."""
    try:
        out = subprocess.run(
            ["git", "log", f"--since={since}", "--format=%cd", "--date=format:%Y-%m-%d"],
            cwd=str(repo), capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    return [l.strip() for l in out.stdout.splitlines() if l.strip()]


def _git_last_push_age_days(repo: Path) -> int | None:
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%ct"],
            cwd=str(repo), capture_output=True, text=True, timeout=5,
        )
        ts = int(out.stdout.strip() or 0)
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    if not ts:
        return None
    return int((dt.datetime.now(dt.timezone.utc).timestamp() - ts) // 86400)


def _classify(last_push_age: int | None, has_inbound_deps: bool) -> str:
    if last_push_age is None:
        return "unknown"
    if last_push_age <= 7:
        return "active"
    if last_push_age >= 180 and not has_inbound_deps:
        return "dead-candidate"
    return "dormant"


def _today_node_delta_for_repo(basename: str) -> int:
    today_start = _start_of_day_utc(0)
    n = 0
    for p in DEPGRAPH_NODES.rglob("*.json"):
        if "_index" in p.parts or p.name == "_meta.json":
            continue
        if p.stat().st_mtime < today_start:
            continue
        try:
            row = json.loads(p.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        src = (row.get("source") or {}).get("repo")
        if src == basename:
            n += 1
    return n


def repo_activity(basename: str) -> dict:
    repo = _repo_path(basename)
    if repo is None:
        return {
            "commits_7d": 0,
            "commits_30d": 0,
            "sparkline": [0] * 7,
            "today_node_delta": 0,
            "classification": "unknown",
            "last_push_age_days": None,
        }
    dates = _git_log_dates(repo, "30 days ago")
    # 7-day sparkline (oldest first)
    today = dt.datetime.now(dt.timezone.utc).date()
    spark = []
    for d in range(6, -1, -1):
        target = (today - dt.timedelta(days=d)).isoformat()
        spark.append(sum(1 for x in dates if x == target))
    commits_7d = sum(spark)
    commits_30d = len(dates)
    age = _git_last_push_age_days(repo)
    # Inbound deps gate is filled in by repo_summary; default False here.
    classification = _classify(age, has_inbound_deps=False)
    return {
        "commits_7d": commits_7d,
        "commits_30d": commits_30d,
        "sparkline": spark,
        "today_node_delta": _today_node_delta_for_repo(basename),
        "classification": classification,
        "last_push_age_days": age,
    }


_EXT_TO_LANG = {
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".js": "JavaScript", ".jsx": "JavaScript",
    ".py": "Python",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".java": "Java",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".cs": "C#",
    ".php": "PHP",
}


def _framework_hints(repo: Path) -> list[str]:
    hints: list[str] = []
    pkg = repo / "package.json"
    if pkg.exists():
        try:
            row = json.loads(pkg.read_text())
        except (OSError, json.JSONDecodeError):
            row = {}
        deps = {**(row.get("dependencies") or {}), **(row.get("devDependencies") or {})}
        if "next" in deps:
            hints.append("Next")
        if "react" in deps:
            hints.append("React")
        if "vitest" in deps:
            hints.append("Vitest")
        if "@playwright/test" in deps or "playwright" in deps:
            hints.append("Playwright")
    pyproj = repo / "pyproject.toml"
    reqs = repo / "requirements.txt"
    py_text = ""
    if pyproj.exists():
        py_text += pyproj.read_text(errors="ignore")
    if reqs.exists():
        py_text += reqs.read_text(errors="ignore")
    if "fastapi" in py_text.lower():
        hints.append("FastAPI")
    if "sqlalchemy" in py_text.lower():
        hints.append("SQLAlchemy")
    if "pytest" in py_text.lower():
        hints.append("pytest")
    return hints


def repo_languages(basename: str) -> list[dict]:
    repo = _repo_path(basename)
    if repo is None:
        return []
    counts: dict[str, int] = {}
    for p in repo.rglob("*"):
        if not p.is_file():
            continue
        if any(part.startswith(".") or part == "node_modules" for part in p.parts):
            continue
        lang = _EXT_TO_LANG.get(p.suffix)
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
    primary = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:2]
    out = [{"label": lang, "hint": "primary"} for lang, _ in primary]
    for h in _framework_hints(repo)[:4 - len(out)]:
        out.append({"label": h, "hint": "framework"})
    return out


def repo_areas(basename: str) -> list[dict]:
    """Return top-level directories in `basename` that contain at least one
    tracked node, ordered by node_count desc. Each entry: {dir, node_count}."""
    counts: dict[str, int] = {}
    for n in load_depgraph_nodes():
        src = (n.get("source") or {})
        if src.get("repo") != basename:
            continue
        path = src.get("path") or ""
        head = path.split("/", 1)[0] if "/" in path else path
        if not head:
            continue
        counts[head] = counts.get(head, 0) + 1
    return [
        {"dir": d, "node_count": c}
        for d, c in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    ]


def repo_dep_counts(basename: str) -> dict:
    """Compute three counts:
      - inbound_repos: # of other tracked repos with nodes whose dependents
        index points into a node belonging to `basename`.
      - outbound_repos: # of other tracked repos whose nodes are referenced
        by nodes in `basename` (via the by_target dependents index — symmetric).
      - external_pkgs: # of packages declared in `basename/package.json` deps
        + `basename/requirements.txt` lines + `basename/pyproject.toml` deps.
    """
    inbound: set[str] = set()
    outbound: set[str] = set()
    dependents = load_dependents()  # by_target: target_id -> [dependent dicts]
    nodes = load_depgraph_nodes()
    in_my_repo = {n["id"] for n in nodes if (n.get("source") or {}).get("repo") == basename}
    for target_id, dependers in dependents.items():
        target_repo = target_id.split("::", 1)[0]
        for d in dependers:
            dep_repo = (d.get("id") or "").split("::", 1)[0]
            if not dep_repo or dep_repo == target_repo:
                continue
            if target_repo == basename and dep_repo != basename:
                inbound.add(dep_repo)
            if dep_repo == basename and target_repo != basename:
                outbound.add(target_repo)

    ext = 0
    repo = _repo_path(basename)
    if repo is not None:
        pkg = repo / "package.json"
        if pkg.exists():
            try:
                row = json.loads(pkg.read_text())
                ext += len(row.get("dependencies") or {})
                ext += len(row.get("devDependencies") or {})
            except (OSError, json.JSONDecodeError):
                pass
        reqs = repo / "requirements.txt"
        if reqs.exists():
            ext += sum(
                1 for l in reqs.read_text(errors="ignore").splitlines()
                if l.strip() and not l.strip().startswith("#")
            )
        pyproj = repo / "pyproject.toml"
        if pyproj.exists():
            txt = pyproj.read_text(errors="ignore")
            # crude: count lines under a [project] dependencies array; good enough for v1.
            in_deps = False
            for line in txt.splitlines():
                s = line.strip()
                if s.startswith("dependencies"):
                    in_deps = True
                    continue
                if in_deps:
                    if s.startswith("]"):
                        in_deps = False
                        continue
                    if s.startswith('"') or s.startswith("'"):
                        ext += 1
    return {"inbound_repos": len(inbound), "outbound_repos": len(outbound), "external_pkgs": ext}


def repo_cross_cuts(basename: str) -> dict:
    """List the rule/process/domain ids that touch any node in `basename`.
    Returns id-lists (not counts) so the repo card can name a few inline."""
    lg = load_logigraph_nodes()
    rule_ids: set[str] = set()
    proc_ids: set[str] = set()
    domain_ids: set[str] = set()

    for r in lg["rules"]:
        for c in r.get("claims_code", []) or []:
            did = c.get("depgraph_id") or ""
            if did.startswith(f"{basename}::"):
                rule_ids.add(r["id"])
                for ref in (r.get("references_domain") or []):
                    domain_ids.add(ref)
                break
    for p in lg["processes"]:
        for step in p.get("steps", []) or []:
            hit = False
            for c in step.get("claims_code", []) or []:
                did = c.get("depgraph_id") or ""
                if did.startswith(f"{basename}::"):
                    proc_ids.add(p["id"])
                    for ref in (step.get("references_domain") or []):
                        domain_ids.add(ref)
                    hit = True
                    break
            if hit:
                break
    return {
        "rules": sorted(rule_ids),
        "processes": sorted(proc_ids),
        "domain": sorted(domain_ids),
    }
