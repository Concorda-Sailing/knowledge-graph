"""FastAPI app for the depgraph + logigraph viewer.

Mount-prefix is `/graph` so it can sit behind the dev box Caddy at
`https://dev.members.massbaysailing.org/graph/`.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import datetime
import json
import os
import subprocess

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import loader
from . import markdown_render
from . import search as search_module

# Where the framework CLIs live. Env vars let us point at the tool
# repos without coupling graphui to a specific layout. Defaults match
# the current ~/tools/ install.
DEPGRAPH_BIN = Path(
    os.environ.get("DEPGRAPH_BIN")
    or (Path.home() / "tools" / "knowledge-graph" / "depgraph" / "bin" / "depgraph")
)
LOGIGRAPH_BIN = Path(
    os.environ.get("LOGIGRAPH_BIN")
    or (Path.home() / "tools" / "knowledge-graph" / "logigraph" / "bin" / "logigraph")
)


# Node-id prefixes used to route bump requests to the right CLI.
_LOGIGRAPH_RULE_PREFIX = "rule::"
_LOGIGRAPH_PROCESS_PREFIX = "process::"
_LOGIGRAPH_DOMAIN_PREFIXES = (
    "role::", "resource::", "attribute::", "relationship::", "action::",
)

APP_ROOT = Path(__file__).parent
TEMPLATES = Jinja2Templates(directory=str(APP_ROOT / "templates"))


def _review_pending_count() -> int:
    """Lazy helper for templates — counts current llm_drafted dossiers.
    Exposed as a Jinja global so the top-nav badge works on every page
    without each route having to thread the count through context."""
    return len(_review_queue())


TEMPLATES.env.globals["review_pending_count"] = _review_pending_count


def _issues_fresh_count() -> int:
    """Lazy helper for the Issues nav badge — counts fresh (untracked) flags."""
    return loader.corpus_flags().get("count_fresh", 0)


TEMPLATES.env.globals["issues_fresh_count"] = _issues_fresh_count
STATIC = APP_ROOT / "static"

app = FastAPI(title="graphui", openapi_url=None, docs_url=None)
app.mount("/graph/static", StaticFiles(directory=str(STATIC)), name="static")


# ----- Helpers ----------------------------------------------------------------

STATE_ORDER = ["current", "llm_drafted", "unreviewed", "stale", "missing"]
TIER_ORDER = ["A", "B", "C", "*"]
KIND_ORDER = [
    "model", "service", "endpoint", "schema",
    "component", "hook", "test", "rule", "process", "domain",
]


def _kind_sort(k: str) -> int:
    return KIND_ORDER.index(k) if k in KIND_ORDER else 99


# ----- Routes -----------------------------------------------------------------

@app.get("/graph/", response_class=HTMLResponse)
@app.get("/graph", response_class=HTMLResponse)
def index(request: Request, sort: str = "activity", activity: str | None = None) -> HTMLResponse:
    """Top-level dashboard: activity strip, graph health, cross-cuts, then repos
    filtered by activity classification and sorted per `sort` param."""
    repos_all = loader.repo_summary()
    counts = {"active": 0, "dormant": 0, "dead-candidate": 0, "all": len(repos_all)}
    for r in repos_all:
        cls = r["activity"]["classification"]
        if cls in counts:
            counts[cls] += 1

    if activity and activity != "all":
        repos = [r for r in repos_all if r["activity"]["classification"] == activity]
    else:
        repos = repos_all

    if sort == "alpha":
        repos = sorted(repos, key=lambda r: r["basename"])
    elif sort == "inbound":
        repos = sorted(repos, key=lambda r: r["dep_counts"]["inbound_repos"], reverse=True)
    elif sort == "dead":
        repos = sorted(repos, key=lambda r: r["dead_code_score"], reverse=True)
    else:  # activity (default)
        repos = sorted(repos, key=lambda r: r["activity"]["commits_7d"], reverse=True)

    today_date = datetime.datetime.now().strftime("%a %b %d")

    return TEMPLATES.TemplateResponse(
        request,
        "index.html",
        {
            "repos": repos,
            "filter_counts": counts,
            "sort": sort,
            "activity_filter": activity,
            "today_date": today_date,
            "activity": loader.activity_summary(),
            "health": loader.graph_health(),
            "cross": loader.cross_cutting_summary(),
            "review_pending": len(_review_queue()),
            "flags": loader.corpus_flags(),
            "meta": loader.load_meta(),
        },
    )


@app.get("/graph/activity", response_class=HTMLResponse)
def activity_page(request: Request) -> HTMLResponse:
    """Activity rollup. Full event chronology (per-commit, per-fire, per-draft)
    is deferred to a follow-up plan; for now this surfaces the same today/30-day
    numbers the dashboard strip uses so the link is not a dead end."""
    return TEMPLATES.TemplateResponse(
        request,
        "activity.html",
        {
            "activity": loader.activity_summary(),
            "meta": loader.load_meta(),
        },
    )


@app.get("/graph/search", response_class=HTMLResponse)
def search_page(
    request: Request,
    q: str = "",
    mode: str = "semantic",
    scope: list[str] | None = Query(default=None),
    limit: int = 30,
) -> HTMLResponse:
    """Hybrid search results. `mode` is the primary tab (semantic/dep/
    knowledge); `scope` may be repeated to narrow further within the mode."""
    if mode not in ("semantic", "dep", "knowledge"):
        mode = "semantic"
    scope_list = scope if scope else None
    hits = (search_module.search(q, scopes=scope_list, mode=mode, limit=limit)
            if q else [])
    # Granular chips visible under the active tab depend on mode.
    chips_by_mode = {
        "semantic": ["rules", "domain", "processes", "dossiers"],
        "dep": ["dossiers"],
        "knowledge": ["rules", "domain", "processes"],
    }
    return TEMPLATES.TemplateResponse(
        request,
        "search.html",
        {
            "q": q,
            "mode": mode,
            "all_modes": ["semantic", "dep", "knowledge"],
            "scopes_selected": set(scope_list or []),
            "scope_chips": chips_by_mode.get(mode, chips_by_mode["semantic"]),
            "hits": hits,
            "limit": limit,
            "meta": loader.load_meta(),
        },
    )


@app.get("/graph/settings", response_class=HTMLResponse)
def settings_page(request: Request) -> HTMLResponse:
    """Read-only view of project.toml, tracked repos with git remotes, and the
    extractor file inventory. v1 is informational only — no editing."""
    return TEMPLATES.TemplateResponse(
        request,
        "settings.html",
        {
            "framework": loader.framework_settings(),
            "project": loader.read_project_toml(),
            "repos": loader.tracked_repos_settings(),
            "extractors": loader.extractor_inventory(),
            "project_toml_path": str(loader.DEPGRAPH / "project.toml"),
            "meta": loader.load_meta(),
        },
    )


@app.get("/graph/telemetry", response_class=HTMLResponse)
def telemetry_page(request: Request) -> HTMLResponse:
    """Telemetry rollup. Full per-rule + per-dossier injection breakdown is
    deferred to a follow-up plan; this surfaces the same numbers the dashboard
    health tile uses so the 'see all telemetry →' link is not a dead end."""
    return TEMPLATES.TemplateResponse(
        request,
        "telemetry.html",
        {
            "health": loader.graph_health(),
            "meta": loader.load_meta(),
        },
    )


@app.get("/graph/issues", response_class=HTMLResponse)
def issues_page(request: Request) -> HTMLResponse:
    """Full-page view of corpus flags — what the Needs-attention banner
    summarizes on the dashboard. Same kind-grouping + Track action."""
    return TEMPLATES.TemplateResponse(
        request,
        "issues.html",
        {
            "flags": loader.corpus_flags(),
            "flagged_nodes": loader.flagged_nodes(),
            "meta": loader.load_meta(),
        },
    )


@app.get("/graph/knowledge", response_class=HTMLResponse)
def knowledge_page(
    request: Request,
    sort: str = "id",
    kind: str | None = None,
    state: str | None = None,
    subkind: str | None = None,
) -> HTMLResponse:
    """Unified knowledge list: rules + domain + processes. Filter by kind,
    state, subkind; sort by id / title / fan_out / state. Each row carries
    a checkbox for bulk selection (currently bulk-promote drafts)."""
    return TEMPLATES.TemplateResponse(
        request,
        "knowledge.html",
        {
            "items": loader.all_knowledge_nodes(sort=sort, kind_filter=kind, state_filter=state, subkind_filter=subkind),
            "filters": loader.knowledge_filters(),
            "sort": sort,
            "kind_filter": kind,
            "state_filter": state,
            "subkind_filter": subkind,
            "meta": loader.load_meta(),
        },
    )


DOMAIN_PAGE_SIZE_DEFAULT = 100
DOMAIN_PAGE_SIZE_MAX = 500


@app.get("/graph/repo/{basename}", response_class=HTMLResponse)
def repo_detail(
    request: Request,
    basename: str,
    tab: str = "nodes",
    kind: str | None = None,
    area: str | None = None,
    tier: str | None = None,
    state: str | None = None,
    page: int = 1,
    per_page: int = DOMAIN_PAGE_SIZE_DEFAULT,
) -> HTMLResponse:
    """One source repo with header + left rail + tabbed main pane.

    The domain-nodes table on the nodes tab is server-paginated via `page`
    and `per_page`. The common-nodes group is lazy-loaded (see the
    `/graph/repo/{basename}/common` fragment route) so large repos don't
    ship thousands of hidden rows on first paint.
    """
    repo = next(
        (r for r in loader.repo_summary() if r["basename"] == basename),
        None,
    )
    if repo is None:
        raise HTTPException(404, f"repo not found in any tracked node: {basename}")

    nodes = loader.nodes_for_repo(basename, kind=kind, area=area, tier=tier, state=state)
    domain_nodes_all = [n for n in nodes if not n.get("common")]
    common_nodes_all = [n for n in nodes if n.get("common")]

    per_page = max(1, min(per_page, DOMAIN_PAGE_SIZE_MAX))
    domain_total = len(domain_nodes_all)
    domain_pages = max(1, (domain_total + per_page - 1) // per_page)
    page = max(1, min(page, domain_pages))
    start = (page - 1) * per_page
    domain_nodes_page = domain_nodes_all[start:start + per_page]

    domain_pagination = {
        "page": page,
        "per_page": per_page,
        "total": domain_total,
        "pages": domain_pages,
        "start": start + 1 if domain_total else 0,
        "end": start + len(domain_nodes_page),
        "has_prev": page > 1,
        "has_next": page < domain_pages,
        "prev_page": page - 1,
        "next_page": page + 1,
    }

    dead_code = loader.repo_dead_code(basename)
    inbound_rollup = loader.repo_inbound_deps_rollup(basename)
    outbound_rollup = loader.repo_outbound_deps_rollup(basename)
    external = loader.repo_external_pkgs(basename)
    inbound_edge_total = sum(r["edge_count"] for r in inbound_rollup)
    outbound_edge_total = sum(r["edge_count"] for r in outbound_rollup)

    # Tier breakdown for the left rail (across all nodes in this repo, no filters).
    tier_counts: dict[str, int] = {}
    for n in loader.nodes_for_repo(basename):
        t = n.get("tier")
        if t:
            tier_counts[t] = tier_counts.get(t, 0) + 1

    tab_counts = {
        "nodes": repo["node_count"],
        "dead": len(dead_code),
        "deps": inbound_edge_total + outbound_edge_total + len(external),
    }

    if tab not in ("nodes", "dead", "deps", "telemetry", "activity"):
        tab = "nodes"

    return TEMPLATES.TemplateResponse(
        request,
        "repo.html",
        {
            "repo": repo,
            "active_tab": tab,
            "nodes": nodes,
            "domain_nodes": domain_nodes_page,
            "domain_pagination": domain_pagination,
            "common_count": len(common_nodes_all),
            "dead_code": dead_code,
            "inbound_rollup": inbound_rollup,
            "outbound_rollup": outbound_rollup,
            "inbound_edge_total": inbound_edge_total,
            "outbound_edge_total": outbound_edge_total,
            "external_pkgs": external,
            "tab_counts": tab_counts,
            "tier_counts": tier_counts,
            "kind_filter": kind,
            "area_filter": area,
            "tier_filter": tier,
            "state_filter": state,
            "meta": loader.load_meta(),
        },
    )


@app.get("/graph/repo/{basename}/common", response_class=HTMLResponse)
def repo_common_fragment(
    request: Request,
    basename: str,
    kind: str | None = None,
    area: str | None = None,
    tier: str | None = None,
    state: str | None = None,
) -> HTMLResponse:
    """HTML fragment: the common-nodes table rows for a repo, fetched on
    demand when the user expands the Common <details> on the nodes tab.

    Filters mirror the parent /graph/repo/{basename} route so the lazy
    fetch respects whatever chips are active."""
    repo = next(
        (r for r in loader.repo_summary() if r["basename"] == basename),
        None,
    )
    if repo is None:
        raise HTTPException(404, f"repo not found in any tracked node: {basename}")
    nodes = loader.nodes_for_repo(basename, kind=kind, area=area, tier=tier, state=state)
    common_nodes = [n for n in nodes if n.get("common")]
    return TEMPLATES.TemplateResponse(
        request,
        "_node_list.html",
        {
            "nodes": common_nodes,
            "columns": ["title", "area", "kind", "tier", "fan_in", "state"],
            "empty_message": "No common-infrastructure nodes match the current filters.",
        },
    )


@app.get("/graph/kind/{kind_name}", response_class=HTMLResponse)
def kind_detail(
    request: Request,
    kind_name: str,
    subkind: str | None = None,
    state: str | None = None,
) -> HTMLResponse:
    """One logigraph kind (rules | domain | processes). Cards."""
    if kind_name not in ("rules", "domain", "processes"):
        raise HTTPException(404, f"unknown logigraph kind: {kind_name}")
    nodes = loader.nodes_for_kind(kind_name, subkind=subkind, state=state)
    summary_entry = next(
        (k for k in loader.kind_summary() if k["kind"] == kind_name),
        None,
    )
    # Available subkinds for the filter row (domain only).
    subkinds: list[str] = []
    if kind_name == "domain":
        subkinds = sorted({n.get("subkind") for n in loader.load_logigraph_nodes()["domain"] if n.get("subkind")})
    return TEMPLATES.TemplateResponse(
        request,
        "kind.html",
        {
            "kind_name": kind_name,
            "summary": summary_entry,
            "nodes": nodes,
            "subkind_filter": subkind,
            "state_filter": state,
            "subkinds": subkinds,
            "meta": loader.load_meta(),
        },
    )


@app.get("/graph/api/nodes.json")
def nodes_json() -> JSONResponse:
    """Flat node list for client-side filter/sort on the index page.
    Includes both depgraph nodes and logigraph rules+domain, distinguished
    by `kind`."""
    out = []
    for n in loader.load_depgraph_nodes():
        src = n.get("source") or {}
        out.append({
            "id": n["id"],
            "kind": n.get("kind", "—"),
            "title": n.get("title") or n["id"].rsplit("::", 1)[-1],
            "tier": n["tier"],
            "fan_out": n["fan_out"],
            "state": n["dossier_state"],
            "src": f"{src.get('repo','')}/{src.get('path','')}" if src.get("path") else "",
            "href": f"/graph/node/{n['id']}",
        })
    lg = loader.load_logigraph_nodes()
    for r in lg["rules"]:
        out.append({
            "id": r["id"],
            "kind": "rule",
            "title": r.get("title", r["id"]),
            "tier": "*",
            "fan_out": r.get("fan_out", 0),
            "state": r["dossier_state"],
            "src": "",
            "href": f"/graph/rule/{r['id']}",
        })
    for o in lg["domain"]:
        out.append({
            "id": o["id"],
            "kind": "domain",
            "title": o.get("title", o["id"]),
            "tier": "*",
            "fan_out": 0,
            "state": o["dossier_state"],
            "src": "",
            "href": f"/graph/domain/{o['id']}",
        })
    for p in lg["processes"]:
        out.append({
            "id": p["id"],
            "kind": "process",
            "title": p.get("title", p["id"]),
            "tier": "*",
            "fan_out": p.get("fan_out", 0),
            "state": p["dossier_state"],
            "src": "",
            "href": f"/graph/process/{p['id']}",
        })
    return JSONResponse(out)


def _review_queue(tier: str | None = None, kind: str | None = None) -> list[dict]:
    """All llm_drafted nodes (depgraph + logigraph) ranked by fan_out desc,
    optionally filtered by tier (depgraph A/B/C; logigraph nodes have tier='*'
    and pass the filter only when `tier` is None).

    Drives the review queue + node detail prev/next navigation.
    """
    rows: list[dict] = []
    for n in loader.load_depgraph_nodes():
        if n.get("dossier_state") != "llm_drafted":
            continue
        if tier and n.get("tier") != tier:
            continue
        if kind and n.get("kind") != kind:
            continue
        rows.append({
            "id": n["id"],
            "kind": n.get("kind", "—"),
            "title": n.get("title") or n["id"].rsplit("::", 1)[-1],
            "tier": n["tier"],
            "fan_out": n["fan_out"],
            "href": f"/graph/node/{n['id']}",
        })
    lg = loader.load_logigraph_nodes()
    for r in lg["rules"]:
        if r.get("dossier_state") != "llm_drafted":
            continue
        if tier:  # logigraph nodes have no A/B/C tier; skip when caller asks for one
            continue
        if kind and kind != "rule":
            continue
        rows.append({
            "id": r["id"],
            "kind": "rule",
            "title": r.get("title", r["id"]),
            "tier": "*",
            "fan_out": r.get("fan_out", 0),
            "href": f"/graph/rule/{r['id']}",
        })
    for o in lg["domain"]:
        if o.get("dossier_state") != "llm_drafted":
            continue
        if tier:
            continue
        if kind and kind != "domain":
            continue
        rows.append({
            "id": o["id"],
            "kind": "domain",
            "title": o.get("title", o["id"]),
            "tier": "*",
            "fan_out": 0,
            "href": f"/graph/domain/{o['id']}",
        })
    for p in lg.get("processes", []):
        if p.get("dossier_state") != "llm_drafted":
            continue
        if tier:
            continue
        if kind and kind not in ("process", "processes"):
            continue
        rows.append({
            "id": p["id"],
            "kind": "process",
            "title": p.get("title", p["id"]),
            "tier": "*",
            "fan_out": p.get("fan_out", 0),
            "href": f"/graph/process/{p['id']}",
        })
    rows.sort(key=lambda r: (-r.get("fan_out", 0), r["id"]))
    return rows


def _queue_context(node_id: str, dossier_state: str, tier: str | None = None, kind: str | None = None) -> dict:
    """If `node_id` is an llm_drafted entry in the review queue, return the
    context vars the _review_strip partial expects: queue_position,
    queue_total, prev_node, next_node, queue_back_href, target_node_id,
    approve_next_href. Returns dict with None values when the node isn't
    in the queue (the partial then renders nothing)."""
    out = {
        "queue_position": None, "queue_total": None,
        "prev_node": None, "next_node": None,
        "queue_back_href": "/graph/review",
        "target_node_id": node_id,
        "approve_next_href": "/graph/review",
    }
    if dossier_state != "llm_drafted":
        return out
    queue = _review_queue(tier=tier, kind=kind)
    ids = [n["id"] for n in queue]
    if node_id not in ids:
        return out
    i = ids.index(node_id)
    out["queue_position"] = i + 1
    out["queue_total"] = len(ids)
    if i > 0:
        out["prev_node"] = queue[i - 1]
    if i < len(queue) - 1:
        out["next_node"] = queue[i + 1]
    if tier:
        out["queue_back_href"] = f"/graph/review?tier={tier}"
    out["approve_next_href"] = out["next_node"]["href"] if out["next_node"] else out["queue_back_href"]
    return out


@app.get("/graph/review", response_class=HTMLResponse)
def review_queue(request: Request, tier: str | None = None, kind: str | None = None) -> HTMLResponse:
    rows = _review_queue(tier=tier, kind=kind)
    return TEMPLATES.TemplateResponse(
        request,
        "review.html",
        {
            "rows": rows,
            "tier": tier,
            "kind": kind,
            "meta": loader.load_meta(),
        },
    )


@app.get("/graph/node/{node_id:path}", response_class=HTMLResponse)
def node_detail(request: Request, node_id: str) -> HTMLResponse:
    node = loader.load_node_by_id(node_id)
    if not node:
        raise HTTPException(404, f"node not found: {node_id}")
    deps = loader.dependents_of(node_id)
    rule_ids = loader.applicable_rules_for(node_id)
    rules = []
    for rid in rule_ids:
        r = loader.load_rule_by_id(rid)
        if r:
            rules.append(r)
    dossier_text = loader.read_dossier(node.get("dossier"), loader.DEPGRAPH)
    dossier_html = markdown_render.render(dossier_text) if dossier_text else None
    src = node.get("source") or {}
    commits_30d = loader.commits_30d(src.get("repo", ""), src.get("path", ""))
    history = loader.commit_history(
        loader.DEPGRAPH,
        [p for p in (node.get("_node_file"), node.get("dossier")) if p],
    )
    timeline = loader.parse_action_timeline(history)
    telemetry = loader.telemetry_for_node(node_id)
    siblings = loader.siblings_in_file(node_id)
    qctx = _queue_context(node_id, node.get("dossier_state"), tier=node.get("tier"), kind=node.get("kind"))
    flag = loader.flagged_state(node)
    auth = loader.authorship(dossier_text)
    return TEMPLATES.TemplateResponse(
        request,
        "node.html",
        {
            "node": node,
            "dependents": deps,
            "rules": rules,
            "dossier_html": dossier_html,
            "src": src,
            "commits_30d": commits_30d,
            "history": history,
            "timeline": timeline,
            "telemetry": telemetry,
            "siblings": siblings,
            "warnings": loader.warnings_for(node_id),
            "node_id": node_id,
            "flag": flag,
            "authorship": auth,
            **qctx,
        },
    )


@app.get("/graph/rule/{rule_id:path}", response_class=HTMLResponse)
def rule_detail(request: Request, rule_id: str) -> HTMLResponse:
    rule = loader.load_rule_by_id(rule_id)
    if not rule:
        raise HTTPException(404, f"rule not found: {rule_id}")
    dossier_text = loader.read_dossier(rule.get("dossier"), loader.LOGIGRAPH)
    dossier_html = markdown_render.render(dossier_text) if dossier_text else None
    telemetry = loader.telemetry_for_rule(rule_id)
    history = loader.commit_history(
        loader.LOGIGRAPH,
        [p for p in (rule.get("_node_file"), rule.get("dossier")) if p],
    )
    timeline = loader.parse_action_timeline(history)
    qctx = _queue_context(rule_id, rule.get("dossier_state"), kind="rule")
    flag = loader.flagged_state(rule)
    auth = loader.authorship(dossier_text)
    return TEMPLATES.TemplateResponse(
        request,
        "rule.html",
        {
            "rule": rule,
            "dossier_html": dossier_html,
            "telemetry": telemetry,
            "history": history,
            "timeline": timeline,
            "node_id": rule_id,
            "flag": flag,
            "authorship": auth,
            **qctx,
        },
    )


@app.get("/graph/process/{process_id:path}", response_class=HTMLResponse)
def process_detail(request: Request, process_id: str) -> HTMLResponse:
    proc = loader.load_process_by_id(process_id)
    if not proc:
        raise HTTPException(404, f"process not found: {process_id}")
    dossier_text = loader.read_dossier(proc.get("dossier"), loader.LOGIGRAPH)
    dossier_html = markdown_render.render(dossier_text) if dossier_text else None
    history = loader.commit_history(
        loader.LOGIGRAPH,
        [p for p in (proc.get("_node_file"), proc.get("dossier")) if p],
    )
    timeline = loader.parse_action_timeline(history)
    qctx = _queue_context(process_id, proc.get("dossier_state"), kind="processes")
    flag = loader.flagged_state(proc)
    auth = loader.authorship(dossier_text)
    return TEMPLATES.TemplateResponse(
        request,
        "process.html",
        {
            "proc": proc,
            "dossier_html": dossier_html,
            "history": history,
            "timeline": timeline,
            "node_id": process_id,
            "flag": flag,
            "authorship": auth,
            **qctx,
        },
    )


@app.get("/graph/domain/{ont_id:path}/rollup", response_class=HTMLResponse)
def domain_rollup(
    request: Request,
    ont_id: str,
    kind: str | None = None,
    depth: int = 3,
) -> HTMLResponse:
    """Full drill-in rollup for a domain entity. Designed for one-pass
    scanning by the agent — dense rows, all groups expanded, no collapse
    toggles. URL params kind= and depth= are bookmarkable."""
    if depth not in (1, 2, 3):
        raise HTTPException(400, f"depth must be 1, 2, or 3 (got {depth})")
    ont = loader.load_domain_by_id(ont_id)
    if not ont:
        raise HTTPException(404, f"domain node not found: {ont_id}")
    code_rollup = loader.compute_code_rollup(ont, depth=depth)
    kind_filter = set(kind.split(",")) if kind else None
    return TEMPLATES.TemplateResponse(
        request,
        "rollup.html",
        {
            "ont": ont,
            "code_rollup": code_rollup,
            "kind_filter": kind_filter,
            "depth": depth,
            "all_kinds": ["model", "service", "endpoint", "component", "test", "hook", "schema"],
        },
    )


@app.get("/graph/domain/{ont_id:path}", response_class=HTMLResponse)
def domain_detail(request: Request, ont_id: str) -> HTMLResponse:
    ont = loader.load_domain_by_id(ont_id)
    if not ont:
        raise HTTPException(404, f"domain node not found: {ont_id}")
    dossier_text = loader.read_dossier(ont.get("dossier"), loader.LOGIGRAPH)
    dossier_html = markdown_render.render(dossier_text) if dossier_text else None
    history = loader.commit_history(
        loader.LOGIGRAPH,
        [p for p in (ont.get("_node_file"), ont.get("dossier")) if p],
    )
    timeline = loader.parse_action_timeline(history)
    relationships = loader.relationships_for(ont_id)
    collisions = (
        loader.collisions_for_relationship(ont_id)
        if ont.get("subkind") == "relationship" else []
    )
    code_rollup = loader.compute_code_rollup(ont)
    qctx = _queue_context(ont_id, ont.get("dossier_state"), kind="domain")
    flag = loader.flagged_state(ont)
    auth = loader.authorship(dossier_text)
    return TEMPLATES.TemplateResponse(
        request,
        "domain.html",
        {
            "ont": ont,
            "dossier_html": dossier_html,
            "history": history,
            "timeline": timeline,
            "relationships": relationships,
            "collisions": collisions,
            "code_rollup": code_rollup,
            "rollup_summary_cap": 5,  # spec § "Graphui surface": top 5 per kind on summary
            "node_id": ont_id,
            "flag": flag,
            "authorship": auth,
            **qctx,
        },
    )


@app.post("/graph/api/bump")
async def bump_dossier(request: Request) -> JSONResponse:
    """Bump a dossier's status. Dispatches to the right CLI by node-id prefix:
       - rule::*      → bin/logigraph rule-bump
       - role::* / resource::* / attribute::* / relationship::* / action::*
                       → bin/logigraph domain-bump
       - else (depgraph) → bin/depgraph dossier-bump

    POST-only so a wandering GET can't trigger it. UI sends `status: "current"`
    for promote-to-reviewed; the dispatcher translates that to each graph's
    native enum (depgraph: "current"; logigraph: "human_reviewed").
    """
    payload = await request.json()
    node_id = payload.get("node_id")
    ui_status = payload.get("status", "current")
    if not node_id:
        raise HTTPException(400, "missing node_id")
    if ui_status not in ("current", "llm_drafted", "unreviewed"):
        raise HTTPException(400, f"unsupported status: {ui_status}")

    is_rule = node_id.startswith(_LOGIGRAPH_RULE_PREFIX)
    is_process = node_id.startswith(_LOGIGRAPH_PROCESS_PREFIX)
    is_domain = any(node_id.startswith(p) for p in _LOGIGRAPH_DOMAIN_PREFIXES)

    if is_rule:
        # Logigraph rule-bump takes the status as a positional-style enum.
        lg_status = "human_reviewed" if ui_status == "current" else ui_status
        cmd = [str(LOGIGRAPH_BIN), "rule-bump", node_id, "--status", lg_status]
    elif is_process:
        lg_status = "human_reviewed" if ui_status == "current" else ui_status
        cmd = [str(LOGIGRAPH_BIN), "process-bump", node_id, "--status", lg_status]
    elif is_domain:
        lg_status = "human_reviewed" if ui_status == "current" else ui_status
        cmd = [str(LOGIGRAPH_BIN), "domain-bump", node_id, "--status", lg_status]
    else:
        cmd = [str(DEPGRAPH_BIN), "dossier-bump", node_id, "--status", ui_status]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "bump timed out")
    if result.returncode != 0:
        return JSONResponse(
            {"ok": False, "stderr": result.stderr.strip()[:500], "cmd": cmd[0]},
            status_code=500,
        )
    return JSONResponse({"ok": True, "stdout": result.stdout.strip()[:500]})


@app.post("/graph/api/flag")
async def flag_node(request: Request) -> JSONResponse:
    """Set or clear flagged on a node. Body: {node_id, flagged: bool, reason?: string}.
    Dispatches to bin/logigraph or bin/depgraph by node-id prefix.

    Mirrors the existing /graph/api/bump shape — the CLI does the commit;
    graphui just wires the HTTP call to the right binary."""
    payload = await request.json()
    node_id = payload.get("node_id")
    flagged = bool(payload.get("flagged"))
    reason = payload.get("reason") or None
    if not node_id:
        raise HTTPException(400, "missing node_id")

    is_logigraph = (
        node_id.startswith(_LOGIGRAPH_RULE_PREFIX)
        or any(node_id.startswith(p) for p in _LOGIGRAPH_DOMAIN_PREFIXES)
        or node_id.startswith(_LOGIGRAPH_PROCESS_PREFIX)
    )
    bin_path = LOGIGRAPH_BIN if is_logigraph else DEPGRAPH_BIN

    if flagged:
        cmd = [str(bin_path), "flag", node_id]
        if reason:
            cmd += ["--reason", reason]
    else:
        cmd = [str(bin_path), "unflag", node_id]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "flag timed out")
    if result.returncode != 0:
        return JSONResponse(
            {"ok": False, "stderr": result.stderr.strip()[:500], "cmd": cmd[0]},
            status_code=500,
        )
    return JSONResponse({"ok": True, "stdout": result.stdout.strip()[:500]})


@app.post("/graph/api/flags/track")
async def track_flag(request: Request) -> JSONResponse:
    """Flip a fresh flag to tracked by writing/updating a warning entry on
    the affected logigraph node.

    Body: { node_id: "<rule::|role::|resource::|... node id>",
            code: "<warning code>",
            tracking_ref: "<plan path / sha / ticket / free text>" }

    Behavior:
      1. Find the logigraph node JSON for node_id.
      2. Find the warning entry by `code` in its `warnings: []` array; if
         not present, append one (for reconcile-auto warnings the user is
         formalizing for the first time).
      3. Set tracked=true + tracking_ref + discovered_by='author';
         preserve original `discovered_at` and other fields when possible.
      4. Write the node JSON back (canonical pretty-print).
      5. Trigger `bin/logigraph regen` so _meta.json::flags refreshes.
      6. Return ok or stderr."""
    payload = await request.json()
    node_id = payload.get("node_id")
    code = payload.get("code")
    tracking_ref = (payload.get("tracking_ref") or "").strip()
    if not node_id or not code:
        raise HTTPException(400, "missing node_id or code")

    # Resolve node JSON path within the logigraph data dir.
    target_path: Path | None = None
    for sub in ("rules", "domain", "processes"):
        d = loader.LOGIGRAPH_NODES / sub
        if not d.is_dir():
            continue
        for nf in d.glob("*.json"):
            try:
                data = json.loads(nf.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            if data.get("id") == node_id:
                target_path = nf
                break
        if target_path:
            break
    if target_path is None:
        raise HTTPException(404, f"node not found in logigraph corpus: {node_id}")

    node = json.loads(target_path.read_text())
    warnings = list(node.get("warnings") or [])
    today = datetime.date.today().isoformat()
    found_idx = next((i for i, w in enumerate(warnings) if w.get("code") == code), None)
    if found_idx is not None:
        w = warnings[found_idx]
        w["tracked"] = True
        if tracking_ref:
            w["tracking_ref"] = tracking_ref
        warnings[found_idx] = w
    else:
        # Authoring a new structured warning from a reconcile-derived flag.
        # Use sensible defaults; the user can refine later by editing the node.
        warnings.append({
            "code": code,
            "kind": "defect",
            "severity": "medium",
            "message": f"Tracked via graphui Track action (code: {code})",
            "tracked": True,
            "tracking_ref": tracking_ref or None,
            "affected": [node_id],
            "discovered_at": today,
            "discovered_by": "author",
        })
    node["warnings"] = warnings

    new_text = json.dumps(node, indent=2) + "\n"
    tmp = target_path.with_suffix(target_path.suffix + ".tmp")
    tmp.write_text(new_text)
    tmp.replace(target_path)

    # Refresh _meta.json::flags so the dashboard sees the move.
    try:
        subprocess.run([str(LOGIGRAPH_BIN), "regen"], capture_output=True, text=True, timeout=30)
    except subprocess.SubprocessError:
        pass  # non-fatal; the JSON edit is the truth, regen catches up next time

    return JSONResponse({"ok": True, "node": str(target_path.relative_to(loader.LOGIGRAPH))})


@app.get("/graph/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
