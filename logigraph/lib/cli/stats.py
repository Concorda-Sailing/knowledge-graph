"""logigraph stats subcommand — corpus rollup + optional telemetry."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .context import Context
from ._shared import load_all_nodes


def _load_telemetry_events(path: Path, since_hours: int | None = None) -> list[dict]:
    """Read a JSONL log; if since_hours is given, filter to events newer
    than that. Returns an empty list if the file is missing or unreadable."""
    if not path.exists():
        return []
    import datetime as _dt
    cutoff = None
    if since_hours is not None:
        cutoff = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(hours=since_hours)
    out: list[dict] = []
    try:
        with path.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if cutoff is not None:
                    ts_str = ev.get("ts", "")
                    try:
                        ts = _dt.datetime.fromisoformat(ts_str)
                    except ValueError:
                        continue
                    if ts < cutoff:
                        continue
                out.append(ev)
    except OSError:
        return []
    return out


def cmd_stats(args: argparse.Namespace, ctx: Context) -> int:
    """Curation backlog + (optional) telemetry rollup. Designed to fit in
    ~30 lines of output for typical state — eyeballable, not dashboard."""
    injections_log = ctx.TELEMETRY_DIR / "injections.jsonl"
    acks_log = ctx.TELEMETRY_DIR / "acknowledgments.jsonl"

    nodes = load_all_nodes(ctx)
    rules = [(nid, data) for nid, (_, data) in nodes.items() if data.get("kind") == "rule"]
    domain_nodes = [(nid, data) for nid, (_, data) in nodes.items() if data.get("kind") == "domain"]

    # Definition_status breakdown.
    by_kind: dict[str, dict[str, int]] = {}
    for nid, (_, data) in nodes.items():
        kind = data.get("kind", "?")
        by_kind.setdefault(kind, {"stub": 0, "llm_drafted": 0, "human_reviewed": 0, "missing": 0, "other": 0})
        st = data.get("definition_status")
        bucket = st if st in ("stub", "llm_drafted", "human_reviewed") else ("missing" if st is None else "other")
        by_kind[kind][bucket] += 1

    # Stale claims — read directly from rule claims to avoid recomputing.
    stale_claims = sum(
        1
        for _nid, data in rules
        for c in data.get("claims_code", [])
        if c.get("stale")
    )
    total_claims = sum(len(data.get("claims_code", [])) for _nid, data in rules)

    print("# Logigraph stats")
    print()
    print(f"  rules:      {len(rules)}")
    print(f"  domain:     {len(domain_nodes)}")
    print(f"  claims:     {total_claims}  (stale: {stale_claims})")
    print()
    print("## Definition status")
    for kind, kc in sorted(by_kind.items()):
        breakdown = ", ".join(f"{st}={n}" for st, n in kc.items() if n)
        print(f"  {kind:<10} {breakdown}")

    if args.telemetry:
        injections = _load_telemetry_events(injections_log)
        acks = _load_telemetry_events(acks_log)
        recent_injections = _load_telemetry_events(injections_log, since_hours=24 * 7)
        recent_acks = _load_telemetry_events(acks_log, since_hours=24 * 7)

        print()
        print("## Telemetry (all-time)")
        print(f"  total injections:        {len(injections)}")
        print(f"  total acknowledgments:   {len(acks)}")
        print()
        print("## Telemetry (last 7 days)")
        print(f"  injections:              {len(recent_injections)}")
        print(f"  acknowledgments:         {len(recent_acks)}")

        # Per-rule breakdown.
        rule_inj: dict[str, int] = {}
        rule_ack: dict[str, int] = {}
        for ev in injections:
            rid = ev.get("rule_id")
            if rid:
                rule_inj[rid] = rule_inj.get(rid, 0) + 1
        for ev in acks:
            rid = ev.get("rule_id")
            if rid:
                rule_ack[rid] = rule_ack.get(rid, 0) + 1

        if rule_inj:
            print()
            print("## Top-injected rules (all-time, with ack rate)")
            ranked = sorted(rule_inj.items(), key=lambda kv: -kv[1])[:10]
            print(f"  {'inj':>5}  {'ack':>5}  {'rate':>5}  rule")
            print(f"  {'-'*5}  {'-'*5}  {'-'*5}  {'-'*40}")
            for rid, inj_n in ranked:
                ack_n = rule_ack.get(rid, 0)
                rate = (ack_n / inj_n) if inj_n > 0 else 0.0
                print(f"  {inj_n:>5}  {ack_n:>5}  {rate*100:>4.0f}%  {rid}")

            # Highlight low-ack-rate rules — candidates for prose rework.
            low_ack = [(rid, inj_n, rule_ack.get(rid, 0)) for rid, inj_n in rule_inj.items()
                       if inj_n >= 3 and (rule_ack.get(rid, 0) / inj_n) < 0.3]
            if low_ack:
                print()
                print("## Low ack rate — candidates for prose rework")
                for rid, inj_n, ack_n in sorted(low_ack, key=lambda x: -x[1]):
                    print(f"  {rid}: {inj_n} injected, {ack_n} acknowledged")

    return 0


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("stats", help="Curation backlog + optional telemetry rollup")
    p.add_argument(
        "--telemetry",
        action="store_true",
        help="Include injection/acknowledgment metrics from telemetry/",
    )
    p.set_defaults(func=cmd_stats)
