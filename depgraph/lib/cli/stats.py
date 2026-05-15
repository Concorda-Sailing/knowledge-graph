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


def cmd_stats(args: argparse.Namespace, ctx: Context) -> int:
    """Corpus rollup + optional telemetry. Mirrors `logigraph stats`."""
    # ---- corpus rollup --------------------------------------------------
    by_kind_tier_state: dict[str, dict[str, dict[str, int]]] = {}
    total = 0
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
    p.set_defaults(func=cmd_stats)
