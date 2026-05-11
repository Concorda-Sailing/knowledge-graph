"""FastAPI app for the depgraph + logigraph viewer.

Mount-prefix is `/graph` so it can sit behind the dev box Caddy at
`https://dev.members.massbaysailing.org/graph/`.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import os
import subprocess

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import loader
from . import markdown_render

# Where the framework CLIs live. Env vars let us point at the tool
# repos without coupling graphui to a specific layout. Defaults match
# the current ~/tools/ install.
DEPGRAPH_BIN = Path(
    os.environ.get("DEPGRAPH_BIN")
    or (Path.home() / "tools" / "depgraph" / "bin" / "depgraph")
)
LOGIGRAPH_BIN = Path(
    os.environ.get("LOGIGRAPH_BIN")
    or (Path.home() / "tools" / "logigraph" / "bin" / "logigraph")
)


# Node-id prefixes used to route bump requests to the right CLI.
_LOGIGRAPH_RULE_PREFIX = "rule::"
_LOGIGRAPH_DOMAIN_PREFIXES = (
    "role::", "resource::", "attribute::", "relationship::", "action::",
)

APP_ROOT = Path(__file__).parent
TEMPLATES = Jinja2Templates(directory=str(APP_ROOT / "templates"))
STATIC = APP_ROOT / "static"

app = FastAPI(title="Concorda graphui", openapi_url=None, docs_url=None)
app.mount("/graph/static", StaticFiles(directory=str(STATIC)), name="static")


# ----- Helpers ----------------------------------------------------------------

STATE_ORDER = ["current", "llm_drafted", "unreviewed", "stale", "missing"]
TIER_ORDER = ["A", "B", "C", "*"]
KIND_ORDER = [
    "model", "service", "endpoint", "schema",
    "component", "hook", "test", "rule", "domain",
]


def _kind_sort(k: str) -> int:
    return KIND_ORDER.index(k) if k in KIND_ORDER else 99


# ----- Routes -----------------------------------------------------------------

@app.get("/graph/", response_class=HTMLResponse)
@app.get("/graph", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    nodes = loader.load_depgraph_nodes()
    lg = loader.load_logigraph_nodes()
    matrix = loader.coverage_matrix()
    meta = loader.load_meta()
    # Stable kind order for matrix
    matrix_rows = []
    for kind in sorted(matrix.keys(), key=_kind_sort):
        row = {"kind": kind, "tiers": {}}
        for tier in TIER_ORDER:
            cell = matrix[kind].get(tier)
            if cell is None:
                continue
            total = sum(cell.values())
            current = cell.get("current", 0) + cell.get("llm_drafted", 0)
            row["tiers"][tier] = {
                "total": total,
                "current": cell.get("current", 0),
                "llm_drafted": cell.get("llm_drafted", 0),
                "unreviewed": cell.get("unreviewed", 0),
                "stale": cell.get("stale", 0),
                "missing": cell.get("missing", 0),
                "pct": int(round(100 * current / total)) if total else 0,
            }
        matrix_rows.append(row)
    return TEMPLATES.TemplateResponse(
        request,
        "index.html",
        {
            "matrix_rows": matrix_rows,
            "tier_order": TIER_ORDER,
            "depgraph_node_count": len(nodes),
            "rule_count": len(lg["rules"]),
            "domain_count": len(lg["domain"]),
            "meta": meta,
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
    rows.sort(key=lambda r: (-r.get("fan_out", 0), r["id"]))
    return rows


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
    telemetry = loader.telemetry_for_node(node_id)
    # If this node is in the review queue, compute prev/next siblings.
    prev_node = next_node = None
    queue_position = queue_total = None
    if node.get("dossier_state") == "llm_drafted":
        queue = _review_queue(tier=node["tier"], kind=node.get("kind"))
        ids = [n["id"] for n in queue]
        if node_id in ids:
            i = ids.index(node_id)
            queue_position = i + 1
            queue_total = len(ids)
            if i > 0:
                prev_node = queue[i - 1]
            if i < len(queue) - 1:
                next_node = queue[i + 1]
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
            "prev_node": prev_node,
            "next_node": next_node,
            "queue_position": queue_position,
            "queue_total": queue_total,
            "history": history,
            "telemetry": telemetry,
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
    return TEMPLATES.TemplateResponse(
        request,
        "rule.html",
        {
            "rule": rule,
            "dossier_html": dossier_html,
            "telemetry": telemetry,
            "history": history,
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
    relationships = loader.relationships_for(ont_id)
    collisions = (
        loader.collisions_for_relationship(ont_id)
        if ont.get("subkind") == "relationship" else []
    )
    return TEMPLATES.TemplateResponse(
        request,
        "domain.html",
        {
            "ont": ont,
            "dossier_html": dossier_html,
            "history": history,
            "relationships": relationships,
            "collisions": collisions,
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
    is_domain = any(node_id.startswith(p) for p in _LOGIGRAPH_DOMAIN_PREFIXES)

    if is_rule:
        # Logigraph rule-bump takes the status as a positional-style enum.
        lg_status = "human_reviewed" if ui_status == "current" else ui_status
        cmd = [str(LOGIGRAPH_BIN), "rule-bump", node_id, "--status", lg_status]
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


@app.get("/graph/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
