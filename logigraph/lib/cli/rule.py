"""logigraph rule-* lifecycle subcommand handlers.

Subcommands: rule-rank, rule-draft, rule-finalize, rule-bump, rule-stub.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .context import Context
from ._shared import (
    _rule_node_path,
    load_all_nodes,
    load_depgraph_corpus,
    git_commit_if_changed,
    default_actor,
    rewrite_dossier_frontmatter,
)


# ---------------------------------------------------------------------------
# Rule-only path helpers (not shared across other subcommand groups)
# ---------------------------------------------------------------------------

def _rule_dossier_path(ctx: Context, rule_id: str) -> Path:
    parts = rule_id.split("::", 2)
    return ctx.LOGIGRAPH / "dossiers" / "rules" / f"{parts[1]}__{parts[2]}.md"


def _rule_dossier_rel(rule_id: str) -> str:
    parts = rule_id.split("::", 2)
    return f"dossiers/rules/{parts[1]}__{parts[2]}.md"


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

def cmd_rule_rank(args: argparse.Namespace, ctx: Context) -> int:
    """List rule nodes ranked by definition_status (stub > llm_drafted > human_reviewed)
    then by claim count desc. Useful for picking the next rule to author."""
    rules_dir = ctx.NODES / "rules"
    rows = []
    if not rules_dir.is_dir():
        print("no rules directory")
        return 0
    for nf in sorted(rules_dir.glob("*.json")):
        try:
            d = json.loads(nf.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        rows.append({
            "id": d.get("id", nf.stem),
            "title": d.get("title", ""),
            "status": d.get("definition_status", "?"),
            "claims": len(d.get("claims_code") or []),
            "confidence": d.get("confidence", "?"),
        })
    status_order = {"stub": 0, "llm_drafted": 1, "human_reviewed": 2}
    rows.sort(key=lambda r: (status_order.get(r["status"], 99), -r["claims"]))
    if args.status:
        rows = [r for r in rows if r["status"] == args.status]
    print(f"{'#':>3}  {'status':<14}  {'claims':>6}  {'conf':<6}  id")
    print("-" * 100)
    for i, r in enumerate(rows, 1):
        print(f"{i:>3}  {r['status']:<14}  {r['claims']:>6}  {r['confidence']:<6}  {r['id']}")
    return 0


def cmd_rule_draft(args: argparse.Namespace, ctx: Context) -> int:
    """Emit an LLM-drafting context bundle for a rule: template + sibling
    rule examples + each claim_code's depgraph dossier + each domain
    reference's dossier. Pipe to a file and feed to a drafting agent."""
    rule_id = args.id
    node_path = _rule_node_path(ctx, rule_id)
    if not node_path.exists():
        print(f"no rule node at {node_path.relative_to(ctx.LOGIGRAPH)} — try `rule-stub` first", file=sys.stderr)
        return 1
    node = json.loads(node_path.read_text())

    out = []
    out.append(f"# rule-draft context bundle: {rule_id}\n")
    out.append(f"## Target rule\n")
    out.append(f"- id: {rule_id}")
    out.append(f"- title: {node.get('title', '')}")
    out.append(f"- statement: {node.get('statement', '')}")
    out.append(f"- references_domain: {', '.join(node.get('references_domain') or [])}")
    out.append(f"- claims_code ({len(node.get('claims_code') or [])}):")
    for c in node.get("claims_code") or []:
        out.append(f"  - {c.get('role','?')} → `{c.get('depgraph_id','?')}` ({c.get('where','')})")
    out.append("")

    template_path = ctx.LOGIGRAPH / "schema" / "rule_dossier.template.md"
    if template_path.exists():
        out.append("## Authoring template (required sections)\n")
        out.append("```markdown")
        out.append(template_path.read_text().rstrip())
        out.append("```\n")

    out.append("## Existing rule dossiers (style examples — read these first)\n")
    for sibling in sorted((ctx.LOGIGRAPH / "dossiers" / "rules").glob("*.md")):
        out.append(f"### {sibling.stem}\n")
        out.append("```markdown")
        out.append(sibling.read_text().rstrip())
        out.append("```\n")

    out.append("## Claim sources (depgraph dossiers + source paths)\n")
    for c in node.get("claims_code") or []:
        dg_id = c.get("depgraph_id", "")
        out.append(f"### {dg_id}\n")
        # find the depgraph node json
        dg_corpus = load_depgraph_corpus(ctx)
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
            out.append(f"_(not in depgraph corpus — claim points at an HTTP route or an extractor blind spot)_\n")

    out.append("## Domain references\n")
    # Index domain nodes by id (filenames don't always match the id triple).
    domain_by_id: dict[str, dict] = {}
    domain_dir = ctx.NODES / "domain"
    for of in domain_dir.glob("*.json"):
        try:
            d = json.loads(of.read_text())
            if d.get("id"):
                domain_by_id[d["id"]] = d
        except (OSError, json.JSONDecodeError):
            continue
    for oid in node.get("references_domain") or []:
        ontd = domain_by_id.get(oid)
        if ontd:
            out.append(f"### {oid}")
            out.append(f"- title: {ontd.get('title','')}")
            out.append(f"- summary: {ontd.get('summary','')}\n")
            dossier_rel = ontd.get("dossier")
            if dossier_rel:
                p = ctx.LOGIGRAPH / dossier_rel
                if p.exists():
                    out.append("```markdown")
                    out.append(p.read_text().rstrip())
                    out.append("```\n")
        else:
            out.append(f"### {oid} _(stub — domain node not yet authored)_\n")

    out.append("## Authoring instructions\n")
    out.append(
        "Write the dossier body markdown ONLY (no frontmatter — `rule-finalize` adds it).\n"
        "Required sections, in order: `## The rule`, `## Why it exists`, `## Examples`, "
        "`## Counter-examples (what the rule does NOT do)`, `## Decision table`, "
        "`## Edge cases`, `## Surfaces`. The Decision table is mandatory and is the "
        "primary reading surface for the LLM consumer — make it exhaustive over realistic "
        "boundary conditions.\n\n"
        "Reference real commit hashes / PR ids when citing the rule's origin. Cite "
        "claim-code locations with `file:line` form. Keep the prose tight; the table is the "
        "load-bearing artifact."
    )

    print("\n".join(out))
    return 0


