"""logigraph health subcommand — composite check (validate + gaps + curation backlog)."""
from __future__ import annotations

import argparse
import sys

from .context import Context
from ._shared import load_all_nodes, load_depgraph_corpus, validate_json_schema


def cmd_health(args: argparse.Namespace, ctx: Context) -> int:
    """Compact graph-health summary: validate + gaps + curation-backlog
    counts in one block. Exit non-zero if anything is wrong. Used by the
    SessionStart hook for at-a-glance freshness."""
    domain_schema = ctx.tool_root / "schema" / "domain.schema.json"
    rule_schema = ctx.tool_root / "schema" / "rule.schema.json"
    process_schema = ctx.tool_root / "schema" / "process.schema.json"

    problems: list[str] = []
    summary: list[str] = []

    nodes = load_all_nodes(ctx)

    # ---- validate ------------------------------------------------------
    invalid = 0
    for nid, (path, data) in nodes.items():
        kind = data.get("kind")
        if kind == "domain":
            schema_path = domain_schema
        elif kind == "rule":
            schema_path = rule_schema
        elif kind == "process":
            schema_path = process_schema
        else:
            continue
        if validate_json_schema(data, schema_path):
            invalid += 1
    if invalid:
        problems.append(f"{invalid} invalid node(s) — run `logigraph validate`")

    # ---- gaps (orphans + stale) ----------------------------------------
    domain_ids = {nid for nid, (_, d) in nodes.items() if d.get("kind") == "domain"}
    depgraph_corpus = load_depgraph_corpus(ctx)
    depgraph_ids = set(depgraph_corpus.keys())

    orphan_claims = 0
    orphan_refs = 0
    stale_claims = 0

    def _check_claim(claim: dict) -> tuple[bool, bool]:
        cid = claim.get("depgraph_id")
        if cid not in depgraph_ids:
            return (True, False)
        remote = claim.get("remote_hash")
        current = depgraph_corpus[cid].get("structural_hash")
        if remote and current and remote != current:
            return (False, True)
        return (False, False)

    for nid, (_, data) in nodes.items():
        kind = data.get("kind")
        if kind == "rule":
            for ref in data.get("references_domain", []):
                if ref not in domain_ids:
                    orphan_refs += 1
            for claim in data.get("claims_code", []):
                orph, st = _check_claim(claim)
                orphan_claims += int(orph)
                stale_claims += int(st)
        elif kind == "process":
            for step in data.get("steps", []):
                for claim in step.get("claims_code", []):
                    orph, st = _check_claim(claim)
                    orphan_claims += int(orph)
                    stale_claims += int(st)
            for surface in data.get("ui_surfaces", []):
                orph, st = _check_claim(surface)
                orphan_claims += int(orph)
                stale_claims += int(st)
    if orphan_claims:
        problems.append(f"{orphan_claims} orphan claim(s) (rule claims missing depgraph node) — run `logigraph gaps`")
    if orphan_refs:
        problems.append(f"{orphan_refs} orphan domain ref(s) — run `logigraph gaps`")
    if stale_claims:
        problems.append(f"{stale_claims} stale claim(s) (depgraph hash drifted) — run `logigraph gaps`")

    # ---- curation backlog ----------------------------------------------
    by_kind_status: dict[str, dict[str, int]] = {}
    for nid, (_, data) in nodes.items():
        k = data.get("kind", "?")
        s = data.get("definition_status", "?")
        by_kind_status.setdefault(k, {}).setdefault(s, 0)
        by_kind_status[k][s] += 1
    stub_rules = by_kind_status.get("rule", {}).get("stub", 0)
    llm_rules = by_kind_status.get("rule", {}).get("llm_drafted", 0)
    if stub_rules:
        problems.append(f"{stub_rules} rule(s) in stub status — run `logigraph rule-rank --status stub`")
    if llm_rules:
        problems.append(f"{llm_rules} rule(s) awaiting human review — run `logigraph rule-rank --status llm_drafted`")

    rules = by_kind_status.get("rule", {}).get("human_reviewed", 0)
    domain = by_kind_status.get("domain", {}).get("human_reviewed", 0)
    process = by_kind_status.get("process", {}).get("human_reviewed", 0)
    summary.append(f"reviewed: rules={rules} domain={domain} process={process}")

    # ---- output --------------------------------------------------------
    print("# Logigraph health")
    if problems:
        print()
        for p in problems:
            print(f"  ⚠ {p}")
    else:
        print()
        print("  ✓ clean")
    if summary:
        print()
        for s in summary:
            print(f"  {s}")
    return 1 if problems else 0


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser(
        "health",
        help="One-shot graph health summary (validate + gaps + curation backlog). Exit 1 if anything wrong.",
    )
    p.set_defaults(func=cmd_health)
