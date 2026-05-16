"""logigraph context subcommand — print rule/domain blocks applicable to a target.

The subcommand name is ``context``; the module name uses the ``_cmd`` suffix to
avoid shadowing the ``context.py`` module that exports the Context dataclass.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .context import Context
from ._shared import find_rules_for_target, load_all_nodes


def cmd_context(args: argparse.Namespace, ctx: Context) -> int:
    nodes = load_all_nodes(ctx)
    rule_ids = find_rules_for_target(ctx, args.target)
    if not rule_ids:
        print(f"no rules apply to: {args.target}")
        return 0
    for rid in rule_ids:
        if rid not in nodes:
            print(f"WARN: index points to missing rule {rid}", file=sys.stderr)
            continue
        path, data = nodes[rid]
        if data.get("flagged"):
            reason = data.get("flagged_reason") or "(no reason recorded)"
            flagger = data.get("flagged_by") or "(unknown)"
            flag_date = data.get("flagged_at") or ""
            print("⚠ FLAGGED — this rule documents a known deficiency, not an invariant to preserve.")
            meta = f"  Flagged by: {flagger}"
            if flag_date:
                meta += f" · {flag_date}"
            print(meta)
            print(f"  Reason: {reason}")
            print("  When touching affected code: surface alternatives; do NOT pattern-match")
            print("  the current state as desired. The rule's claims describe what exists,")
            print("  not what should exist.")
            print()
        print(f"# {data.get('title', rid)}")
        print(f"id: {rid}  ·  fan_out: {data.get('fan_out') or len(data.get('claims_code') or [])}")
        print(f"statement: {data.get('statement', '')}")
        print()
        for ref in data.get("references_domain", []):
            ont = nodes.get(ref, (None, {}))[1]
            summary = ont.get("summary", "")
            if summary:
                print(f"  · {ref}: {summary}")
        print()
        dossier_rel = data.get("dossier")
        if dossier_rel and (ctx.LOGIGRAPH / dossier_rel).exists():
            print((ctx.LOGIGRAPH / dossier_rel).read_text())
        else:
            print("_no dossier_")
        print()

    # --- Entity rollups -------------------------------------------------------
    # Collect the union of domain refs across the applicable rules; emit a
    # rollup summary block per entity. Spec § "CLI surface / context": inline
    # by default, summary mode (top 3 per kind).
    entity_ids: list[str] = []
    seen_entity: set[str] = set()
    for rid in rule_ids:
        if rid not in nodes:
            continue
        _, rdata = nodes[rid]
        for ref in rdata.get("references_domain", []):
            if ref not in seen_entity and ref in nodes:
                entity_ids.append(ref)
                seen_entity.add(ref)

    if entity_ids:
        try:
            from depgraph.lib.rollup import (  # noqa: PLC0415 (deferred cross-graph import)
                compute_rollup,
                format_rollup_text,
                load_rollup_inputs,
                resolve_anchor,
            )
        except ImportError as e:
            print(f"# (rollups skipped: {e})")
            return 0

        try:
            inputs = load_rollup_inputs(ctx.depgraph_dir)
        except FileNotFoundError as e:
            # Reverse-dependents index missing — surface once, then skip.
            print(f"# (rollups skipped: {e})")
            return 0
        logigraph_index = {nid: data for nid, (_, data) in nodes.items()}
        for eid in entity_ids:
            _, edata = nodes[eid]
            anchor = resolve_anchor(edata, inputs.depgraph_index, logigraph_index=logigraph_index)
            rollup = compute_rollup(
                anchor_id=anchor.model_id or "",
                depgraph_index=inputs.depgraph_index,
                dependents_index=inputs.dependents_index,
                depth=3,
                anchor_result=anchor,
            )
            print(f"─ Rollup for {eid}")
            print(format_rollup_text(rollup, summary=True))
            print()

    return 0


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("context")
    p.add_argument("target")
    p.set_defaults(func=cmd_context)
