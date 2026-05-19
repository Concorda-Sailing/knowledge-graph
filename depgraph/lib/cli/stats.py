"""depgraph stats subcommand handler.

Corpus coverage rollup (kind/tier/state) and optional telemetry summary
(last-7d + all-time injection/acknowledgment rollup).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .context import Context
from ._shared import load_dependents_index, load_telemetry_events


_UNRESOLVED_CATEGORIES = (
    ("external_library", "external library (deliberately not indexed)"),
    ("missed_internal", "missed in-corpus (resolver gap — bug indicator)"),
    ("typed_receiver", "typed-receiver method call (see #51)"),
    ("dynamic_or_other", "dynamic / other"),
    ("other", "other"),
)


def _categorize_unresolved(target: str) -> tuple[str, str]:
    """Bucket an unresolved edge target for resolver-priority triage.

    Returns ``(category, group_key)`` where ``category`` is one of the keys in
    ``_UNRESOLVED_CATEGORIES`` and ``group_key`` is the prefix used to collapse
    similar targets (e.g. all ``external::npm::react::*`` symbols share the
    ``external::npm::react`` group).
    """
    parts = target.split("::")
    if (target.startswith("external::npm::unknown")
            or target.startswith("external::pypi::unknown")):
        return ("missed_internal", "::".join(parts[:3]))
    if target.startswith("external::npm::") or target.startswith("external::pypi::"):
        return ("external_library", "::".join(parts[:3]))
    if target.startswith("external::unresolved::"):
        rest = "::".join(parts[2:])
        if "." in rest:
            return ("typed_receiver", target)
        return ("dynamic_or_other", target)
    return ("other", target)


def cmd_stats(args: argparse.Namespace, ctx: Context) -> int:
    """Corpus rollup + optional telemetry. Mirrors `logigraph stats`."""
    # ---- corpus rollup --------------------------------------------------
    by_kind_tier_state: dict[str, dict[str, dict[str, int]]] = {}
    total = 0
    confidence_counts: dict[str, int] = {}
    # category -> group_key -> count
    unresolved_by_category: dict[str, dict[str, int]] = {}
    dependents = load_dependents_index(ctx)
    for nf in ctx.NODES.rglob("*.json"):
        if nf.name.startswith("_"):
            continue
        if any(p.startswith("_") for p in nf.relative_to(ctx.NODES).parts):
            continue
        try:
            d = json.loads(nf.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        nid = d.get("id")
        if not nid:
            continue
        kind = d.get("kind", "?")
        fan_out = len(dependents.get(nid) or [])
        tier = "A" if fan_out >= 10 else "B" if fan_out >= 3 else "C"
        for edge in d.get("edges_out") or []:
            conf = edge.get("confidence") or "?"
            confidence_counts[conf] = confidence_counts.get(conf, 0) + 1
            if conf == "unresolved":
                cat, group = _categorize_unresolved(edge.get("target") or "")
                buckets = unresolved_by_category.setdefault(cat, {})
                buckets[group] = buckets.get(group, 0) + 1
        # Compute dossier state inline (avoid importing the FastAPI loader).
        rel = d.get("dossier")
        if not rel:
            state = "missing"
        else:
            dp = ctx.DEPGRAPH / rel
            if not dp.exists():
                state = "missing"
            else:
                state = "current"
                text = dp.read_text()
                if text.startswith("---"):
                    try:
                        end = text.index("\n---\n", 4)
                        for line in text[4:end].splitlines():
                            s = line.strip()
                            if s.startswith("status:"):
                                v = s.split(":", 1)[1].strip()
                                if v in ("llm_drafted", "unreviewed"):
                                    state = v
                                break
                    except ValueError:
                        pass
        by_kind_tier_state.setdefault(kind, {}).setdefault(tier, {}).setdefault(state, 0)
        by_kind_tier_state[kind][tier][state] += 1
        total += 1

    print("# Depgraph stats")
    print()
    print(f"  total nodes: {total}")
    print()
    print("## Coverage (current+llm_drafted / total) by kind+tier")
    print(f"  {'kind':<11} {'tier':<5} {'%':>5} {'total':>6} {'cur':>5} {'llm':>5} {'unr':>5} {'miss':>5}")
    for kind in sorted(by_kind_tier_state):
        for tier in ("A", "B", "C"):
            buckets = by_kind_tier_state[kind].get(tier)
            if not buckets:
                continue
            t = sum(buckets.values())
            cur = buckets.get("current", 0)
            llm = buckets.get("llm_drafted", 0)
            unr = buckets.get("unreviewed", 0)
            miss = buckets.get("missing", 0)
            pct = int(round(100 * (cur + llm) / t)) if t else 0
            print(f"  {kind:<11} {tier:<5} {pct:>4}% {t:>6} {cur:>5} {llm:>5} {unr:>5} {miss:>5}")

    if args.edges:
        total_edges = sum(confidence_counts.values())
        print()
        print("## Edges by confidence")
        for conf in ("exact", "fuzzy", "unresolved"):
            n = confidence_counts.get(conf, 0)
            print(f"  {conf:<11} {n:>7}")
        # surface any unexpected confidence values rather than silently dropping them
        for conf in sorted(c for c in confidence_counts if c not in ("exact", "fuzzy", "unresolved")):
            print(f"  {conf:<11} {confidence_counts[conf]:>7}")
        print(f"  {'total':<11} {total_edges:>7}")

        unresolved_total = confidence_counts.get("unresolved", 0)
        if unresolved_total:
            print()
            print("## Unresolved edges by category")
            for cat, label in _UNRESOLVED_CATEGORIES:
                buckets = unresolved_by_category.get(cat)
                if not buckets:
                    continue
                n = sum(buckets.values())
                print(f"  {n:>6}  {label}")

            # head of unresolved targets so the report doubles as a worklist
            all_groups = [(g, n) for buckets in unresolved_by_category.values()
                          for g, n in buckets.items()]
            all_groups.sort(key=lambda kv: -kv[1])
            head = all_groups[: args.unresolved_top]
            if head:
                print()
                print(f"## Top unresolved prefixes (top {len(head)})")
                for group, n in head:
                    print(f"  {n:>6}  {group}")

    if args.telemetry:
        injections = load_telemetry_events(ctx.INJECTIONS_LOG)
        acks = load_telemetry_events(ctx.ACKS_LOG)
        recent_injections = load_telemetry_events(ctx.INJECTIONS_LOG, since_hours=24 * 7)
        recent_acks = load_telemetry_events(ctx.ACKS_LOG, since_hours=24 * 7)

        print()
        print("## Telemetry (all-time)")
        print(f"  total injections:        {len(injections)}")
        print(f"  total acknowledgments:   {len(acks)}")
        print()
        print("## Telemetry (last 7 days)")
        print(f"  injections:              {len(recent_injections)}")
        print(f"  acknowledgments:         {len(recent_acks)}")

        node_inj: dict[str, int] = {}
        node_ack: dict[str, int] = {}
        for ev in injections:
            nid = ev.get("node_id")
            if nid:
                node_inj[nid] = node_inj.get(nid, 0) + 1
        for ev in acks:
            nid = ev.get("node_id")
            if nid:
                node_ack[nid] = node_ack.get(nid, 0) + 1

        if node_inj:
            print()
            print("## Top-injected nodes (all-time, with ack rate)")
            ranked = sorted(node_inj.items(), key=lambda kv: -kv[1])[:10]
            print(f"  {'inj':>5}  {'ack':>5}  {'rate':>5}  node")
            print(f"  {'-'*5}  {'-'*5}  {'-'*5}  {'-'*60}")
            for nid, inj_n in ranked:
                ack_n = node_ack.get(nid, 0)
                rate = (ack_n / inj_n) if inj_n > 0 else 0.0
                print(f"  {inj_n:>5}  {ack_n:>5}  {rate*100:>4.0f}%  {nid}")

            low_ack = [(nid, inj_n, node_ack.get(nid, 0))
                       for nid, inj_n in node_inj.items()
                       if inj_n >= 3 and (node_ack.get(nid, 0) / inj_n) < 0.3]
            if low_ack:
                print()
                print("## Low ack rate — candidates for dossier rework")
                for nid, inj_n, ack_n in sorted(low_ack, key=lambda x: -x[1])[:10]:
                    print(f"  {nid}: {inj_n} injected, {ack_n} acknowledged")

    return 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "stats",
        help="Corpus coverage + (optional) telemetry rollup",
    )
    p.add_argument(
        "--telemetry",
        action="store_true",
        help="Include last-7d and all-time injection/acknowledgment rollup",
    )
    p.add_argument(
        "--edges",
        action="store_true",
        help="Include edge confidence histogram + unresolved-edge categorization "
             "(external library vs missed in-corpus vs typed-receiver vs dynamic)",
    )
    p.add_argument(
        "--unresolved-top",
        type=int,
        default=15,
        metavar="N",
        help="When --edges is set, show the top N unresolved prefixes (default: 15)",
    )
    p.set_defaults(func=cmd_stats)
