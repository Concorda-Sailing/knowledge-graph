"""logigraph process-* lifecycle subcommand handlers.

Subcommands: process-rank, process-draft, process-finalize, process-bump, process-stub.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .context import Context
from ._shared import (
    _process_node_path,
    load_all_nodes,
    load_depgraph_corpus,
    git_commit_if_changed,
    default_actor,
    rewrite_dossier_frontmatter,
)


# ---------------------------------------------------------------------------
# Process-only path helpers
# ---------------------------------------------------------------------------

def _process_dossier_path(ctx: Context, process_id: str) -> Path:
    parts = process_id.split("::")
    return ctx.LOGIGRAPH / "dossiers" / "processes" / f"{parts[1]}__{parts[2]}.md"


def _process_dossier_rel(process_id: str) -> str:
    parts = process_id.split("::")
    return f"dossiers/processes/{parts[1]}__{parts[2]}.md"


# ---------------------------------------------------------------------------
# Process-rank helpers (used only by cmd_process_rank)
# ---------------------------------------------------------------------------

def _existing_process_coverage(ctx: Context, dg_corpus: dict[str, dict] | None = None) -> set[str]:
    """Return the set of depgraph node ids already covered by some existing
    process: directly claimed by any step OR named as flow.endpoint /
    flow.ui_surface OR reachable forward (1-2 hops) from any covered
    endpoint. The forward-reach expansion suppresses convergence-on-model
    candidates that the existing endpoint-anchored processes already
    implicitly own."""
    covered: set[str] = set()
    proc_dir = ctx.NODES / "processes"
    if not proc_dir.is_dir():
        return covered
    direct_endpoints: list[str] = []
    for nf in proc_dir.glob("*.json"):
        try:
            d = json.loads(nf.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        for st in d.get("steps") or []:
            for c in st.get("claims_code") or []:
                cid = c.get("depgraph_id")
                if cid:
                    covered.add(cid)
                    if dg_corpus and (dg_corpus.get(cid) or {}).get("kind") == "endpoint":
                        direct_endpoints.append(cid)
        flow = d.get("flow") or {}
        for k in ("endpoint", "ui_surface"):
            v = flow.get(k)
            if v:
                covered.add(v)
                if dg_corpus and k == "endpoint":
                    direct_endpoints.append(v)
    # Forward-reach expansion: 1-2 hops from each covered endpoint
    if dg_corpus:
        for ep in direct_endpoints:
            node = dg_corpus.get(ep)
            if not node:
                continue
            hop1 = []
            for edge in node.get("depends_on") or []:
                tgt = edge.get("target") if isinstance(edge, dict) else None
                if tgt:
                    covered.add(tgt)
                    hop1.append(tgt)
            for h in hop1:
                node2 = dg_corpus.get(h)
                if not node2:
                    continue
                for edge in node2.get("depends_on") or []:
                    tgt = edge.get("target") if isinstance(edge, dict) else None
                    if tgt:
                        covered.add(tgt)
    return covered


def _kinds_for_claims(claims: list, dg_corpus: dict[str, dict]) -> set[str]:
    """Return the set of distinct depgraph `kind` values represented by these claims."""
    kinds = set()
    for c in claims or []:
        cid = c.get("depgraph_id")
        if not cid:
            continue
        node = dg_corpus.get(cid)
        if node and node.get("kind"):
            kinds.add(node["kind"])
    return kinds


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

def cmd_process_rank(args: argparse.Namespace, ctx: Context) -> int:
    """Stage 1: emit ranked candidate processes from heuristic signals.

    Two signals in this pass:
      rule_shape_mismatch — rule whose claims span >=3 distinct depgraph kinds
                             (it's behaving like a process)
      entrypoint_fan_in   — endpoint whose dependents include >=3 distinct kinds
                             (UI + service + model is the classic flow shape)

    Output is purely advisory. No corpus writes. A second LLM-classification
    stage (the gate against pollution) can be layered on later — this stage
    is deliberately noisy so we can see what falls out.
    """
    dg_corpus = load_depgraph_corpus(ctx)
    covered = _existing_process_coverage(ctx, dg_corpus)
    nodes = load_all_nodes(ctx)
    candidates: list[dict] = []

    # --- Signal A: rule_shape_mismatch -----------------------------------
    for nid, (_path, data) in nodes.items():
        if data.get("kind") != "rule":
            continue
        claims = data.get("claims_code") or []
        kinds = _kinds_for_claims(claims, dg_corpus)
        if len(kinds) < 3:
            continue
        # Skip if all claim anchors are already in some process
        anchors = [c.get("depgraph_id", "") for c in claims if c.get("depgraph_id")]
        if anchors and all(a in covered for a in anchors):
            continue
        # Confidence: 0.6 base + 0.1 per kind above 3, capped at 1.0
        conf = min(1.0, 0.6 + 0.1 * (len(kinds) - 3))
        cat = nid.split("::", 2)[1] if "::" in nid else "uncategorized"
        short = nid.split("::", 2)[2] if nid.count("::") >= 2 else nid.replace("rule::", "")
        candidates.append({
            "signal": "rule_shape_mismatch",
            "anchor": nid,
            "confidence": conf,
            "evidence": f"claims span kinds: {sorted(kinds)} (len={len(kinds)})",
            "suggested": f"process::{cat}::{short}_flow",
            "fan_out": len(claims),
        })

    # --- Signal B: entrypoint_fan_in -------------------------------------
    deps_index_path = ctx.depgraph_dir / "nodes" / "_index" / "dependents.json"
    deps_idx: dict[str, list[dict]] = {}
    if deps_index_path.exists():
        try:
            raw = json.loads(deps_index_path.read_text())
            # Depgraph stores the actual reverse-edge map under "by_target"
            deps_idx = raw.get("by_target") or {}
        except (OSError, json.JSONDecodeError):
            deps_idx = {}
    # Iterate depgraph endpoints
    for nid, dgn in dg_corpus.items():
        if dgn.get("kind") != "endpoint":
            continue
        if nid in covered:
            continue
        dep_entries = deps_idx.get(nid) or []
        # Map dependent source ids to their kinds
        dep_kinds: set[str] = set()
        for de in dep_entries:
            src = de.get("source") or de.get("id")
            if not src:
                continue
            dep_node = dg_corpus.get(src)
            if dep_node and dep_node.get("kind"):
                dep_kinds.add(dep_node["kind"])
        if len(dep_kinds) < 3:
            continue
        # Confidence: 0.55 base + 0.1 per kind above 3 + small bump if fan-out is high
        conf = min(1.0, 0.55 + 0.1 * (len(dep_kinds) - 3) + min(0.2, len(dep_entries) / 100))
        # Derive a suggested name from the endpoint path
        title = dgn.get("title") or nid
        # POST::/api/events/{slug}/register → events_register
        slug = ""
        if "::" in nid:
            try:
                slug = nid.split("::", 1)[1].strip("/").replace("/", "_").replace("{", "").replace("}", "")
            except Exception:
                slug = ""
        candidates.append({
            "signal": "entrypoint_fan_in",
            "anchor": nid,
            "confidence": conf,
            "evidence": f"{len(dep_entries)} dependents across kinds {sorted(dep_kinds)}",
            "suggested": f"process::endpoints::{slug[:50]}_flow",
            "fan_out": len(dep_entries),
        })

    # --- Signal C: forward-edge multi-kind reach from endpoint ----------
    # Walk each endpoint's depends_on transitively (BFS depth 3). If the
    # reached set spans >=3 distinct kinds OR writes >=2 distinct models,
    # the endpoint is orchestrating something flow-shaped.
    def _bfs_forward(start_id: str, max_depth: int = 2) -> dict[str, int]:
        """Return {node_id: depth_first_reached}. Depth 1 = direct depends_on
        edges from the start node. Depth 2 = one further hop. Stops at 2 by
        default to avoid noise from transitively-shared services (auth, db,
        utils) inflating reach counts."""
        depth_of: dict[str, int] = {start_id: 0}
        frontier = [start_id]
        for d in range(1, max_depth + 1):
            next_frontier = []
            for nid in frontier:
                node = dg_corpus.get(nid)
                if not node:
                    continue
                for edge in node.get("depends_on") or []:
                    tgt = edge.get("target") if isinstance(edge, dict) else None
                    if tgt and tgt not in depth_of:
                        depth_of[tgt] = d
                        next_frontier.append(tgt)
            frontier = next_frontier
            if not frontier:
                break
        return {k: v for k, v in depth_of.items() if k != start_id}

    # Build reverse-aggregation alongside Signal C for convergence
    endpoints_reaching: dict[str, set[str]] = {}  # downstream_id -> {endpoint_ids}

    # Lifecycle = state mutation, not aggregation. GET endpoints are reads
    # in REST-shaped APIs; their fan-out reflects read patterns, not flow
    # shape. Skip them from both Signal C and the convergence aggregation
    # used by Signal D so noise like the ICS feed (reads 5 models) doesn't
    # surface as flow-shaped.
    for nid, dgn in dg_corpus.items():
        if dgn.get("kind") != "endpoint":
            continue
        if nid.startswith("GET::"):
            continue
        reached = set(_bfs_forward(nid, max_depth=2).keys())
        # Tally for convergence signal
        for r in reached:
            endpoints_reaching.setdefault(r, set()).add(nid)
        # Signal C own emit
        if nid in covered:
            continue
        kinds = {dg_corpus[r].get("kind", "?") for r in reached if r in dg_corpus}
        kinds.discard("?")
        models = {r for r in reached if r in dg_corpus and dg_corpus[r].get("kind") == "model"}
        if len(kinds) < 3 and len(models) < 2:
            continue
        # Skip pure-test or pure-component fan-out (READ endpoints typically)
        non_trivial_kinds = kinds - {"test", "component", "schema", "route_call"}
        if len(non_trivial_kinds) < 2:
            continue
        conf = min(1.0, 0.55 + 0.1 * (len(kinds) - 3) + 0.15 * max(0, len(models) - 1))
        # Suggested name from endpoint path
        slug = nid.split("::", 1)[1].strip("/").replace("/", "_").replace("{", "").replace("}", "") if "::" in nid else "endpoint"
        candidates.append({
            "signal": "endpoint_forward_reach",
            "anchor": nid,
            "confidence": conf,
            "evidence": f"reaches kinds {sorted(kinds)}; writes {len(models)} model(s)",
            "suggested": f"process::endpoints::{slug[:50]}_orchestration",
            "fan_out": len(reached),
        })

    # --- Signal D+E (unified): convergence on shared downstream ---------
    # Kind-weighted; only emit when >=3 endpoints converge AND the
    # downstream node isn't itself an endpoint or already covered.
    KIND_WEIGHT = {"model": 1.0, "hook": 0.85, "service": 0.65, "schema": 0.45}
    for downstream_id, endpoints in endpoints_reaching.items():
        if downstream_id in covered:
            continue
        n_eps = len(endpoints)
        if n_eps < 3:
            continue
        # Skip hubs: nodes touched by too many endpoints aren't flow centers,
        # they're foundational primitives (Person, Event, the auth context).
        # Threshold tuned by inspection — anything >15 endpoints in a corpus
        # of ~300 is reading like a hub.
        if n_eps > 15:
            continue
        ds_node = dg_corpus.get(downstream_id)
        if not ds_node:
            continue
        ds_kind = ds_node.get("kind", "?")
        if ds_kind not in KIND_WEIGHT:
            continue
        # confidence: kind weight × concentration factor (peaks 4-7 endpoints)
        kw = KIND_WEIGHT[ds_kind]
        # Gaussian-ish bump centered at 5 endpoints
        conc = 1.0 - abs(n_eps - 5) / 12.0
        conf = min(1.0, kw * max(0.3, conc))
        # Suggested name from downstream id
        # e.g. api::models/order.py::Order → process::order::lifecycle
        suggest_slug = downstream_id.split("::")[-1].lower()
        suggest_cat = ds_kind  # "model", "hook", etc.
        candidates.append({
            "signal": f"convergence_on_{ds_kind}",
            "anchor": downstream_id,
            "confidence": conf,
            "evidence": f"{len(endpoints)} endpoint(s) reach this {ds_kind}",
            "suggested": f"process::{suggest_cat}::{suggest_slug}_lifecycle",
            "fan_out": len(endpoints),
        })

    # --- Signal F — UI-initiated flow: pages and hooks --------------------
    # A typical UI flow starts at a button (component in
    # src/app/**/page.tsx) or at a reusable hook (kind=hook in src/hooks/).
    # Walk forward from each candidate entry point; require it to reach
    # both an endpoint AND a model for the flow to be "complete."
    for nid, dgn in dg_corpus.items():
        kind = dgn.get("kind")
        src = dgn.get("source") or {}
        path = src.get("path") or ""

        # Classify entry type
        is_page = kind == "component" and path.endswith("/page.tsx")
        is_hook = kind == "hook"

        if not (is_page or is_hook):
            continue
        if nid in covered:
            continue

        reach_map = _bfs_forward(nid, max_depth=4)
        if not reach_map:
            continue

        endpoints_reached = {r for r in reach_map if r in dg_corpus and dg_corpus[r].get("kind") == "endpoint"}
        models_reached = {r for r in reach_map if r in dg_corpus and dg_corpus[r].get("kind") == "model"}

        if not endpoints_reached or not models_reached:
            continue

        # Confidence: page > hook (pages are unambiguous user actions; hooks
        # may be shared utilities). Bump by depth-1 closeness (the more
        # direct the reach to the endpoint, the cleaner the flow shape).
        min_endpoint_depth = min(reach_map.get(e, 99) for e in endpoints_reached)
        base = 0.75 if is_page else 0.55
        conf = min(1.0, base + 0.1 * max(0, 3 - min_endpoint_depth))

        signal_name = "page_initiated_flow" if is_page else "hook_initiated_flow"
        # Suggested name from path
        slug = path.replace("src/", "").replace("/", "_").replace(".tsx", "").replace(".ts", "").lower()
        category = "ui" if is_page else "hooks"
        candidates.append({
            "signal": signal_name,
            "anchor": nid,
            "confidence": conf,
            "evidence": f"reaches {len(endpoints_reached)} endpoint(s), {len(models_reached)} model(s); nearest endpoint at depth {min_endpoint_depth}",
            "suggested": f"process::{category}::{slug[:50]}_flow",
            "fan_out": len(endpoints_reached) + len(models_reached),
        })

    # --- Signal G — headless flow: cron / worker / handler entry points ---
    # A node with NO reverse-edge dependents AND non-(endpoint|component|test|hook)
    # kind that still reaches endpoints/models via its forward graph is being
    # entered from outside the dependency graph — i.e. a cron job, a worker
    # function, a signal handler, a script.
    HEADLESS_SKIP_KINDS = {"endpoint", "component", "test", "hook", "schema", "model"}
    # Test-named paths aren't flows we want to document as processes —
    # they're test infrastructure that ENTERS the system from outside but
    # isn't user-facing or scheduled production work. Path-shaped hints
    # only (no hardcoded repo basenames).
    TEST_PATH_HINTS = ("/tests/", "tests/", ".spec.ts", ".spec.tsx", "_test.py", "test_", "/spec/")
    # API client wrappers (lib/api.ts, lib/api-client.ts) and client-side
    # hooks/utils directories — these are thin shells or caching primitives.
    # Calling them is "calling the endpoint." They reach endpoints+models
    # but the flow lives in the endpoint, not the wrapper. Path-shaped
    # conventions only, not literal project repo names.
    API_CLIENT_PATH_HINTS = (
        "lib/api.ts", "lib/api-client.ts", "lib/client.ts",
        "api_client.py", "client.py",
        "/hooks/", "hooks/use-",   # React-convention client hooks
        "/utils/", "/util/",        # generic util dirs
    )
    for nid, dgn in dg_corpus.items():
        kind = dgn.get("kind")
        if kind in HEADLESS_SKIP_KINDS:
            continue
        if nid in covered:
            continue
        # No one depends on this node — it's an entry from outside
        if deps_idx.get(nid):
            continue

        src = dgn.get("source") or {}
        path = src.get("path") or ""
        repo = src.get("repo") or ""
        # Skip test infrastructure (path-shaped hints only)
        if any(h in path for h in TEST_PATH_HINTS):
            continue
        # Skip API client wrappers — the flow is the endpoint they call
        if any(h in path for h in API_CLIENT_PATH_HINTS):
            continue

        reach_map = _bfs_forward(nid, max_depth=3)
        if not reach_map:
            continue
        endpoints_reached = {r for r in reach_map if r in dg_corpus and dg_corpus[r].get("kind") == "endpoint"}
        models_reached = {r for r in reach_map if r in dg_corpus and dg_corpus[r].get("kind") == "model"}
        # Headless needs to TOUCH state to be a flow; needs at least one model
        if not models_reached:
            continue

        # Suggested name from path
        slug = path.replace("/", "_").replace(".py", "").replace(".ts", "").lower()[:50]
        conf = min(1.0, 0.6 + 0.05 * len(models_reached) + (0.1 if endpoints_reached else 0))

        candidates.append({
            "signal": "headless_initiated_flow",
            "anchor": nid,
            "confidence": conf,
            "evidence": f"no reverse deps; reaches {len(endpoints_reached)} endpoint(s), {len(models_reached)} model(s)",
            "suggested": f"process::headless::{slug}_flow",
            "fan_out": len(reach_map),
        })

    # Sort by confidence, then fan_out, descending
    candidates.sort(key=lambda c: (-c["confidence"], -c["fan_out"]))
    if args.limit:
        candidates = candidates[: args.limit]

    if args.format == "json":
        print(json.dumps(candidates, indent=2))
        return 0

    print(f"# Process candidates (Stage 1 — heuristic, no LLM gate)\n")
    print(f"  {len(candidates)} candidates after deduplication against existing processes\n")
    print(f"  {'#':>3}  {'conf':>5}  {'signal':<22}  {'fan':>4}  anchor → suggested")
    print(f"  {'-'*3}  {'-'*5}  {'-'*22}  {'-'*4}  {'-'*70}")
    for i, c in enumerate(candidates, 1):
        print(f"  {i:>3}  {c['confidence']:>5.2f}  {c['signal']:<22}  {c['fan_out']:>4}  {c['anchor']}")
        print(f"  {'':>3}  {'':>5}  {'':>22}  {'':>4}    → {c['suggested']}")
        print(f"  {'':>3}  {'':>5}  {'':>22}  {'':>4}    {c['evidence']}")
    return 0


def cmd_process_stub(args: argparse.Namespace, ctx: Context) -> int:
    """Materialize a stub process node from a flow.action + ordered list of
    steps. Each --step has form 'step_id:title:depgraph_id[|where]'. Pass
    --step multiple times to seed multi-step flows."""
    process_id = args.id
    if not process_id.startswith("process::"):
        print(f"id must start with process:: — got {process_id}", file=sys.stderr)
        return 1
    node_path = _process_node_path(ctx, process_id)
    if node_path.exists() and not args.force:
        print(f"node already exists: {node_path.relative_to(ctx.LOGIGRAPH)}; pass --force to overwrite", file=sys.stderr)
        return 1

    if not args.step:
        print("at least one --step is required (form 'step_id:title:depgraph_id[|where]')", file=sys.stderr)
        return 1

    steps = []
    for s in args.step:
        # format: "step_id:title:depgraph_id[|where]"
        parts_s = s.split(":", 2)
        if len(parts_s) != 3:
            print(f"--step must be 'step_id:title:depgraph_id[|where]' (got: {s})", file=sys.stderr)
            return 1
        step_id, title, claim_part = parts_s
        if "|" in claim_part:
            dg_id, where = claim_part.split("|", 1)
        else:
            dg_id, where = claim_part, ""
        steps.append({
            "id": step_id.strip(),
            "title": title.strip(),
            "claims_code": [{
                "depgraph_id": dg_id.strip(),
                "role": "implements",
                "where": where.strip(),
                "confidence": "medium",
                "remote_hash": "",
                "stale": False,
            }],
        })

    flow = {"action": args.flow_action or "TODO: describe what kicks off this flow"}
    if args.flow_ui_surface:
        flow["ui_surface"] = args.flow_ui_surface
    if args.flow_endpoint:
        flow["endpoint"] = args.flow_endpoint

    title = args.title or process_id.split("::", 2)[2].replace("_", " ").capitalize()
    summary = args.summary or "TODO: one-paragraph summary of what this flow does"

    import hashlib as _h
    structural_hash = _h.sha256(process_id.encode()).hexdigest()
    node = {
        "schema_version": 2,
        "id": process_id,
        "kind": "process",
        "title": title,
        "summary": summary,
        "flow": flow,
        "steps": steps,
        "definition_status": "stub",
        "structural_hash": structural_hash,
        "dossier": _process_dossier_rel(process_id),
    }
    if args.enforces_rule:
        node["enforces_rules"] = list(args.enforces_rule)

    node_path.parent.mkdir(parents=True, exist_ok=True)
    node_path.write_text(json.dumps(node, indent=2) + "\n")
    print(f"wrote {node_path.relative_to(ctx.LOGIGRAPH)}")
    print(f"status: stub — next: bin/logigraph process-draft '{process_id}'")
    return 0


def cmd_process_draft(args: argparse.Namespace, ctx: Context) -> int:
    """Emit an LLM-drafting context bundle for a process: the stub node +
    each step's claim_code's depgraph dossier + sibling process examples
    + recent commits touching any step's anchor file."""
    process_id = args.id
    node_path = _process_node_path(ctx, process_id)
    if not node_path.exists():
        print(f"no process node at {node_path.relative_to(ctx.LOGIGRAPH)} — try `process-stub` first", file=sys.stderr)
        return 1
    node = json.loads(node_path.read_text())

    out = []
    out.append(f"# process-draft context bundle: {process_id}\n")
    out.append("## Target process\n")
    out.append(f"- id: {process_id}")
    out.append(f"- title: {node.get('title', '')}")
    out.append(f"- summary: {node.get('summary', '')}")
    flow = node.get("flow") or {}
    out.append(f"- flow.action: {flow.get('action', '?')}")
    if flow.get("endpoint"):
        out.append(f"- flow.endpoint: `{flow['endpoint']}`")
    if flow.get("ui_surface"):
        out.append(f"- flow.ui_surface: `{flow['ui_surface']}`")
    out.append(f"- steps ({len(node.get('steps') or [])}):")
    for st in node.get("steps") or []:
        for c in st.get("claims_code") or []:
            out.append(f"  - {st.get('id','?')} \"{st.get('title','?')}\" → `{c.get('depgraph_id','?')}` ({c.get('where','')})")
    if node.get("enforces_rules"):
        out.append(f"- enforces_rules: {', '.join(node['enforces_rules'])}")
    out.append("")

    out.append("## Existing process dossiers (style examples — read these first)\n")
    proc_dossier_dir = ctx.LOGIGRAPH / "dossiers" / "processes"
    if proc_dossier_dir.exists():
        for sibling in sorted(proc_dossier_dir.glob("*.md"))[:5]:
            out.append(f"### {sibling.stem}\n")
            out.append("```markdown")
            out.append(sibling.read_text().rstrip())
            out.append("```\n")

    out.append("## Step anchors (depgraph dossiers + source paths)\n")
    dg_corpus = load_depgraph_corpus(ctx)
    for st in node.get("steps") or []:
        out.append(f"### step `{st.get('id','?')}` — {st.get('title','')}\n")
        for c in st.get("claims_code") or []:
            dg_id = c.get("depgraph_id", "")
            out.append(f"#### {dg_id}\n")
            if dg_id in dg_corpus:
                dgn = dg_corpus[dg_id]
                src = dgn.get("source") or {}
                out.append(f"- repo/path: `{src.get('repo','')}/{src.get('path','')}` line {src.get('line','?')}")
                dossier_rel = dgn.get("dossier")
                if dossier_rel:
                    p = ctx.depgraph_dir / dossier_rel
                    if p.exists():
                        out.append(f"- dossier: `depgraph/{dossier_rel}`\n")
                        out.append("```markdown")
                        out.append(p.read_text().rstrip())
                        out.append("```\n")
            else:
                out.append(f"_(not in depgraph corpus — claim points at an HTTP route or extractor blind spot)_\n")

    out.append("## Authoring instructions\n")
    out.append(
        "Write the dossier body markdown ONLY (no frontmatter — `process-finalize` adds it).\n"
        "Processes are POINTER-SHAPED, not narrative. The dossier should be terse — "
        "typically a single section explaining WHY this is one process and not N rules, "
        "and any cross-cutting invariants the steps share that aren't captured by an "
        "individual rule. Recommended sections:\n\n"
        "  ## Why this is a process and not N rules\n"
        "  ## Invariants across the flow\n"
        "  ## Failure modes / partial-progress states\n"
        "  ## State modifications (what the flow exists to do)\n"
        "  ## Side effects (incidental but worth knowing)\n"
        "  ## Open design questions  (omit if none — but include it whenever\n"
        "                              an asymmetry, race window, missing\n"
        "                              column, or other unresolved concern\n"
        "                              became visible while writing the body)\n\n"
        "Reference real commit hashes / PR ids when citing the flow's origin. Keep "
        "everything tight. The node JSON itself carries the structured step + claim list "
        "— don't duplicate that in prose."
    )

    print("\n".join(out))
    return 0


def cmd_process_finalize(args: argparse.Namespace, ctx: Context) -> int:
    """Write a process dossier body file to the canonical path with frontmatter
    set to llm_drafted. Mirrors rule-finalize."""
    process_id = args.id
    node_path = _process_node_path(ctx, process_id)
    if not node_path.exists():
        print(f"no process node at {node_path.relative_to(ctx.LOGIGRAPH)} — try `process-stub` first", file=sys.stderr)
        return 1
    node = json.loads(node_path.read_text())

    body_file = Path(args.body_file)
    if not body_file.exists():
        print(f"body file not found: {body_file}", file=sys.stderr)
        return 1
    body = body_file.read_text().strip()

    import datetime as _dt
    today = _dt.date.today().isoformat()
    title = node.get("title") or process_id

    fm_lines = [
        "---",
        f"node_id: {process_id}",
        "node_kind: process",
        "definition_status: llm_drafted",
        f"last_reviewed: {today}",
        f"last_reviewed_against_hash: {node.get('structural_hash')}",
    ]
    if args.authored_by:
        fm_lines.append("authored_by:")
        for a in args.authored_by:
            fm_lines.append(f"  - {a}")
    fm_lines.append("---")
    frontmatter = "\n".join(fm_lines) + "\n\n" + f"# {title}\n\n"

    dossier_path = _process_dossier_path(ctx, process_id)
    dossier_path.parent.mkdir(parents=True, exist_ok=True)
    dossier_path.write_text(frontmatter + body + "\n")
    node["definition_status"] = "llm_drafted"
    node_path.write_text(json.dumps(node, indent=2) + "\n")
    print(f"wrote {dossier_path.relative_to(ctx.LOGIGRAPH)}")
    print(f"updated {node_path.relative_to(ctx.LOGIGRAPH)} → definition_status: llm_drafted")
    print(f"next: review the dossier, then `bin/logigraph process-bump '{process_id}'`")
    return 0


def cmd_process_bump(args: argparse.Namespace, ctx: Context) -> int:
    """Promote a process node's definition_status (default: → human_reviewed).
    Updates both the JSON node and the dossier frontmatter."""
    process_id = args.id
    try:
        node_path = _process_node_path(ctx, process_id)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1
    if not node_path.exists():
        print(f"no process node: {node_path.relative_to(ctx.LOGIGRAPH)}", file=sys.stderr)
        return 1
    node = json.loads(node_path.read_text())
    new_status = args.status
    node["definition_status"] = new_status
    node_path.write_text(json.dumps(node, indent=2) + "\n")
    print(f"bumped {node_path.relative_to(ctx.LOGIGRAPH)} → definition_status: {new_status}")

    dossier_path = _process_dossier_path(ctx, process_id)
    actor = args.actor or default_actor()
    paths = [node_path]
    if dossier_path.exists():
        rewrite_dossier_frontmatter(dossier_path, node.get("structural_hash", ""), new_status, actor)
        print(f"updated {dossier_path.relative_to(ctx.LOGIGRAPH)} frontmatter")
        paths.append(dossier_path)

    prefix = "review" if new_status == "human_reviewed" else "chore(bump)"
    git_commit_if_changed(ctx, paths, f"{prefix}: {process_id}")
    return 0


# ---------------------------------------------------------------------------
# Subparser registration
# ---------------------------------------------------------------------------

def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p_pr = sub.add_parser("process-rank", help="Stage 1: emit heuristic process candidates (no corpus writes)")
    p_pr.add_argument("--limit", type=int, default=30, help="Max candidates (default 30)")
    p_pr.add_argument("--format", choices=["text", "json"], default="text")
    p_pr.set_defaults(func=cmd_process_rank)

    p_ps = sub.add_parser("process-stub", help="Materialize a process candidate as a stub JSON node")
    p_ps.add_argument("id", help="process::category::short_name")
    p_ps.add_argument("--title")
    p_ps.add_argument("--summary", help="One-paragraph elevator pitch for the flow")
    p_ps.add_argument("--flow-action", help="What kicks off the flow ('User clicks Accept on…', 'Stripe webhook fires', 'Cron at 02:00 UTC')")
    p_ps.add_argument("--flow-endpoint", help="Optional depgraph node id of the HTTP endpoint that receives the trigger")
    p_ps.add_argument("--flow-ui-surface", help="Optional depgraph node id of the UI element that triggers the flow")
    p_ps.add_argument("--step", action="append", default=[],
                      help="Format: 'step_id:title:depgraph_id[|where]'; repeat for ordered steps")
    p_ps.add_argument("--enforces-rule", action="append", default=[],
                      help="Rule id this process enforces (repeatable)")
    p_ps.add_argument("--force", action="store_true", help="Overwrite existing node")
    p_ps.set_defaults(func=cmd_process_stub)

    p_pd = sub.add_parser("process-draft", help="Emit an LLM-drafting context bundle for one process")
    p_pd.add_argument("id")
    p_pd.set_defaults(func=cmd_process_draft)

    p_pf = sub.add_parser("process-finalize", help="Save an LLM-drafted process dossier body to canonical path")
    p_pf.add_argument("id")
    p_pf.add_argument("body_file", help="Path to dossier body markdown (no frontmatter)")
    p_pf.add_argument("--authored-by", action="append", default=[],
                      help="Actor that drafted the body (model id or person). Repeat for multiple authors.")
    p_pf.set_defaults(func=cmd_process_finalize)

    p_pb = sub.add_parser("process-bump", help="Promote a process node's definition_status (default → human_reviewed)")
    p_pb.add_argument("id")
    p_pb.add_argument("--status", default="human_reviewed", choices=["stub", "llm_drafted", "human_reviewed"])
    p_pb.add_argument("--actor", default=None, help="Reviewer (default: git config user.name)")
    p_pb.set_defaults(func=cmd_process_bump)