def cmd_rule_finalize(args: argparse.Namespace, ctx: Context) -> int:
    """Write a rule dossier body file to the canonical path with frontmatter
    set to llm_drafted. Mirrors `bin/depgraph dossier-finalize`."""
    rule_id = args.id
    node_path = _rule_node_path(ctx, rule_id)
    if not node_path.exists():
        print(f"no rule node at {node_path.relative_to(ctx.LOGIGRAPH)} — try `rule-stub` first", file=sys.stderr)
        return 1
    node = json.loads(node_path.read_text())

    body_file = Path(args.body_file)
    if not body_file.exists():
        print(f"body file not found: {body_file}", file=sys.stderr)
        return 1
    body = body_file.read_text().strip()

    import datetime as _dt
    today = _dt.date.today().isoformat()
    title = node.get("title") or rule_id
    fan_out = len(node.get("claims_code") or [])
    frontmatter = (
        f"---\n"
        f"node_id: {rule_id}\n"
        f"node_kind: rule\n"
        f"definition_status: llm_drafted\n"
        f"last_reviewed: {today}\n"
        f"last_reviewed_against_hash: {node.get('structural_hash')}\n"
        f"fan_out: {fan_out}\n"
        f"---\n\n"
        f"# {title}\n\n"
    )
    dossier_path = _rule_dossier_path(ctx, rule_id)
    dossier_path.parent.mkdir(parents=True, exist_ok=True)
    dossier_path.write_text(frontmatter + body + "\n")
    # Bump the JSON node's definition_status too — keeps node + dossier in sync
    node["definition_status"] = "llm_drafted"
    node_path.write_text(json.dumps(node, indent=2) + "\n")
    print(f"wrote {dossier_path.relative_to(ctx.LOGIGRAPH)}")
    print(f"updated {node_path.relative_to(ctx.LOGIGRAPH)} → definition_status: llm_drafted")
    print("next: review the dossier, then `bin/logigraph rule-bump '{0}'`".format(rule_id))
    return 0


def cmd_rule_bump(args: argparse.Namespace, ctx: Context) -> int:
    """Promote a rule's definition_status (default: → human_reviewed). Updates
    both the JSON node and the dossier frontmatter."""
    rule_id = args.id
    node_path = _rule_node_path(ctx, rule_id)
    if not node_path.exists():
        print(f"no rule node: {node_path.relative_to(ctx.LOGIGRAPH)}", file=sys.stderr)
        return 1
    node = json.loads(node_path.read_text())
    new_status = args.status
    node["definition_status"] = new_status
    node_path.write_text(json.dumps(node, indent=2) + "\n")
    print(f"bumped {node_path.relative_to(ctx.LOGIGRAPH)} → definition_status: {new_status}")

    dossier_path = _rule_dossier_path(ctx, rule_id)
    actor = args.actor or default_actor()
    paths = [node_path]
    if dossier_path.exists():
        rewrite_dossier_frontmatter(dossier_path, node.get("structural_hash", ""), new_status, actor)
        print(f"updated {dossier_path.relative_to(ctx.LOGIGRAPH)} frontmatter")
        paths.append(dossier_path)

    prefix = "review" if new_status == "human_reviewed" else "chore(bump)"
    git_commit_if_changed(ctx, paths, f"{prefix}: {rule_id}")
    return 0


