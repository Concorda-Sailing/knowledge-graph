"""Load depgraph + logigraph indexes into in-memory dicts.

Single source of truth: the JSON files on disk at the data dirs pointed
at by the active `Project`. graphui can serve multiple projects in one
process — each request resolves its active project via the
`_CURRENT_PROJECT` contextvar (set by the FastAPI middleware in
`main.py`), and the heavy loaders cache per-project keyed on the mtime
of that project's `nodes/_meta.json`. Reconcile writes that file at
the end of a regen, so a fresh extraction invalidates the cache
without a graphui restart.

Single-project mode (legacy systemd / dev): if `DEPGRAPH_DATA_DIR` is
set, the module exposes a default Project synthesized from the env
vars. With no env vars and no registered projects, graphui exits at
startup.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
import os
import sys
import time
import tomllib  # stdlib 3.11+
import hashlib
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from depgraph.lib.edges import (
    ACKNOWLEDGMENTS_LOG_FILENAME,
    INJECTIONS_LOG_FILENAME,
    REVERSE_INDEX_FILENAME,
)

HOME = Path.home()

# Where `kg project add` writes the registered-graphs list. The orchestrator
# hook (`kg/hook.py::_pre_edit`) reads the same file; keep them in sync.
REGISTERED_GRAPHS_PATH = HOME / ".claude" / "kg-graphs.toml"


@dataclass(frozen=True)
class Project:
    """A single tracked graph: where its data lives + a name/description
    for the UI picker. All paths are absolute and resolved."""
    id: str            # short stable key; matches kg-graphs.toml `[[graph]].name`
    name: str          # human label (may match id, may come from project.toml)
    description: str   # one-line summary, "" if unset
    graph_dir: Path    # ~/<project>-knowledge-graph
    depgraph_dir: Path
    logigraph_dir: Path

    @property
    def depgraph_nodes_dir(self) -> Path:
        return self.depgraph_dir / "nodes"

    @property
    def logigraph_nodes_dir(self) -> Path:
        return self.logigraph_dir / "nodes"


def _make_project(project_id: str, name: str, description: str, graph_dir: Path) -> Project:
    return Project(
        id=project_id,
        name=name or project_id,
        description=description or "",
        graph_dir=graph_dir,
        depgraph_dir=graph_dir / "depgraph",
        logigraph_dir=graph_dir / "logigraph",
    )


def _read_project_description(graph_dir: Path) -> tuple[str, str]:
    """Read `<graph_dir>/project.toml`'s `[project]` section. Returns
    (name, description); falls back to ("", "") when the file or the
    fields are absent. `description` is an optional field convention
    graphui surfaces — adding it to project.toml is opt-in."""
    p = graph_dir / "project.toml"
    if not p.exists():
        return "", ""
    try:
        cfg = tomllib.loads(p.read_text())
    except (OSError, tomllib.TOMLDecodeError):
        return "", ""
    proj = cfg.get("project") or {}
    return str(proj.get("name") or ""), str(proj.get("description") or "")


def list_projects() -> list[Project]:
    """Enumerate registered graphs from `~/.claude/kg-graphs.toml`.
    Falls back to a single synthetic project (id `default`) when the
    file is absent but env-var single-project mode is in use."""
    out: list[Project] = []
    if REGISTERED_GRAPHS_PATH.exists():
        try:
            cfg = tomllib.loads(REGISTERED_GRAPHS_PATH.read_text())
        except (OSError, tomllib.TOMLDecodeError):
            cfg = {}
        for entry in cfg.get("graph") or []:
            raw_path = entry.get("path")
            if not raw_path:
                continue
            graph_dir = Path(raw_path).expanduser().resolve()
            project_id = str(entry.get("name") or graph_dir.name)
            name, description = _read_project_description(graph_dir)
            out.append(_make_project(project_id, name or project_id, description, graph_dir))
    if not out and _DEFAULT_PROJECT is not None:
        out.append(_DEFAULT_PROJECT)
    out.sort(key=lambda p: p.name.lower())
    return out


def _resolve(env_var: str) -> Path | None:
    """Resolve a graph data dir from env var, else None. With no env vars
    and no registered projects we exit; the check happens after we know
    whether kg-graphs.toml has entries."""
    val = os.environ.get(env_var)
    if not val:
        return None
    return Path(val).expanduser().resolve()


from kg.shared.env import DEPGRAPH_DATA_DIR, LOGIGRAPH_DATA_DIR  # noqa: E402

_ENV_DEPGRAPH = _resolve(DEPGRAPH_DATA_DIR)
_ENV_LOGIGRAPH = _resolve(LOGIGRAPH_DATA_DIR)

# Synthesize a "default" Project from env vars when present — preserves the
# pre-multiproject startup path. graph_dir is the common parent of the two
# data dirs when they share one (the standard `~/<x>-knowledge-graph/{depgraph,
# logigraph}` layout); otherwise it falls back to depgraph_dir.parent.
_DEFAULT_PROJECT: Project | None = None
if _ENV_DEPGRAPH and _ENV_LOGIGRAPH:
    _shared = _ENV_DEPGRAPH.parent if _ENV_DEPGRAPH.parent == _ENV_LOGIGRAPH.parent else _ENV_DEPGRAPH.parent
    _name_from_toml, _desc_from_toml = _read_project_description(_shared)
    _DEFAULT_PROJECT = Project(
        id=_name_from_toml or _shared.name or "default",
        name=_name_from_toml or _shared.name or "default",
        description=_desc_from_toml,
        graph_dir=_shared,
        depgraph_dir=_ENV_DEPGRAPH,
        logigraph_dir=_ENV_LOGIGRAPH,
    )


_CURRENT_PROJECT: ContextVar[Project | None] = ContextVar("_CURRENT_PROJECT", default=None)


def current_project() -> Project:
    """Resolve the active project for this request. Reads the contextvar
    first; falls back to the env-var-synthesized default for single-project
    mode. Exits the process if neither is available — graphui needs to know
    which project to serve."""
    p = _CURRENT_PROJECT.get()
    if p is not None:
        return p
    if _DEFAULT_PROJECT is not None:
        return _DEFAULT_PROJECT
    projects = list_projects()
    if projects:
        return projects[0]
    sys.exit(
        "graphui has no project to serve — set DEPGRAPH_DATA_DIR/LOGIGRAPH_DATA_DIR "
        f"or register one with `kg project add <path>` (writes {REGISTERED_GRAPHS_PATH})."
    )


def set_current_project(project: Project | None) -> Any:
    """Bind the request's active project to the contextvar. Returns the
    token so the middleware can reset it after the request completes."""
    return _CURRENT_PROJECT.set(project)


def reset_current_project(token: Any) -> None:
    _CURRENT_PROJECT.reset(token)


# Per-project caches. Keys are the project's `depgraph_dir` (or graph_dir
# where the cache spans both subgraphs). Each value is the same
# (cache_key, value) tuple as before. cache_key is the mtime of the
# relevant `nodes/_meta.json`; reconcile rewrites that file at the end of
# every regen, so a fresh extraction invalidates the cache on the next
# request.
_DEPGRAPH_DEPS_CACHE: dict[Path, tuple[float, dict[str, list[dict]]]] = {}
_DEPGRAPH_NODES_CACHE: dict[Path, tuple[float, list[dict]]] = {}
_LOGIGRAPH_NODES_CACHE: dict[Path, tuple[float, dict[str, list[dict]]]] = {}
_META_CACHE: dict[Path, tuple[tuple[float, float], dict[str, Any]]] = {}
_REPO_AGGREGATES_CACHE: dict[Path, tuple[tuple[float, float], dict[str, dict]]] = {}


def _depgraph_meta_mtime() -> float:
    try:
        return (current_project().depgraph_nodes_dir / "_meta.json").stat().st_mtime
    except OSError:
        return 0.0


def _logigraph_meta_mtime() -> float:
    try:
        return (current_project().logigraph_nodes_dir / "_meta.json").stat().st_mtime
    except OSError:
        return 0.0

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
_FRAMEWORK_ROOT = _GRAPHUI_TOOL_ROOT.parent  # ~/tools/knowledge-graph
_DEPGRAPH_TOOL_ROOT = _FRAMEWORK_ROOT / "depgraph"
if str(_FRAMEWORK_ROOT) not in sys.path:
    sys.path.insert(0, str(_FRAMEWORK_ROOT))
from depgraph.lib.rollup import (  # noqa: E402
    resolve_anchor,
    compute_rollup,
    Rollup,
    AnchorResult,
)
from depgraph.lib.config import project_repos as _depgraph_project_repos  # noqa: E402


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
    """Count commits in the last 30d touching a file. Cached for 5 minutes.

    `repo` is the v2 `source.repo` value (the `[repos.<key>]` key from
    project.toml, NOT a directory basename), resolved via `_repo_path` so
    `path = "~/<project>-api"` works (#25).
    """
    if not repo or not rel_path:
        return 0
    key = (repo, rel_path)
    now = time.time()
    if key in _COMMITS_CACHE:
        ts, val = _COMMITS_CACHE[key]
        if now - ts < 300:
            return val
    repo_root = _repo_path(repo)
    if repo_root is None or not (repo_root / ".git").exists():
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
    proj = current_project()
    mt = _depgraph_meta_mtime()
    cached = _DEPGRAPH_DEPS_CACHE.get(proj.depgraph_dir)
    if cached is not None and cached[0] == mt:
        return cached[1]
    p = proj.depgraph_nodes_dir / "_index" / REVERSE_INDEX_FILENAME
    if not p.exists():
        out: dict[str, list[dict]] = {}
    else:
        idx = json.loads(p.read_text())
        # v2 is flat {target: [...]}, v1 wraps in {"schema_version": 1, "by_target": {...}}.
        if isinstance(idx, dict) and "by_target" in idx and "schema_version" in idx:
            out = idx.get("by_target") or {}
        else:
            out = idx if isinstance(idx, dict) else {}
    _DEPGRAPH_DEPS_CACHE[proj.depgraph_dir] = (mt, out)
    return out


def load_logigraph_by_code() -> dict[str, list[str]]:
    """Map of depgraph node-id (or HTTP route) -> [rule_id, ...]."""
    p = current_project().logigraph_nodes_dir / "_index" / "by_code.json"
    if not p.exists():
        return {}
    idx = json.loads(p.read_text())
    return idx.get("by_target") or {}


def load_meta() -> dict[str, Any]:
    """Read both meta files."""
    proj = current_project()
    key = (_depgraph_meta_mtime(), _logigraph_meta_mtime())
    cached = _META_CACHE.get(proj.graph_dir)
    if cached is not None and cached[0] == key:
        return cached[1]
    out: dict[str, Any] = {"depgraph": {}, "logigraph": {}}
    for label, p in (
        ("depgraph", proj.depgraph_nodes_dir / "_meta.json"),
        ("logigraph", proj.logigraph_nodes_dir / "_meta.json"),
    ):
        if p.exists():
            try:
                out[label] = json.loads(p.read_text())
            except (OSError, json.JSONDecodeError):
                pass
    _META_CACHE[proj.graph_dir] = (key, out)
    return out


def load_depgraph_nodes() -> list[dict]:
    """Read every depgraph node file and enrich with derived fields:
    fan_out, tier, dossier_state, commits_30d. Sorted by id."""
    proj = current_project()
    mt = _depgraph_meta_mtime()
    cached = _DEPGRAPH_NODES_CACHE.get(proj.depgraph_dir)
    if cached is not None and cached[0] == mt:
        return cached[1]
    deps = load_dependents()
    nodes: list[dict] = []
    for nf in proj.depgraph_nodes_dir.rglob("*.json"):
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
        d["dossier_state"] = _dossier_state(d, proj.depgraph_dir)
        d["_node_file"] = str(nf.relative_to(proj.depgraph_dir))
        src = d.get("source") or {}
        nodes.append(d)
    nodes.sort(key=lambda n: n["id"])
    _DEPGRAPH_NODES_CACHE[proj.depgraph_dir] = (mt, nodes)
    return nodes


def load_logigraph_nodes() -> dict[str, list[dict]]:
    """Returns {'rules': [...], 'domain': [...], 'processes': [...]} with
    derived dossier_state."""
    proj = current_project()
    mt = _logigraph_meta_mtime()
    cached = _LOGIGRAPH_NODES_CACHE.get(proj.logigraph_dir)
    if cached is not None and cached[0] == mt:
        return cached[1]
    out: dict[str, list[dict]] = {"rules": [], "domain": [], "processes": []}
    for kind, sub in (("rules", "rules"), ("domain", "domain"), ("processes", "processes")):
        d = proj.logigraph_nodes_dir / sub
        if not d.is_dir():
            continue
        for nf in sorted(d.glob("*.json")):
            try:
                node = json.loads(nf.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            node["dossier_state"] = _dossier_state(node, proj.logigraph_dir)
            node["_node_file"] = str(nf.relative_to(proj.logigraph_dir))
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
    _LOGIGRAPH_NODES_CACHE[proj.logigraph_dir] = (mt, out)
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


def _configured_repo_basenames() -> set[str]:
    """The set of repo identifiers configured in depgraph/project.toml.

    These are the `[repos.<key>]` keys — the same string the extractor
    stores in each node's `source.repo`. Used to inject empty-corpus
    placeholder rows for repos whose extractor produced zero primitives.
    Empty when project.toml is missing or has no `[repos.*]` tables.

    Earlier versions returned `{basename: key}`, where basename was the
    path's last segment. That mismatched what extractors write to
    `source.repo` (always the key), so the placeholder injection produced
    a duplicate row keyed by basename next to the real row keyed by the
    `[repos.<key>]` name (#24).
    """
    proj = current_project()
    try:
        repos = _depgraph_project_repos(proj.depgraph_dir)
    except Exception:
        # Malformed project.toml shouldn't crash the dashboard.
        return set()
    return set(repos.keys())


def repo_summary() -> list[dict]:
    """One entry per source repo seen in depgraph nodes' source.repo field,
    PLUS one entry for every `[repos.<key>]` configured in project.toml that
    produced zero primitives — those would otherwise vanish from the dashboard
    and the user has no signal that extraction failed (#21).

    Returns: [{basename, node_count, state_counts: {current: n, ...},
               current_pct, has_stale, kinds: [{kind, count}, ...],
               empty_corpus: bool}]
    Sorted by node_count desc.

    All graph-derived per-repo aggregates (areas, cross-repo dep counts,
    cross_cuts) come from a single cached pass via `_repo_aggregates`; only
    activity (git log), languages (filesystem walk), and external_pkgs
    (per-repo package.json) require any per-repo I/O.
    """
    aggregates = _repo_aggregates()
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

    # Inject configured-but-empty repos. Without this, a TS repo whose
    # extractor crashed at regen time silently disappears from the dashboard.
    for repo_key in _configured_repo_basenames():
        if repo_key not in by_repo:
            by_repo[repo_key] = {
                "basename": repo_key,
                "node_count": 0,
                "state_counts": _empty_state_counts(),
                "kinds": {},
            }

    out = []
    for r in by_repo.values():
        sc = r["state_counts"]
        current = sc.get("current", 0)
        total = r["node_count"]
        r["current_pct"] = round(100 * current / total) if total else 0
        r["has_stale"] = sc.get("stale", 0) > 0
        r["empty_corpus"] = (total == 0)
        r["kinds"] = sorted(
            [{"kind": k, "count": v} for k, v in r["kinds"].items()],
            key=lambda x: -x["count"],
        )
        agg = aggregates.get(r["basename"], {})
        r["activity"] = repo_activity(r["basename"])
        r["languages"] = repo_languages(r["basename"])
        r["areas"] = agg.get("areas", [])
        dep_nodes = agg.get("dep_counts_nodes") or {
            "inbound_repos": 0, "outbound_repos": 0,
            "inbound_edges": 0, "outbound_edges": 0,
        }
        r["dep_counts"] = {**dep_nodes, "external_pkgs": _repo_external_pkgs(r["basename"])}
        r["cross_cuts"] = agg.get("cross_cuts") or {"rules": [], "processes": [], "domain": []}
        # dead_code_score: low push frequency + zero inbound + many stale claims.
        # Use total inbound edges (any source), not cross-repo repo count —
        # otherwise every single-repo project scores as dead-candidate.
        age = r["activity"]["last_push_age_days"] or 0
        inbound_edges = r["dep_counts"]["inbound_edges"]
        stale = r["state_counts"].get("stale", 0)
        score = (age // 30) + (10 if inbound_edges == 0 else 0) + stale
        r["dead_code_score"] = score
        # Override classification for empty configured repos — "extractor
        # produced nothing" is its own state, distinct from old code that
        # nobody depends on.
        if r["empty_corpus"]:
            r["activity"]["classification"] = "empty"
        elif r["activity"]["classification"] == "dormant" and age >= 180 and inbound_edges == 0:
            r["activity"]["classification"] = "dead-candidate"
        out.append(r)
    out.sort(key=lambda r: (-r["node_count"], r["basename"]))
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


def _extraction_ran(meta: dict) -> bool:
    """True iff at least one of depgraph/logigraph has written `_meta.json`
    for this project (#63).

    `load_meta()` returns `{"depgraph": {}, "logigraph": {}}` both when
    meta files are absent and when they're empty, so a non-empty dict on
    either side is the canonical "regen has run at least once" signal."""
    return bool(meta.get("depgraph") or meta.get("logigraph"))


def corpus_flags() -> dict:
    """Return all corpus flags partitioned by tracked/fresh and grouped by
    kind within each. Reads logigraph `_meta.json::flags` written by
    reconcile AND synthesizes flags from depgraph `_meta.json` schema-
    validation counters (`primitive_error_count`, `orphan_edge_count`,
    `slug_collision_count`, plus any `edge_errors` in `validation_report`)
    so schema-level defects show up on the Issues page (#23).

    Shape:
      {
        "fresh":   [{kind, count, items}, ...],
        "tracked": [{kind, count, items}, ...],
        "count_fresh": N,
        "count_tracked": N,
        "extraction_ran": bool,   # #63: distinguish "no data yet" from "clean"
      }
    """
    meta = load_meta()
    flags = list((meta.get("logigraph") or {}).get("flags") or [])
    if not isinstance(flags, list):
        flags = []
    flags.extend(_depgraph_validation_flags(meta.get("depgraph") or {}))
    fresh_flat = [f for f in flags if not f.get("tracked")]
    tracked_flat = [f for f in flags if f.get("tracked")]
    return {
        "fresh": _group_flags_by_kind(fresh_flat),
        "tracked": _group_flags_by_kind(tracked_flat),
        "count_fresh": len(fresh_flat),
        "count_tracked": len(tracked_flat),
        "extraction_ran": _extraction_ran(meta),
    }


def _depgraph_validation_flags(depgraph_meta: dict) -> list[dict]:
    """Synthesize defect flags from depgraph `_meta.json` counters.

    Returns one flag per non-zero counter so the Issues page can group
    them under the `defect` kind. The validation_report itself can be
    expensive to enumerate (thousands of edge_errors), so we surface the
    counts as a single summary entry per class — the user goes to
    `kg depgraph validate` for the detail dump.

    Flags are emitted as `tracked=False` so they appear in the "fresh"
    bucket (this is corpus-state right now, not historical drift).
    """
    out: list[dict] = []
    counters = (
        ("primitive_error_count", "schema_invalid_primitive",
         "{n} primitive(s) violate the v2 schema"),
        ("orphan_edge_count", "orphan_edge",
         "{n} edge(s) point at a target neither in the corpus nor external::"),
        ("slug_collision_count", "slug_collision",
         "{n} primitive id(s) slugify to the same filename"),
    )
    for field, code, msg in counters:
        n = depgraph_meta.get(field) or 0
        if not n:
            continue
        out.append({
            "code": code,
            "kind": "defect",
            "severity": "critical" if field == "slug_collision_count" else "high",
            "count": n,
            "message": msg.format(n=n),
            "remedy": "Run `kg depgraph validate` for the full detail listing.",
            "tracked": False,
        })
    # edge_errors aren't surfaced as their own counter — read from the
    # validation_report. Same summary shape.
    report = depgraph_meta.get("validation_report") or {}
    edge_errors = report.get("edge_errors") if isinstance(report, dict) else None
    if edge_errors:
        out.append({
            "code": "edge_kind_invalid",
            "kind": "defect",
            "severity": "high",
            "count": len(edge_errors),
            "message": f"{len(edge_errors)} edge(s) violate the EdgeKind source/target rules",
            "remedy": "Run `kg depgraph validate` for the full detail listing.",
            "tracked": False,
        })
    return out


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


# Path prefixes that mark a node as "common" infrastructure rather than
# domain feature code. Conservative: only obvious shared-utility folders.
# Everything else is treated as domain-specific so the repo view defaults
# to surfacing feature code first.
_COMMON_PATH_PREFIXES = (
    "src/components/ui/",
    "src/lib/",
    "src/hooks/",
    "lib/",
    "utils/",
)


def is_common_path(path: str) -> bool:
    return any(path.startswith(p) for p in _COMMON_PATH_PREFIXES)


def nodes_for_repo(
    basename: str,
    kind: str | None = None,
    area: str | None = None,
    tier: str | None = None,
    state: str | None = None,
    sort: str = "fan_out",
) -> list[dict]:
    """Flat node list for a repo, ready to feed the universal `_node_list.html`
    partial. Each row carries the keys the partial reads (`id`, `title`, `kind`,
    `fan_out`, `state`, `href`, `id`, plus `area`, `tier`, and `common`).

    Filters: kind, area (top-level directory), tier (A/B/C), state, sort (fan_out|title|state).
    """
    out: list[dict] = []
    for n in load_depgraph_nodes():
        src = n.get("source") or {}
        if src.get("repo") != basename:
            continue
        path = src.get("path") or ""
        area_val = path.split("/", 1)[0] if "/" in path else path
        if kind and n.get("kind") != kind:
            continue
        if area and area_val != area:
            continue
        if tier and n.get("tier") != tier:
            continue
        if state and n.get("dossier_state") != state:
            continue
        out.append({
            "id": n["id"],
            "title": n.get("title") or n["id"].rsplit("::", 1)[-1],
            "kind": n.get("kind", "—"),
            "subkind": n.get("subkind"),
            "fan_out": n.get("fan_out", 0),
            "state": n.get("dossier_state", "current"),
            "tier": n.get("tier"),
            "area": area_val,
            "common": is_common_path(path),
            "href": f"/graph/node/{n['id']}",
            "src": f"{src.get('repo','')}/{src.get('path','')}" if src.get("path") else "",
        })
    if sort == "title":
        out.sort(key=lambda r: r["title"].lower())
    elif sort == "state":
        out.sort(key=lambda r: r["state"])
    else:  # fan_out (default)
        out.sort(key=lambda r: r["fan_out"], reverse=True)
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
    # Classified kinds (v1 + v2)
    "model": "models",
    "service": "services",
    "endpoint": "endpoints",
    "schema": "schemas",
    "component": "components",
    "hook": "hooks",
    "test": "tests",
    "util": "utils",
    # Logigraph kinds
    "rule": "rules",
    "domain": "domain",
    # v2 unclassified primitive-type dirs — primitives that didn't match any
    # classifier rule land here; displayed as "Unclassified primitives" in the
    # coverage matrix header, but each kind still appears as its own row.
    "module": "modules",
    "package": "packages",
    "class": "classes",
    "function": "functions",
    "variable": "variables",
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

# Telemetry paths are derived per-request from the active project; the legacy
# module-level constants were removed when graphui learned to serve multiple
# projects (see Project / current_project()).


def _logigraph_injections_path() -> Path:
    return current_project().logigraph_dir / "telemetry" / INJECTIONS_LOG_FILENAME


def _logigraph_acks_path() -> Path:
    return current_project().logigraph_dir / "telemetry" / ACKNOWLEDGMENTS_LOG_FILENAME


def _depgraph_injections_path() -> Path:
    return current_project().depgraph_dir / "telemetry" / INJECTIONS_LOG_FILENAME


def _depgraph_acks_path() -> Path:
    return current_project().depgraph_dir / "telemetry" / ACKNOWLEDGMENTS_LOG_FILENAME


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
        injections_path=_logigraph_injections_path(),
        acks_path=_logigraph_acks_path(),
        days=days,
    )


def telemetry_for_node(node_id: str, days: int = 7) -> dict[str, Any]:
    return _telemetry_for_id(
        target_id=node_id,
        id_field="node_id",
        injections_path=_depgraph_injections_path(),
        acks_path=_depgraph_acks_path(),
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
    proj = current_project()
    n = 0
    for kind_dir in (proj.depgraph_dir / "dossiers", proj.logigraph_dir / "dossiers"):
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
    rule_dir = current_project().logigraph_nodes_dir / "rules"
    return _count_node_files_since(rule_dir, since_ts)


def activity_summary() -> dict:
    """Today / 7-day sparkline / 30-day rollup for the dashboard activity strip."""
    proj = current_project()
    today_start = _start_of_day_utc(0)
    today = {
        "nodes_added": _count_node_files_since(proj.depgraph_nodes_dir, today_start),
        "drafts_authored": _drafts_authored_since(today_start),
        "drift_events": _drift_events_since(today_start),
        "rules_authored": _rules_authored_since(today_start),
    }
    # 7-day sparkline: bucket telemetry injections per day. mtimes were a poor
    # proxy because every regen rewrites every node file with the same timestamp,
    # masking real user/agent activity. Injections are written when Claude actually
    # edits a tracked file, so they reflect work.
    spark: list[int] = [0] * 7  # oldest first
    today_date = dt.datetime.now(dt.timezone.utc).date()
    for src in (_depgraph_injections_path(), _logigraph_injections_path()):
        for row in _read_jsonl(src):
            ts_raw = row.get("ts")
            try:
                day = dt.datetime.fromisoformat(ts_raw.replace("Z", "+00:00")).date()
            except (TypeError, AttributeError, ValueError):
                continue
            delta = (today_date - day).days
            if 0 <= delta <= 6:
                spark[6 - delta] += 1
    thirty_start = _start_of_day_utc(30)
    thirty_day = {
        "nodes_added": _count_node_files_since(proj.depgraph_nodes_dir, thirty_start),
        "drafts_reviewed": _count_jsonl_since(
            _logigraph_acks_path(), thirty_start
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

    for src in (_depgraph_injections_path(), _logigraph_injections_path()):
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

    for src in (_depgraph_acks_path(), _logigraph_acks_path()):
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
    rules_dir = current_project().logigraph_nodes_dir / "rules"
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
    """Read the most-recent calibration run dir under the project's
    logigraph/calibration/runs/. Returns accuracy %, pass/fail counts,
    drifted rule ids, prev-run delta."""
    runs_dir = current_project().logigraph_dir / "calibration" / "runs"
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


def _repo_path(key: str) -> Path | None:
    """Resolve a tracked-repo identifier to its filesystem path.

    The argument is whatever the extractor wrote to `source.repo` — in v2
    that's the `[repos.<key>]` key (e.g. "api"), NOT the path basename. We
    look the key up in depgraph/project.toml and expand `~` so paths like
    `path = "~/<project>-api"` resolve correctly (#25).

    Fall back to HOME/<arg> for legacy data that recorded a path basename
    and for the rare case where the key matches the on-disk dir name.
    """
    proj = current_project()
    try:
        repos = _depgraph_project_repos(proj.depgraph_dir)
    except Exception:
        repos = {}
    info = repos.get(key)
    if info is not None:
        configured = Path(info["path"]).expanduser()
        if (configured / ".git").exists():
            return configured
        # `path` is set but the checkout is missing — still return it so
        # callers can distinguish "not configured" from "configured but
        # absent." The git helpers no-op on a non-git dir.
        if configured.exists():
            return configured
    # Legacy fallback: basename under $HOME.
    p = HOME / key
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


def _classify(last_push_age: int | None) -> str:
    """Coarse activity classification by age only. dead-candidate is intentionally
    not produced here — that gate requires BOTH age and the inbound-deps signal,
    which is only available at repo_summary level. repo_summary upgrades
    dormant → dead-candidate when the second condition holds."""
    if last_push_age is None:
        return "unknown"
    if last_push_age <= 7:
        return "active"
    return "dormant"


def _today_node_delta_for_repo(basename: str) -> int:
    today_start = _start_of_day_utc(0)
    n = 0
    for p in current_project().depgraph_nodes_dir.rglob("*.json"):
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
    # Coarse classification by age only. repo_summary refines dormant →
    # dead-candidate by AND-ing in the inbound-deps signal it has access to.
    classification = _classify(age)
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


def _repo_external_pkgs(basename: str) -> int:
    """Count packages declared in the repo's `package.json` deps + dev-deps,
    `requirements.txt` lines, and `pyproject.toml` `[project].dependencies`.
    Touches the source repo's own files, so it's the only per-repo I/O that
    `_repo_aggregates` can't fold into a single pass over node data."""
    repo = _repo_path(basename)
    if repo is None:
        return 0
    ext = 0
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
    return ext


def _repo_aggregates() -> dict[str, dict]:
    """Per-repo aggregates computed in one pass over depgraph nodes + the
    dependents index + logigraph nodes. Cached per regen.

    Replaces the prior pattern where `repo_summary` called `repo_areas`,
    `repo_dep_counts`, and `repo_cross_cuts` once per repo — each of which
    walked the full node corpus on its own. That was O(N × R); this is O(N).

    Returns: {basename: {areas, dep_counts_nodes, cross_cuts}} where
      - areas: list[{dir, node_count}] sorted by node_count desc
      - dep_counts_nodes: {inbound_repos, outbound_repos} (no external_pkgs;
        that depends on the source repo's own files, not graph data)
      - cross_cuts: {rules, processes, domain} — sorted id lists
    """
    proj = current_project()
    key = (_depgraph_meta_mtime(), _logigraph_meta_mtime())
    cached = _REPO_AGGREGATES_CACHE.get(proj.graph_dir)
    if cached is not None and cached[0] == key:
        return cached[1]

    nodes = load_depgraph_nodes()
    dependents = load_dependents()
    lg = load_logigraph_nodes()

    # Endpoint nodes have ids like `GET::/api/foo` (method-prefixed); the
    # leading id segment is the verb, not the repo. Only `source.repo` is
    # authoritative.
    repo_by_id: dict[str, str] = {}
    area_counts: dict[str, dict[str, int]] = {}
    seen_repos: set[str] = set()
    for n in nodes:
        nid = n.get("id")
        src = n.get("source") or {}
        basename = src.get("repo")
        if not basename:
            continue
        seen_repos.add(basename)
        if nid:
            repo_by_id[nid] = basename
        path = src.get("path") or ""
        head = path.split("/", 1)[0] if "/" in path else path
        if head:
            buckets = area_counts.setdefault(basename, {})
            buckets[head] = buckets.get(head, 0) + 1

    inbound: dict[str, set[str]] = {b: set() for b in seen_repos}
    outbound: dict[str, set[str]] = {b: set() for b in seen_repos}
    # Edge totals — fan-in and fan-out summed across every node in the repo,
    # including same-repo edges. For a single-repo project the cross-repo
    # set above is always empty; without these totals the card shows "0
    # inbound" even when there's a full edge index (#24).
    inbound_edges: dict[str, int] = {b: 0 for b in seen_repos}
    outbound_edges: dict[str, int] = {b: 0 for b in seen_repos}
    for target_id, dependers in dependents.items():
        target_repo = repo_by_id.get(target_id)
        if not target_repo:
            continue
        inbound_edges[target_repo] = inbound_edges.get(target_repo, 0) + len(dependers)
        for d in dependers:
            dep_repo = repo_by_id.get(d.get("source") or "")
            if not dep_repo:
                continue
            outbound_edges[dep_repo] = outbound_edges.get(dep_repo, 0) + 1
            if dep_repo == target_repo:
                continue
            inbound[target_repo].add(dep_repo)
            outbound.setdefault(dep_repo, set()).add(target_repo)

    cross: dict[str, dict[str, set[str]]] = {
        b: {"rules": set(), "processes": set(), "domain": set()}
        for b in seen_repos
    }
    for r in lg["rules"]:
        touched: set[str] = set()
        for c in r.get("claims_code", []) or []:
            did = c.get("depgraph_id") or ""
            head = did.split("::", 1)[0]
            if head:
                touched.add(head)
        for basename in touched:
            slot = cross.setdefault(basename, {"rules": set(), "processes": set(), "domain": set()})
            slot["rules"].add(r["id"])
            for ref in (r.get("references_domain") or []):
                slot["domain"].add(ref)
    for p in lg["processes"]:
        touched_per_step: list[tuple[set[str], list[str]]] = []
        for step in p.get("steps", []) or []:
            touched: set[str] = set()
            for c in step.get("claims_code", []) or []:
                did = c.get("depgraph_id") or ""
                head = did.split("::", 1)[0]
                if head:
                    touched.add(head)
            if touched:
                touched_per_step.append((touched, step.get("references_domain") or []))
        for touched, refs in touched_per_step:
            for basename in touched:
                slot = cross.setdefault(basename, {"rules": set(), "processes": set(), "domain": set()})
                slot["processes"].add(p["id"])
                for ref in refs:
                    slot["domain"].add(ref)

    out: dict[str, dict] = {}
    for basename in seen_repos | set(cross.keys()):
        areas = area_counts.get(basename, {})
        out[basename] = {
            "areas": [
                {"dir": d, "node_count": c}
                for d, c in sorted(areas.items(), key=lambda kv: kv[1], reverse=True)
            ],
            "dep_counts_nodes": {
                "inbound_repos": len(inbound.get(basename, set())),
                "outbound_repos": len(outbound.get(basename, set())),
                "inbound_edges": inbound_edges.get(basename, 0),
                "outbound_edges": outbound_edges.get(basename, 0),
            },
            "cross_cuts": {
                "rules": sorted(cross[basename]["rules"]) if basename in cross else [],
                "processes": sorted(cross[basename]["processes"]) if basename in cross else [],
                "domain": sorted(cross[basename]["domain"]) if basename in cross else [],
            },
        }

    _REPO_AGGREGATES_CACHE[proj.graph_dir] = (key, out)
    return out


def repo_areas(basename: str) -> list[dict]:
    """Return top-level directories in `basename` that contain at least one
    tracked node, ordered by node_count desc. Each entry: {dir, node_count}."""
    return _repo_aggregates().get(basename, {}).get("areas", [])


def repo_dep_counts(basename: str) -> dict:
    """Compute three counts:
      - inbound_repos: # of other tracked repos with nodes whose dependents
        index points into a node belonging to `basename`.
      - outbound_repos: # of other tracked repos whose nodes are referenced
        by nodes in `basename` (via the by_target dependents index — symmetric).
      - external_pkgs: # of packages declared in `basename/package.json` deps
        + `basename/requirements.txt` lines + `basename/pyproject.toml` deps.
    """
    agg = _repo_aggregates().get(basename, {}).get("dep_counts_nodes") or {
        "inbound_repos": 0, "outbound_repos": 0,
        "inbound_edges": 0, "outbound_edges": 0,
    }
    return {**agg, "external_pkgs": _repo_external_pkgs(basename)}


def repo_cross_cuts(basename: str) -> dict:
    """List the rule/process/domain ids that touch any node in `basename`.
    Returns id-lists (not counts) so the repo card can name a few inline."""
    return _repo_aggregates().get(basename, {}).get("cross_cuts") or {
        "rules": [], "processes": [], "domain": [],
    }


def _titles_and_repos_by_id() -> tuple[dict[str, str], dict[str, str]]:
    """One-pass lookup of {id -> title} and {id -> source.repo}. Endpoint
    node ids are method-prefixed (`GET::/api/...`), so the repo can only
    be resolved by reading the node's `source.repo` field — not by
    splitting the id on `::`."""
    titles: dict[str, str] = {}
    repos: dict[str, str] = {}
    for n in load_depgraph_nodes():
        nid = n.get("id")
        if not nid:
            continue
        titles[nid] = n.get("title") or nid.rsplit("::", 1)[-1]
        r = (n.get("source") or {}).get("repo")
        if r:
            repos[nid] = r
    return titles, repos


def repo_inbound_deps_detail(basename: str) -> list[dict]:
    """Rows of {from_repo, from_id, from_title, to_id, to_title} — one per
    cross-repo dependent edge pointing INTO a node in `basename`."""
    out: list[dict] = []
    titles, repos = _titles_and_repos_by_id()
    for target_id, dependers in load_dependents().items():
        target_repo = repos.get(target_id)
        if target_repo != basename:
            continue
        for d in dependers:
            dep_id = d.get("source") or ""
            dep_repo = repos.get(dep_id)
            if not dep_repo or dep_repo == basename:
                continue
            out.append({
                "from_repo": dep_repo,
                "from_id": dep_id,
                "from_title": titles.get(dep_id, dep_id.rsplit("::", 1)[-1]),
                "to_id": target_id,
                "to_title": titles.get(target_id, target_id.rsplit("::", 1)[-1]),
            })
    out.sort(key=lambda r: (r["from_repo"], r["from_id"]))
    return out


def repo_outbound_deps_detail(basename: str) -> list[dict]:
    """Rows of {to_repo, from_id, from_title, to_id, to_title} — one per
    cross-repo dependent edge pointing OUT of a node in `basename`."""
    out: list[dict] = []
    titles, repos = _titles_and_repos_by_id()
    for target_id, dependers in load_dependents().items():
        target_repo = repos.get(target_id)
        if not target_repo or target_repo == basename:
            continue
        for d in dependers:
            dep_id = d.get("source") or ""
            dep_repo = repos.get(dep_id)
            if dep_repo != basename:
                continue
            out.append({
                "to_repo": target_repo,
                "from_id": dep_id,
                "from_title": titles.get(dep_id, dep_id.rsplit("::", 1)[-1]),
                "to_id": target_id,
                "to_title": titles.get(target_id, target_id.rsplit("::", 1)[-1]),
            })
    out.sort(key=lambda r: (r["to_repo"], r["to_id"]))
    return out


def repo_external_pkgs(basename: str) -> list[dict]:
    """List external packages declared by `basename`. Each row:
    {name, source} where source is 'npm' or 'python'. Sorted by name."""
    repo = _repo_path(basename)
    if repo is None:
        return []
    out: list[dict] = []
    pkg = repo / "package.json"
    if pkg.exists():
        try:
            row = json.loads(pkg.read_text())
            for name in (row.get("dependencies") or {}):
                out.append({"name": name, "source": "npm"})
            for name in (row.get("devDependencies") or {}):
                out.append({"name": name, "source": "npm"})
        except (OSError, json.JSONDecodeError):
            pass
    reqs = repo / "requirements.txt"
    if reqs.exists():
        for line in reqs.read_text(errors="ignore").splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            # strip pin syntax: package>=1.0,<2 → package
            name = s.split("=", 1)[0].split("<", 1)[0].split(">", 1)[0].split("[", 1)[0].strip()
            if name:
                out.append({"name": name, "source": "python"})
    pyproj = repo / "pyproject.toml"
    if pyproj.exists():
        txt = pyproj.read_text(errors="ignore")
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
                    name = s.strip("\"',").split("=", 1)[0].split("<", 1)[0].split(">", 1)[0].split("[", 1)[0].strip()
                    if name:
                        out.append({"name": name, "source": "python"})
    out.sort(key=lambda r: r["name"].lower())
    return out


def repo_dead_code(basename: str) -> list[dict]:
    """Nodes belonging to `basename` with zero inbound dep references.
    Sorted by fan_out asc (least-connected first)."""
    dependents = load_dependents()
    incoming_count: dict[str, int] = {tid: len(d) for tid, d in dependents.items()}
    out: list[dict] = []
    for n in load_depgraph_nodes():
        src = n.get("source") or {}
        if src.get("repo") != basename:
            continue
        nid = n["id"]
        if incoming_count.get(nid, 0) > 0:
            continue
        path = src.get("path") or ""
        area = path.split("/", 1)[0] if "/" in path else path
        out.append({
            "id": nid,
            "title": n.get("title") or nid.rsplit("::", 1)[-1],
            "kind": n.get("kind", "—"),
            "area": area,
            "fan_out": n.get("fan_out", 0),
            "state": n["dossier_state"],
            "href": f"/graph/node/{nid}",
        })
    out.sort(key=lambda r: (r["fan_out"], r["area"], r["title"].lower()))
    return out


def read_project_toml() -> dict:
    """Parse the depgraph project.toml. Returns the raw dict; callers
    interpret `repos.*`, `[project]`, etc."""
    path = current_project().depgraph_dir / "project.toml"
    if not path.exists():
        return {}
    try:
        return tomllib.loads(path.read_text())
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def tracked_repos_settings() -> list[dict]:
    """One row per [repos.*] in project.toml. Each row carries enough
    detail for the Settings page: key, basename, resolved filesystem path,
    git remote URL, extractor command, extractor file (resolved abs), and
    files_arg if any."""
    proj = current_project()
    cfg = read_project_toml()
    repos = cfg.get("repos") or {}
    out: list[dict] = []
    for key, info in repos.items():
        raw_path = info.get("path") or ""
        path = Path(raw_path).expanduser() if raw_path else None
        extractor_cmd = list(info.get("extractor") or [])
        # Resolve {data_dir} in the extractor command to locate the file.
        extractor_file = None
        for part in extractor_cmd:
            if isinstance(part, str) and "{data_dir}" in part:
                resolved = part.replace("{data_dir}", str(proj.depgraph_dir))
                if Path(resolved).exists():
                    extractor_file = resolved
                    break
        git_remote = git_remote_url(path) if path and (path / ".git").exists() else None
        out.append({
            "key": key,
            "basename": path.name if path else "—",
            "path": str(path) if path else "—",
            "path_exists": bool(path and path.exists()),
            "git_remote": git_remote,
            "extractor_cmd": extractor_cmd,
            "extractor_file": extractor_file,
            "files_arg": info.get("files_arg"),
        })
    return out


_EXTRACTOR_VERSION_RE = re.compile(r"""__extractor_version__\s*=\s*["']([^"']+)["']""")


def _scan_extractor_file(path: Path, scope: str) -> dict:
    """Build the per-file row for the inventory."""
    raw = path.read_bytes() if path.exists() else b""
    text = ""
    try:
        text = raw.decode("utf-8", errors="ignore")
    except UnicodeDecodeError:
        pass
    m = _EXTRACTOR_VERSION_RE.search(text)
    return {
        "filename": path.name,
        "path": str(path),
        "size_bytes": len(raw),
        "mtime_iso": dt.datetime.fromtimestamp(
            path.stat().st_mtime, dt.timezone.utc
        ).isoformat(timespec="seconds") if path.exists() else None,
        "sha256_prefix": hashlib.sha256(raw).hexdigest()[:12],
        "scope": scope,
        "declared_version": m.group(1) if m else None,
    }


def extractor_inventory() -> list[dict]:
    """Walk the project-custom extractor dir AND the framework's per-language
    extractor dirs. Returns one row per file with size, mtime, sha256 prefix,
    and scope (`project` or `framework`)."""
    out: list[dict] = []
    project_dir = current_project().depgraph_dir / "extractors"
    if project_dir.exists():
        for p in sorted(project_dir.iterdir()):
            if p.is_file() and not p.name.startswith("."):
                out.append(_scan_extractor_file(p, "project"))
    # Framework-shipped per-language extractors (Python in-process, TypeScript
    # via tsx subprocess, SQL pipeline).
    framework_extractors = _DEPGRAPH_TOOL_ROOT / "extractors"
    for subdir in ("python", "typescript", "sql"):
        d = framework_extractors / subdir
        if not d.exists():
            continue
        for p in sorted(d.rglob("*.py")):
            if "/node_modules/" in str(p) or "/__pycache__/" in str(p):
                continue
            out.append(_scan_extractor_file(p, "framework"))
        for p in sorted(d.rglob("*.ts")):
            if "/node_modules/" in str(p):
                continue
            out.append(_scan_extractor_file(p, "framework"))
    return out


_LOGIGRAPH_TOOL_ROOT = _GRAPHUI_TOOL_ROOT.parent / "logigraph"


def _framework_git_sha(repo_root: Path) -> str | None:
    """Short SHA of HEAD in the given framework tool repo. None if not a git
    checkout (e.g. installed via package manager, vendored, etc.)."""
    if not (repo_root / ".git").exists():
        return None
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short=12", "HEAD"],
            cwd=str(repo_root), capture_output=True, text=True, timeout=5,
        )
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def framework_settings() -> dict:
    """Surface the depgraph + logigraph framework + data-dir state for the
    Settings page. Pulls from the active project's paths, env-resolved CLI
    bins (overridable via DEPGRAPH_BIN/LOGIGRAPH_BIN), git HEAD of the tool
    repos, and the corpus _meta.json files."""
    proj = current_project()
    meta = load_meta()
    depgraph_cli = os.environ.get("DEPGRAPH_BIN") or str(
        _DEPGRAPH_TOOL_ROOT / "bin" / "depgraph"
    )
    logigraph_cli = os.environ.get("LOGIGRAPH_BIN") or str(
        _LOGIGRAPH_TOOL_ROOT / "bin" / "logigraph"
    )
    return {
        "depgraph": {
            "tool_root": str(_DEPGRAPH_TOOL_ROOT),
            "tool_exists": _DEPGRAPH_TOOL_ROOT.exists(),
            "cli_bin": depgraph_cli,
            "data_dir": str(proj.depgraph_dir),
            "framework_git_sha": _framework_git_sha(_DEPGRAPH_TOOL_ROOT),
            "corpus_commit": (meta.get("depgraph") or {}).get("git_commit"),
            "regen_at": (meta.get("depgraph") or {}).get("regen_at"),
            "regen_status": (meta.get("depgraph") or {}).get("regen_status"),
            "node_count": (meta.get("depgraph") or {}).get("node_count"),
        },
        "logigraph": {
            "tool_root": str(_LOGIGRAPH_TOOL_ROOT),
            "tool_exists": _LOGIGRAPH_TOOL_ROOT.exists(),
            "cli_bin": logigraph_cli,
            "data_dir": str(proj.logigraph_dir),
            "framework_git_sha": _framework_git_sha(_LOGIGRAPH_TOOL_ROOT),
            "corpus_commit": (meta.get("logigraph") or {}).get("git_commit"),
            "regen_at": (meta.get("logigraph") or {}).get("regen_at"),
            "regen_status": (meta.get("logigraph") or {}).get("regen_status"),
            "node_count": (meta.get("logigraph") or {}).get("node_count"),
        },
    }


def repo_inbound_deps_rollup(basename: str) -> list[dict]:
    """Cross-repo inbound edges rolled up by source repo. Each row:
    {from_repo, edge_count}. Sorted by edge_count desc. Human-grade summary
    of the per-edge view in repo_inbound_deps_detail."""
    _, repos = _titles_and_repos_by_id()
    counts: dict[str, int] = {}
    for target_id, dependers in load_dependents().items():
        if repos.get(target_id) != basename:
            continue
        for d in dependers:
            dep_repo = repos.get(d.get("source") or "")
            if not dep_repo or dep_repo == basename:
                continue
            counts[dep_repo] = counts.get(dep_repo, 0) + 1
    return [
        {"from_repo": r, "edge_count": c}
        for r, c in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    ]


def repo_outbound_deps_rollup(basename: str) -> list[dict]:
    """Cross-repo outbound edges rolled up by target repo. Each row:
    {to_repo, edge_count}. Symmetric to repo_inbound_deps_rollup."""
    _, repos = _titles_and_repos_by_id()
    counts: dict[str, int] = {}
    for target_id, dependers in load_dependents().items():
        target_repo = repos.get(target_id)
        if not target_repo or target_repo == basename:
            continue
        for d in dependers:
            if repos.get(d.get("source") or "") == basename:
                counts[target_repo] = counts.get(target_repo, 0) + 1
    return [
        {"to_repo": r, "edge_count": c}
        for r, c in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    ]
