"""Pass A — structural classifier for the dossier-draft two-pass split (#57).

This pass turns one node's graph context into structured JSON. It runs
*before* any prose LLM call so the prose pass can be grounded in
classified data rather than asked to derive structure and write narrative
in a single head.

Design choices (per #57's "rule-based classifier first" guidance):

  - Rule-based, no LLM. Everything the schema asks for is derivable from
    the node dict, the dependents index, and (optionally) `git log`. The
    LLM-fallback variant is left out of the first cut; classifier output
    is the contract, the implementation can be swapped later without
    touching Pass B.
  - Deterministic. Same inputs → same output. No timestamps, no model
    randomness. Hashable for caching by future callers.
  - Read-only. The classifier never writes to disk; it returns a
    `ClassifierResult` dataclass that the caller can serialize or pipe
    into Pass B.

The output shape mirrors the draft in #57's issue body:

    {
      "node_kind": "model" | "endpoint" | ...,
      "coverage_caveats": [...],          # populated by #55 when it lands
      "salient_inbound_edges": [...],     # top-N dependents by call-site density
      "salient_outbound_edges": [...],    # outbound edges grouped by kind
      "git_log_signal": {"recent_fix": bool, "recent_revert": bool, "high_churn": bool},
      "test_coverage_hint": "tested" | "untested" | "unknown",
    }
"""
from __future__ import annotations

import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


# Top-N caps for salient-edge lists. Keep small enough that the Pass B
# prompt stays under a few KB even on hub nodes with hundreds of edges.
_SALIENT_INBOUND_LIMIT = 8
_SALIENT_OUTBOUND_PER_KIND_LIMIT = 5

# Recency window for git-log signals (days). Anything older isn't
# treated as a "recent" event — the dossier prose should describe it
# from source rather than reach for it as fresh history.
_GIT_SIGNAL_WINDOW_DAYS = 90

# Threshold for `high_churn` — commits touching the file in the window.
# 10+ commits in 90 days = "this file moves often, treat invariants
# with caution." Tuned for active feature codebases; can be made
# configurable if churn baselines vary by project.
_HIGH_CHURN_THRESHOLD = 10


@dataclass
class SalientEdge:
    """One row in `salient_inbound_edges` or `salient_outbound_edges`.

    For inbound: `target` is the dependent node id (the caller).
    For outbound: `target` is the callee node id (what this symbol uses).
    """
    target: str
    kind: str           # edge kind: calls / imports / reads / extends / references / ...
    via: str = ""       # `via` discriminator from the edge record (function_call, etc.)
    where: str = ""     # source location of the edge ("path:line"), if recorded
    confidence: str = ""  # "exact" | "heuristic" | etc., when the extractor sets it


@dataclass
class GitLogSignal:
    """Coarse-grained git-history signals. Booleans only — the prose pass
    decides how (or whether) to mention them."""
    recent_fix: bool = False
    recent_revert: bool = False
    high_churn: bool = False
    commits_in_window: int = 0


@dataclass
class ClassifierResult:
    """The complete Pass A output for one node. Matches the draft JSON
    shape in #57's issue body."""
    node_kind: str
    coverage_caveats: list[str] = field(default_factory=list)
    salient_inbound_edges: list[SalientEdge] = field(default_factory=list)
    salient_outbound_edges: list[SalientEdge] = field(default_factory=list)
    git_log_signal: GitLogSignal = field(default_factory=GitLogSignal)
    test_coverage_hint: str = "unknown"

    def to_json_dict(self) -> dict:
        """Plain-JSON form, useful for serialization or for embedding
        into a Pass B prompt as a fenced block."""
        return asdict(self)


