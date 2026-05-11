"""Load depgraph + logigraph indexes into in-memory dicts.

Single source of truth: the JSON files on disk under ~/concorda/depgraph and
~/concorda/logigraph. We re-read on each request so the UI tracks regen
output without restart. At ~1500 nodes the cost is negligible (~50ms cold).
"""
from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any

HOME = Path.home()
DEPGRAPH = HOME / "concorda" / "depgraph"
LOGIGRAPH = HOME / "concorda" / "logigraph"

DEPGRAPH_NODES = DEPGRAPH / "nodes"
LOGIGRAPH_NODES = LOGIGRAPH / "nodes"


def _tier_of(fan_out: int) -> str:
    if fan_out >= 10:
        return "A"
    if fan_out >= 3:
        return "B"
    return "C"


def _dossier_state(node: dict, root: Path) -> str:
    """Match depgraph CLI's _dossier_state semantics."""
    rel = node.get("dossier")
    if not rel:
        return "missing"
    full = root / rel
    if not full.exists():
        return "missing"
    text = full.read_text()
    pinned = None
    status = "current"
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("status:"):
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
    """Returns {'rules': [...], 'ontology': [...]} with derived dossier_state."""
    out: dict[str, list[dict]] = {"rules": [], "ontology": []}
    for kind, sub in (("rules", "rules"), ("ontology", "ontology")):
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
            if "fan_out" not in node:
                node["fan_out"] = len(node.get("claims_code") or [])
            out[kind].append(node)
    return out


def load_node_by_id(node_id: str) -> dict | None:
    for n in load_depgraph_nodes():
        if n["id"] == node_id:
            return n
    return None


def load_rule_by_id(rule_id: str) -> dict | None:
    for n in load_logigraph_nodes()["rules"]:
        if n["id"] == rule_id:
            return n
    return None


def load_ontology_by_id(ont_id: str) -> dict | None:
    for n in load_logigraph_nodes()["ontology"]:
        if n["id"] == ont_id:
            return n
    return None


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
    "ontology": "ontology",
}


def coverage_matrix() -> dict[str, dict[str, dict[str, int]]]:
    """{ kind: { tier: { state: count } } }
    states: current, llm_drafted, unreviewed, stale, missing
    Includes both depgraph kinds and logigraph kinds (rules+ontology, all Tier ?).
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
    for kind in ("rules", "ontology"):
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

INJECTIONS = LOGIGRAPH / "telemetry" / "injections.jsonl"
ACKS = LOGIGRAPH / "telemetry" / "acknowledgments.jsonl"


def telemetry_for_rule(rule_id: str, days: int = 7) -> dict[str, Any]:
    cutoff = time.time() - days * 86400
    inj = 0
    ack = 0
    last_fired: str | None = None
    if INJECTIONS.exists():
        for line in INJECTIONS.read_text().splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rule_id not in (row.get("rule_ids") or []):
                continue
            ts = row.get("ts", "")
            try:
                # ISO8601 → epoch
                from datetime import datetime
                t = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
            except (ValueError, TypeError):
                t = 0
            if t < cutoff:
                continue
            inj += 1
            if not last_fired or ts > last_fired:
                last_fired = ts
            if row.get("acknowledged"):
                ack += 1
    return {
        "injections_7d": inj,
        "acked_7d": ack,
        "ack_rate": (ack / inj) if inj else None,
        "last_fired": last_fired,
    }
