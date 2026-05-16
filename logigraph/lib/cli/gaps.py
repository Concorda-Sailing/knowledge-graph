"""logigraph gaps subcommand — orphan rules / orphan domain refs / stale claims."""
from __future__ import annotations

import argparse

from .context import Context
from ._shared import load_all_nodes, load_depgraph_corpus


def cmd_gaps(args: argparse.Namespace, ctx: Context) -> int:
    nodes = load_all_nodes(ctx)
    domain_ids = {nid for nid, (_, d) in nodes.items() if d.get("kind") == "domain"}
    depgraph_corpus = load_depgraph_corpus(ctx)
    depgraph_ids = set(depgraph_corpus.keys())

    orphan_claims: list[tuple[str, str]] = []
    orphan_domain_refs: list[tuple[str, str]] = []
    stale_claims: list[tuple[str, str]] = []

    for nid, (_, data) in nodes.items():
        if data.get("kind") != "rule":
            continue
        for ref in data.get("references_domain", []):
            if ref not in domain_ids:
                orphan_domain_refs.append((nid, ref))
        for claim in data.get("claims_code", []):
            cid = claim.get("depgraph_id")
            if cid not in depgraph_ids:
                orphan_claims.append((nid, cid))
                continue
            remote = claim.get("remote_hash")
            current = depgraph_corpus[cid].get("structural_hash")
            if remote and current and remote != current:
                stale_claims.append((nid, cid))

    if orphan_claims:
        print(f"ORPHAN CLAIMS ({len(orphan_claims)}):")
        for rule_id, claim_id in orphan_claims:
            print(f"  {rule_id} → {claim_id}")
    if orphan_domain_refs:
        print(f"ORPHAN DOMAIN REFS ({len(orphan_domain_refs)}):")
        for rule_id, ref in orphan_domain_refs:
            print(f"  {rule_id} → {ref}")
    if stale_claims:
        print(f"STALE CLAIMS ({len(stale_claims)}):")
        for rule_id, claim_id in stale_claims:
            print(f"  {rule_id} → {claim_id}")

    total = len(orphan_claims) + len(orphan_domain_refs) + len(stale_claims)
    if total == 0:
        print("no gaps")
        return 0
    return 1


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("gaps")
    p.set_defaults(func=cmd_gaps)