def cmd_rule_stub(args: argparse.Namespace, ctx: Context) -> int:
    """Materialize a stub rule node from a one-line statement. Optionally
    seed claims_code from --claim flags. Use this to capture rule
    candidates before authoring the full dossier."""
    rule_id = args.id
    if not rule_id.startswith("rule::"):
        print(f"id must start with rule:: — got {rule_id}", file=sys.stderr)
        return 1
    node_path = _rule_node_path(ctx, rule_id)
    if node_path.exists() and not args.force:
        print(f"node already exists: {node_path.relative_to(ctx.LOGIGRAPH)}; pass --force to overwrite", file=sys.stderr)
        return 1
    title = args.title or rule_id.split("::", 2)[2].replace("_", " ").capitalize()
    statement = args.statement or "TODO: one-sentence rule statement"
    claims = []
    for c in args.claim or []:
        # format: "<role>:<depgraph_id>[|<where>]"
        if ":" not in c:
            print(f"--claim format is '<role>:<depgraph_id>[|<where>]' (got: {c})", file=sys.stderr)
            return 1
        role, rest = c.split(":", 1)
        if "|" in rest:
            dg_id, where = rest.split("|", 1)
        else:
            dg_id, where = rest, ""
        claims.append({
            "depgraph_id": dg_id.strip(),
            "role": role.strip(),
            "where": where.strip(),
            "confidence": "medium",
            "remote_hash": "",
            "stale": False,
        })
    domain_refs = args.domain_ref or ["resource::project::TODO"]
    import hashlib as _h
    structural_hash = _h.sha256(rule_id.encode()).hexdigest()
    node = {
        "schema_version": 2,
        "id": rule_id,
        "kind": "rule",
        "title": title,
        "statement": statement,
        "references_domain": domain_refs,
        "claims_code": claims,
        "fan_out": len(claims),
        "confidence": args.confidence,
        "source": args.source or "",
        "definition_status": "stub",
        "structural_hash": structural_hash,
        "dossier": _rule_dossier_rel(rule_id),
    }
    node_path.parent.mkdir(parents=True, exist_ok=True)
    node_path.write_text(json.dumps(node, indent=2) + "\n")
    print(f"wrote {node_path.relative_to(ctx.LOGIGRAPH)}")
    print(f"status: stub — next: bin/logigraph rule-draft '{rule_id}'")
    return 0


# ---------------------------------------------------------------------------
# Subparser registration
# ---------------------------------------------------------------------------

def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p_rr = sub.add_parser("rule-rank", help="List rule nodes by status (stub > llm_drafted > human_reviewed)")
    p_rr.add_argument("--status", choices=["stub", "llm_drafted", "human_reviewed"], help="Filter by status")
    p_rr.set_defaults(func=cmd_rule_rank)

    p_rs = sub.add_parser("rule-stub", help="Materialize a rule candidate as a stub JSON node")
    p_rs.add_argument("id", help="rule::category::short_name")
    p_rs.add_argument("--title")
    p_rs.add_argument("--statement", help="One-sentence rule statement")
    p_rs.add_argument("--domain-ref", action="append", help="Domain entity id (repeat for multiple)")
    p_rs.add_argument("--claim", action="append", help="Format: <role>:<depgraph_id>[|<where>]; repeat for multiple")
    p_rs.add_argument("--confidence", choices=["high", "medium", "low"], default="medium")
    p_rs.add_argument("--source", help="Free-text origin (commit hash, incident, decision)")
    p_rs.add_argument("--force", action="store_true", help="Overwrite existing node")
    p_rs.set_defaults(func=cmd_rule_stub)

    p_rd = sub.add_parser("rule-draft", help="Emit an LLM-drafting context bundle for one rule")
    p_rd.add_argument("id")
    p_rd.set_defaults(func=cmd_rule_draft)

    p_rf = sub.add_parser("rule-finalize", help="Save an LLM-drafted rule dossier body to canonical path")
    p_rf.add_argument("id")
    p_rf.add_argument("body_file", help="Path to dossier body markdown (no frontmatter)")
    p_rf.set_defaults(func=cmd_rule_finalize)

    p_rb = sub.add_parser("rule-bump", help="Promote a rule's definition_status (default → human_reviewed)")
    p_rb.add_argument("id")
    p_rb.add_argument("--status", default="human_reviewed", choices=["stub", "llm_drafted", "human_reviewed"])
    p_rb.add_argument("--actor", default=None, help="Reviewer (default: git config user.name)")
    p_rb.set_defaults(func=cmd_rule_bump)
