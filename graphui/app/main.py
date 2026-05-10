"""FastAPI app for the depgraph + logigraph viewer.

Mount-prefix is `/graph` so it can sit behind the dev box Caddy at
`https://dev.members.massbaysailing.org/graph/`.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import subprocess

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import loader
from . import markdown_render

DEPGRAPH_BIN = Path.home() / "concorda" / "depgraph" / "bin" / "depgraph"

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
    "component", "hook", "test", "rule", "ontology",
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
            "ontology_count": len(lg["ontology"]),
            "meta": meta,
        },
    )


@app.get("/graph/api/nodes.json")
def nodes_json() -> JSONResponse:
    """Flat node list for client-side filter/sort on the index page.
    Includes both depgraph nodes and logigraph rules+ontology, distinguished
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
    for o in lg["ontology"]:
        out.append({
            "id": o["id"],
            "kind": "ontology",
            "title": o.get("title", o["id"]),
            "tier": "*",
            "fan_out": 0,
            "state": o["dossier_state"],
            "src": "",
            "href": f"/graph/ontology/{o['id']}",
        })
    return JSONResponse(out)


def _review_queue(tier: str | None = None, kind: str | None = None) -> list[dict]:
    """Tier B (or filtered) llm_drafted nodes ranked by fan_out desc.
    Drives the review queue + node detail prev/next navigation."""
    rows = []
    for n in loader.load_depgraph_nodes():
        if n.get("dossier_state") != "llm_drafted":
            continue
        if tier and n.get("tier") != tier:
            continue
        if kind and n.get("kind") != kind:
            continue
        rows.append(n)
    rows.sort(key=lambda r: (-r.get("fan_out", 0), r["id"]))
    return rows


@app.get("/graph/review", response_class=HTMLResponse)
def review_queue(request: Request, tier: str = "B", kind: str | None = None) -> HTMLResponse:
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
    return TEMPLATES.TemplateResponse(
        request,
        "rule.html",
        {
            "rule": rule,
            "dossier_html": dossier_html,
            "telemetry": telemetry,
        },
    )


@app.get("/graph/ontology/{ont_id:path}", response_class=HTMLResponse)
def ontology_detail(request: Request, ont_id: str) -> HTMLResponse:
    ont = loader.load_ontology_by_id(ont_id)
    if not ont:
        raise HTTPException(404, f"ontology node not found: {ont_id}")
    dossier_text = loader.read_dossier(ont.get("dossier"), loader.LOGIGRAPH)
    dossier_html = markdown_render.render(dossier_text) if dossier_text else None
    return TEMPLATES.TemplateResponse(
        request,
        "ontology.html",
        {
            "ont": ont,
            "dossier_html": dossier_html,
        },
    )


@app.post("/graph/api/bump")
async def bump_dossier(request: Request) -> JSONResponse:
    """Run `bin/depgraph dossier-bump <node_id>`. Used by the Approve button
    on the node detail page. POST-only so a wandering GET can't trigger it."""
    payload = await request.json()
    node_id = payload.get("node_id")
    new_status = payload.get("status", "current")
    if not node_id:
        raise HTTPException(400, "missing node_id")
    if new_status not in ("current", "llm_drafted", "unreviewed"):
        raise HTTPException(400, f"unsupported status: {new_status}")
    try:
        result = subprocess.run(
            [str(DEPGRAPH_BIN), "dossier-bump", node_id, "--status", new_status],
            capture_output=True, text=True, timeout=15,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "dossier-bump timed out")
    if result.returncode != 0:
        return JSONResponse(
            {"ok": False, "stderr": result.stderr.strip()[:500]},
            status_code=500,
        )
    return JSONResponse({"ok": True, "stdout": result.stdout.strip()[:500]})


@app.get("/graph/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