def run_classifier(
    node: dict,
    *,
    dependents_index: dict[str, list[dict]],
    nodes_by_id: dict[str, dict],
    repo_root: Optional[Path] = None,
) -> ClassifierResult:
    """Compute the structured classification for a single node.

    `dependents_index` is the reverse-edge map (`nodes/_index/by_target.json`
    parsed form). `nodes_by_id` is used to identify test-file dependents
    (for `test_coverage_hint`) by checking the dependent's `kind`.
    `repo_root` is the on-disk path to the node's repo; passed when
    `git log` should be consulted. Pass None to skip git signals (signals
    will all be False, commits_in_window=0).
    """
    nid = node.get("id") or ""
    node_kind = node.get("kind") or node.get("primitive") or "unknown"

    deps = dependents_index.get(nid) or []
    inbound = _rank_inbound(deps)

    edges_out = node.get("edges_out") or []
    outbound = _rank_outbound(edges_out)

    test_hint = _classify_test_coverage(deps, nodes_by_id)

    if repo_root is not None:
        src = node.get("source") or {}
        rel = src.get("path")
        git_signal = _git_log_signals(repo_root, rel) if rel else GitLogSignal()
    else:
        git_signal = GitLogSignal()

    # `coverage_caveats` is reserved for #55. The classifier exposes the
    # field today so Pass B's prompt slot is stable; the list stays empty
    # until #55 wires its enums in here.
    coverage_caveats: list[str] = []

    return ClassifierResult(
        node_kind=node_kind,
        coverage_caveats=coverage_caveats,
        salient_inbound_edges=inbound,
        salient_outbound_edges=outbound,
        git_log_signal=git_signal,
        test_coverage_hint=test_hint,
    )


def _rank_inbound(deps: list[dict]) -> list[SalientEdge]:
    """Top-N dependents by call-site density.

    Density = how many times a single source node references this target.
    The reverse-edge index records one entry per call site, so we group
    by source id and count. Ties broken by edge kind alphabetically, then
    by source id, for determinism.
    """
    counts: dict[tuple[str, str, str], dict] = {}
    for d in deps:
        key = (d.get("source") or "?", d.get("kind") or "?", d.get("via") or "")
        slot = counts.setdefault(key, {"count": 0, "edge": d})
        slot["count"] += 1

    ranked = sorted(
        counts.items(),
        key=lambda kv: (-kv[1]["count"], kv[0][1], kv[0][0]),
    )
    out: list[SalientEdge] = []
    for (src, kind, via), slot in ranked[:_SALIENT_INBOUND_LIMIT]:
        edge = slot["edge"]
        out.append(SalientEdge(
            target=src,
            kind=kind,
            via=via,
            where=edge.get("where") or "",
            confidence=edge.get("confidence") or "",
        ))
    return out


def _rank_outbound(edges_out: list[dict]) -> list[SalientEdge]:
    """Salient outbound edges, grouped by kind then capped per group.

    Different edge kinds carry different meaning (extends / references /
    calls / imports), so dossier-relevant outbound info needs at least
    one per kind. We sort kinds alphabetically and take up to
    `_SALIENT_OUTBOUND_PER_KIND_LIMIT` from each.
    """
    by_kind: dict[str, list[dict]] = {}
    for e in edges_out:
        by_kind.setdefault(e.get("kind") or "?", []).append(e)

    out: list[SalientEdge] = []
    for kind in sorted(by_kind):
        # Stable ordering within a kind: by target, then via.
        group = sorted(
            by_kind[kind],
            key=lambda e: (e.get("target") or "", e.get("via") or ""),
        )
        for e in group[:_SALIENT_OUTBOUND_PER_KIND_LIMIT]:
            out.append(SalientEdge(
                target=e.get("target") or "?",
                kind=kind,
                via=e.get("via") or "",
                where=e.get("where") or "",
                confidence=e.get("confidence") or "",
            ))
    return out


def _classify_test_coverage(
    deps: list[dict],
    nodes_by_id: dict[str, dict],
) -> str:
    """`tested` if any dependent node has kind=='test'; else `unknown`.

    We never say `untested` from this signal alone — the absence of a
    `calls`-edge dependent in our corpus could mean "no test exists" or
    "the test exists but our extractor didn't link it." Better to say
    nothing than to confidently mis-classify untested code as untested
    when the gap is in our tooling. Once #52 lands richer test-coverage
    extraction this can grow a third arm.
    """
    for d in deps:
        src_id = d.get("source")
        if not src_id:
            continue
        src_node = nodes_by_id.get(src_id)
        if src_node and src_node.get("kind") == "test":
            return "tested"
    return "unknown"


