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


# Map confidence value -> (category-key, display-label). Issue #53 Option A
# replaced the previous-collapsed `unresolved` bucket with these specific
# values; the category breakdown now reads directly off the edge's
# confidence field instead of re-deriving from the target prefix.
_CONFIDENCE_CATEGORIES: tuple[tuple[str, str], ...] = (
    ("external", "external library (deliberately not indexed)"),
    ("unresolved_internal", "missed in-corpus (resolver gap — bug indicator)"),
    ("unresolved_receiver", "typed-receiver method call (see #51)"),
    ("dynamic", "dynamic (getattr / computed callee)"),
)
# Confidence values that count as "unresolved" for the purposes of the
# category breakdown / unresolved-prefixes worklist. `external` is
# expected and shown; the rest are the gap-shaped buckets.
_NON_EXACT_CONFIDENCES: frozenset[str] = frozenset(
    name for name, _ in _CONFIDENCE_CATEGORIES
)


def _group_key_for_target(target: str) -> str:
    """Collapse similar targets to a shared prefix for the worklist view.

    `external::npm::<pkg>::Foo`, `external::npm::<pkg>::Bar` → both share
    the `external::npm::<pkg>` group. `external::unresolved::db.query` stays
    as-is (it's already the natural group). `external::dynamic::<shape>::
    <callsite>` collapses to `external::dynamic::<shape>` so the per-shape
    count is the legible signal (each callsite is unique by construction —
    #90)."""
    parts = target.split("::")
    if target.startswith("external::npm::") or target.startswith("external::pypi::"):
        return "::".join(parts[:3])
    if target.startswith("external::dynamic::"):
        return "::".join(parts[:3])
    return target


def _render_resolver_stats(ctx: Context) -> None:
    """Read `_meta.json::resolver_stats` and print a small per-resolver
    table — one row per resolver branch with hit / fuzzy / fallthrough
    counts and the resulting hit rate.

    Surface for R7 (issue #77): each resolver branch in the Python and TS
    extractors ticks an outcome counter; regen.py merges them under this
    key. The table answers "the imports-table fallback I added (#68/#69) —
    how often does it hit vs miss?".

    Silently no-op when the key is missing so older corpora keep rendering
    cleanly. Also no-op on JSON parse errors — the corpus rollup above us
    is the load-bearing report; resolver stats are an observational extra.
    """
    meta_path = ctx.CORPUS_META
    if not meta_path.exists():
        return
    try:
        meta = json.loads(meta_path.read_text())
    except (OSError, json.JSONDecodeError):
        return
    resolver_stats = meta.get("resolver_stats")
    if not resolver_stats:
        return

    print()
    print("## Resolver stats (R7)")
    # Column header: resolver name, hit / fuzzy / fallthrough, total, hit %.
    print(f"  {'resolver':<46} {'hit':>6} {'fuzzy':>6} {'fall':>6} {'total':>6} {'hit%':>5}")
    for resolver in sorted(resolver_stats):
        outcomes = resolver_stats[resolver] or {}
        hit = int(outcomes.get("hit", 0))
        fuzzy = int(outcomes.get("fuzzy", 0))
        fall = int(outcomes.get("fallthrough", 0))
        total = hit + fuzzy + fall
        # Surface any unexpected outcome keys instead of silently dropping
        # — same convention as the confidence histogram above.
        extra = sum(int(v) for k, v in outcomes.items()
                    if k not in {"hit", "fuzzy", "fallthrough"})
        total += extra
        pct = int(round(100 * hit / total)) if total else 0
        print(f"  {resolver:<46} {hit:>6} {fuzzy:>6} {fall:>6} {total:>6} {pct:>4}%")


def cmd_stats(args: argparse.Namespace, ctx: Context) -> int:
    """Corpus rollup + optional telemetry. Mirrors `logigraph stats`."""
    # ---- corpus rollup --------------------------------------------------
    by_kind_tier_state: dict[str, dict[str, dict[str, int]]] = {}
    total = 0
    confidence_counts: dict[str, int] = {}
    # confidence -> group_key -> count
    by_confidence_buckets: dict[str, dict[str, int]] = {}
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
            if conf in _NON_EXACT_CONFIDENCES:
                group = _group_key_for_target(edge.get("target") or "")
                buckets = by_confidence_buckets.setdefault(conf, {})
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
        # Canonical print order: exact, fuzzy, then the four
        # previously-unresolved sub-buckets.
        canonical_order = ("exact", "fuzzy") + tuple(c for c, _ in _CONFIDENCE_CATEGORIES)
        for conf in canonical_order:
            n = confidence_counts.get(conf, 0)
            print(f"  {conf:<22} {n:>7}")
        # surface any unexpected confidence values rather than silently dropping them
        for conf in sorted(c for c in confidence_counts if c not in canonical_order):
            print(f"  {conf:<22} {confidence_counts[conf]:>7}")
        print(f"  {'total':<22} {total_edges:>7}")

        unresolved_total = sum(
            confidence_counts.get(c, 0)
            for c, _ in _CONFIDENCE_CATEGORIES
            if c != "external"
        )
        # Show the category breakdown whenever any non-`exact`/`fuzzy`
        # bucket is populated — the breakdown is what makes the histogram
        # actionable.
        if any(confidence_counts.get(c, 0) for c, _ in _CONFIDENCE_CATEGORIES):
            print()
            print("## Edges by confidence category")
            for cat, label in _CONFIDENCE_CATEGORIES:
                buckets = by_confidence_buckets.get(cat)
                if not buckets:
                    continue
                n = sum(buckets.values())
                print(f"  {n:>6}  {label}")

            # Head of "gap-shaped" target groups (everything except
            # `external`, which is expected and not a worklist item).
            gap_groups = [
                (g, n)
                for cat, buckets in by_confidence_buckets.items()
                if cat != "external"
                for g, n in buckets.items()
            ]
            gap_groups.sort(key=lambda kv: -kv[1])
            head = gap_groups[: args.unresolved_top]
            if head:
                print()
                print(f"## Top gap-target prefixes (top {len(head)})")
                for group, n in head:
                    print(f"  {n:>6}  {group}")

    # Per-resolver hit-rate table (R7, #77). Populated by `kg depgraph regen`
    # — see resolver_stats key in nodes/_meta.json. Skipped silently when the
    # key is absent so older corpora keep rendering cleanly.
    _render_resolver_stats(ctx)

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
        help="Include edge confidence histogram + per-bucket worklist "
             "(external library vs unresolved_internal vs unresolved_receiver vs dynamic). "
             "Replaces the pre-#53 unresolved-by-category breakdown.",
    )
    p.add_argument(
        "--unresolved-top",
        type=int,
        default=15,
        metavar="N",
        help="When --edges is set, show the top N gap-target prefixes "
             "(non-`external` buckets) (default: 15)",
    )
    p.set_defaults(func=cmd_stats)
