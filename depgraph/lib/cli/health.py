"""depgraph health subcommand handler.

Compact graph-health report. Bundles validate + orphans + stale-dossier
detection + tier-A coverage shortfall into one summary suitable for
SessionStart injection. Exits non-zero if anything is wrong.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .context import Context
from ._shared import is_dossier_eligible, load_dependents_index, dossier_state

# Make depgraph/lib/config.py importable.
_DEPGRAPH_LIB = Path(__file__).resolve().parents[1]
if str(_DEPGRAPH_LIB) not in sys.path:
    sys.path.insert(0, str(_DEPGRAPH_LIB))
from depgraph.lib.config import basename_path_map  # noqa: E402


def cmd_health(args: argparse.Namespace, ctx: Context) -> int:
    """Compact graph-health report. Bundles validate + orphans + stale-dossier
    detection + tier-A coverage shortfall into one summary suitable for
    SessionStart injection. Exits non-zero if anything is wrong."""
    # Liveness gate (#61): "no extraction has run" must not look like "clean."
    # _meta.json is the canonical "regen completed" signal; without it we
    # cannot distinguish a healthy empty corpus from one that was never
    # extracted, so refuse to claim clean.
    if not ctx.CORPUS_META.exists():
        print("# Depgraph health")
        print()
        print("  ⚠ no extraction has run yet — run `depgraph regen`")
        return 1

    problems: list[str] = []
    summary: list[str] = []

    # ---- single corpus walk (#70) ---------------------------------------
    # Health runs on every SessionStart hook; the previous implementation
    # walked ctx.NODES.rglob("*.json") four separate times and re-parsed
    # each node JSON on every pass, so cost scaled as 4 × corpus_size.
    # Collapse to one walk: parse each node once, then apply each pass's
    # filters and counters in turn.
    try:
        import jsonschema  # type: ignore[import-untyped]
        schema = json.loads((ctx.tool_root / "schema" / "node.schema.json").read_text())
        # Build the validator once: jsonschema.validate() re-runs check_schema
        # on every call, which dominates the corpus walk (84s of 88s on a
        # 6.8k-node corpus per cProfile). Constructing the validator up-front
        # checks the schema once.
        _validator_cls = jsonschema.validators.validator_for(schema)
        _validator_cls.check_schema(schema)
        validator = _validator_cls(schema)
        validate_enabled = True
    except ImportError:
        jsonschema = None  # type: ignore[assignment]
        schema = None
        validator = None  # type: ignore[assignment]
        validate_enabled = False
        summary.append("validate: skipped (jsonschema not installed)")

    # Coverage caveats are aggregated in the same corpus walk below; the
    # previous implementation did a separate rglob+parse pass for them.
    from depgraph.lib.coverage_caveats import (
        CAVEAT_REGISTRY,
        caveat_title,
    )
    caveat_counts: dict[str, int] = {}

    invalid = 0
    orphan_n = 0
    stale_n = 0
    drift_n = 0
    a_total = 0
    a_covered = 0
    basename_to_path = basename_path_map(ctx.DEPGRAPH)
    dependents = load_dependents_index(ctx)

    for node_file in ctx.NODES.rglob("*.json"):
        if node_file.name.startswith("_") or any(p.startswith("_") for p in node_file.parts):
            continue

        # Read+parse the file exactly once.
        try:
            raw = node_file.read_text()
        except OSError:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # An invalid JSON file fails the schema pass; the other three
            # passes (orphan/stale/tier-A) need a parsed dict and skip it.
            if validate_enabled:
                invalid += 1
            continue

        # Pass 1a: coverage caveats. Aggregated here (before any pass-
        # specific `continue`) so the histogram reflects every node, not
        # just tier-A-eligible ones. Previously this was a separate
        # rglob+parse pass; folding it in halved the parse work.
        for c in data.get("coverage_caveats") or []:
            caveat_counts[c] = caveat_counts.get(c, 0) + 1

        # Pass 1: schema validate.
        if validate_enabled:
            try:
                validator.validate(data)
            except jsonschema.ValidationError:
                invalid += 1

        # Pass 2: orphans (node points at missing source file).
        src = data.get("source") or {}
        repo, rel = src.get("repo"), src.get("path")
        if repo and rel:
            repo_path = basename_to_path.get(repo)
            if repo_path is not None and not (repo_path / rel).exists():
                orphan_n += 1

        # Compute dossier_state once per node — both pass 3 and pass 4
        # consult it, and walking the dossier file twice would defeat
        # half the savings from collapsing the corpus walk.
        d_state = dossier_state(data, ctx.DEPGRAPH)

        # Pass 3: stale dossiers (hash drift).
        if d_state == "stale":
            stale_n += 1

        # Pass 3b (#58): inbound-edge drift is an independent staleness
        # signal — the node's own source may be unchanged, but its
        # consumer set has shifted enough that the dossier's External
        # consumers / Dependencies prose is likely out of date. Surface
        # as a separate problem so the operator sees both axes.
        if data.get("inbound_drift"):
            drift_n += 1

        # Pass 4: tier-A coverage shortfall.
        nid = data.get("id")
        if not nid:
            continue
        if not is_dossier_eligible(data):
            continue
        if data.get("kind", "") == "test":
            continue
        fan_out = len(dependents.get(nid) or [])
        if fan_out < 10:
            continue
        a_total += 1
        if d_state == "current":
            a_covered += 1

    if invalid:
        problems.append(f"{invalid} invalid node(s) — run `depgraph validate`")
    if orphan_n:
        problems.append(f"{orphan_n} orphan node(s) (source file gone) — run `depgraph orphans`")
    if stale_n:
        problems.append(f"{stale_n} stale dossier(s) (structural_hash drifted) — run `depgraph dossier-rank --only-stale`")
    if drift_n:
        problems.append(f"{drift_n} dossier(s) with consumer-set drift — run `depgraph dossier-rank --only-drifted`")
    a_pct = int(round(100 * a_covered / a_total)) if a_total else 100
    if a_pct < 80 and a_total > 0:
        problems.append(f"Tier-A dossier coverage at {a_pct}% ({a_covered}/{a_total}) — run `depgraph dossier-rank --tier A`")
    else:
        summary.append(f"tier-A coverage: {a_pct}% ({a_covered}/{a_total})")

    # ---- coverage caveats (corpus-wide blind-spot histogram) -------------
    # Per #55: surface the "what is this graph blind to, at corpus scale?"
    # view. Counts are informational — not a problem to be fixed (extractor
    # coverage gaps aren't graph-health bugs), but visible signal so the
    # operator knows where investment in extractors would pay off.
    # `caveat_counts` is populated in the single walk above.
    if caveat_counts:
        summary.append("coverage caveats stamped:")
        for c in sorted(caveat_counts, key=lambda k: -caveat_counts[k]):
            summary.append(f"  {caveat_counts[c]:>5}  {c} ({caveat_title(c)})")
    # Registry entries with zero corpus coverage = a gap nothing surfaces
    # yet. Worth listing so the operator can see "we have a vocabulary
    # for this blind spot but no extractor stamps it" — i.e., either the
    # detector is missing or the corpus genuinely has no such nodes.
    untouched = sorted(set(CAVEAT_REGISTRY) - set(caveat_counts))
    if untouched and caveat_counts:
        summary.append("registered caveats not stamped on any node:")
        for c in untouched:
            summary.append(f"        {c}")

    # ---- output ---------------------------------------------------------
    print("# Depgraph health")
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


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "health",
        help="One-shot graph health summary (validate + orphans + stale + tier-A coverage). Exit 1 if anything wrong.",
    )
    p.set_defaults(func=cmd_health)