def _git_log_signals(repo_root: Path, rel_path: str) -> GitLogSignal:
    """Parse `git log` subjects for fix/revert keywords and count commits.

    Best-effort: any subprocess / OS error returns an all-False signal.
    The dossier prose pass is allowed to consume these as hints, not as
    ground truth — the prose grounding rule still says "quote the commit
    verbatim, don't paraphrase from this summary."
    """
    if not (repo_root / ".git").exists():
        return GitLogSignal()
    try:
        out = subprocess.run(
            [
                "git", "log",
                f"--since={_GIT_SIGNAL_WINDOW_DAYS}.days.ago",
                "--format=%s",
                "--", rel_path,
            ],
            cwd=str(repo_root),
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return GitLogSignal()

    subjects = [l.strip() for l in (out.stdout or "").splitlines() if l.strip()]
    if not subjects:
        return GitLogSignal()

    # Conservative keyword detection — first token (typed by humans as
    # "fix:" / "Fix " / "fixes" / "Revert "). Avoid matching "prefix"
    # or "infix" by checking word boundaries cheaply.
    def _has_keyword(line: str, keywords: tuple[str, ...]) -> bool:
        head = line.lower()
        # Conventional-commit form: "fix: ..." or "fix(scope): ..."
        for kw in keywords:
            if head.startswith(kw + ":") or head.startswith(kw + "("):
                return True
            # Plain English form: starts with the verb followed by space.
            if head.startswith(kw + " "):
                return True
        return False

    recent_fix = any(_has_keyword(s, ("fix", "fixes", "fixed")) for s in subjects)
    recent_revert = any(_has_keyword(s, ("revert",)) for s in subjects)

    return GitLogSignal(
        recent_fix=recent_fix,
        recent_revert=recent_revert,
        high_churn=len(subjects) >= _HIGH_CHURN_THRESHOLD,
        commits_in_window=len(subjects),
    )


def format_classifier_block(result: ClassifierResult) -> str:
    """Render `result` as a markdown block suitable for embedding in the
    Pass B prompt. The format is deliberately structured (not free prose)
    so the prose pass can refer to specific fields like
    'salient_inbound_edges' and quote them verbatim instead of summarizing.

    Empty lists collapse to '(none)' rather than disappearing — the
    presence of the header is a signal to the model that the field was
    consulted and came back empty, not that we forgot to mention it.
    """
    lines: list[str] = ["## Structured facts about this node (Pass A output)"]
    lines.append("")
    lines.append(
        "These facts were derived deterministically from the graph. Treat "
        "them as ground truth and do not re-derive them. If your prose "
        "would contradict a fact below, the prose is wrong."
    )
    lines.append("")
    lines.append(f"- node_kind: `{result.node_kind}`")
    lines.append(f"- test_coverage_hint: `{result.test_coverage_hint}`")

    gls = result.git_log_signal
    lines.append(
        f"- git_log_signal: recent_fix={gls.recent_fix}, "
        f"recent_revert={gls.recent_revert}, high_churn={gls.high_churn} "
        f"(commits_in_window={gls.commits_in_window})"
    )

    if result.coverage_caveats:
        lines.append("- coverage_caveats:")
        for c in result.coverage_caveats:
            lines.append(f"    - {c}")
    else:
        lines.append("- coverage_caveats: (none)")

    lines.append("")
    lines.append("### salient_inbound_edges")
    if result.salient_inbound_edges:
        for e in result.salient_inbound_edges:
            lines.append(_format_edge_line(e))
    else:
        lines.append("- (none)")

    lines.append("")
    lines.append("### salient_outbound_edges")
    if result.salient_outbound_edges:
        for e in result.salient_outbound_edges:
            lines.append(_format_edge_line(e))
    else:
        lines.append("- (none)")

    return "\n".join(lines)


def _format_edge_line(e: SalientEdge) -> str:
    bits = [f"{e.kind}"]
    if e.via:
        bits.append(f"via={e.via}")
    if e.where:
        bits.append(f"@ {e.where}")
    if e.confidence:
        bits.append(f"[{e.confidence}]")
    return f"- {e.target}  ({', '.join(bits)})"
