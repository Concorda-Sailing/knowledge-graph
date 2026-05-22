"""Wild-corpus probe — run the depgraph extractor against real GitHub repos.

Reads `targets.toml`, clones each target into a temp dir at the pinned
commit sha, runs `kg depgraph regen` Mode B against it, and reports:

  - Schema conformance (validation_report fields in _meta.json)
  - Edge-count totals (per language, per edge kind)
  - Unresolved-rate (fraction of edges with confidence != "exact")
  - Anomalies — taxonomy errors, orphan edges, regen failures

The probe is the DISCOVERY mechanism per [[feedback-wild-means-real-repos]].
Synthetic fixtures designed to pass don't surface what real corpora do.

Usage:
  python -m tools.wild_probe.probe                 # all targets
  python -m tools.wild_probe.probe encode-databases # one target
  python -m tools.wild_probe.probe --keep-clones    # don't delete clones

Output: one block per target on stderr, plus a final `results.json` written
to `tools/wild-probe/results/<timestamp>.json` with all metrics.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tomllib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = REPO_ROOT / "tools" / "wild-probe"
TARGETS_FILE = TOOLS_DIR / "targets.toml"
RESULTS_DIR = TOOLS_DIR / "results"
KG = REPO_ROOT / "bin" / "kg"


@dataclass
class Target:
    name: str
    url: str
    sha: str
    language: str
    patterns: list[str]


@dataclass
class ProbeResult:
    target: str
    sha: str
    language: str
    success: bool
    duration_s: float
    primitives_total: int = 0
    primitives_by_kind: dict[str, int] = field(default_factory=dict)
    edges_total: int = 0
    edges_by_kind: dict[str, int] = field(default_factory=dict)
    edges_by_confidence: dict[str, int] = field(default_factory=dict)
    validation_report: dict = field(default_factory=dict)
    # Option-C test-coverage stats (issue #52). Populated from
    # `test_coverage.json` when the regen pass wrote one (i.e. Python
    # targets, today). Empty dict otherwise.
    test_coverage_stats: dict = field(default_factory=dict)
    error: str = ""
    anomalies: list[str] = field(default_factory=list)


def load_targets(path: Path = TARGETS_FILE) -> list[Target]:
    with path.open("rb") as f:
        raw = tomllib.load(f)
    out: list[Target] = []
    for t in raw.get("target", []):
        out.append(Target(
            name=t["name"],
            url=t["url"],
            sha=t["sha"],
            language=t["language"],
            patterns=t.get("patterns", []),
        ))
    return out


def _shallow_clone(target: Target, dest: Path) -> str:
    """Clone the repo at the pinned sha into dest. Returns the actual sha
    used (which may differ from target.sha if the pin is stale, in which
    case we fall back to HEAD and the anomaly is recorded by the caller)."""
    # Try the pinned sha first; fall back to HEAD on failure.
    subprocess.run(
        ["git", "init", "--quiet", str(dest)],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(dest), "remote", "add", "origin", target.url],
        check=True, capture_output=True,
    )
    try:
        subprocess.run(
            ["git", "-C", str(dest), "fetch", "--depth=1", "--quiet",
             "origin", target.sha],
            check=True, capture_output=True, timeout=120,
        )
        subprocess.run(
            ["git", "-C", str(dest), "checkout", "--quiet", target.sha],
            check=True, capture_output=True,
        )
        return target.sha
    except subprocess.CalledProcessError:
        # Pin stale or unreachable as a single-sha fetch; pull HEAD instead.
        subprocess.run(
            ["git", "-C", str(dest), "fetch", "--depth=1", "--quiet",
             "origin", "HEAD"],
            check=True, capture_output=True, timeout=180,
        )
        subprocess.run(
            ["git", "-C", str(dest), "checkout", "--quiet", "FETCH_HEAD"],
            check=True, capture_output=True,
        )
        result = subprocess.run(
            ["git", "-C", str(dest), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        )
        return result.stdout.strip()


def _build_data_dir(data_dir: Path, target: Target, repo_path: Path) -> None:
    """Synthesize a minimal data dir with a one-repo project.toml so Mode B
    has the project context it expects.

    Python targets get the canonical Option-C exclude pattern so test
    files are kept out of the production graph (matching real-world
    project.toml shapes; see issue #52). The depgraph regen pipeline
    then runs the test-coverage walker over those excluded files and
    writes `test_coverage.json`. The probe reads that file back for
    its coverage stats.
    """
    (data_dir / "nodes" / "_index").mkdir(parents=True, exist_ok=True)
    (data_dir / "telemetry").mkdir(exist_ok=True)
    project_toml = data_dir / "project.toml"
    lines = [
        f'[project]',
        f'name = "{target.name}"',
        f'primary_repo = "{target.name}"',
        '',
        f'[repos.{target.name}]',
        f'path = "{repo_path}"',
        f'languages = ["{target.language}"]',
    ]
    if target.language == "python":
        # Mirror the canonical production-side exclusions the issue cites
        # (#52) so the probe verifies the Option-C path end-to-end: tests
        # stay out of the production graph, the coverage walker fills the
        # gap.
        lines.append(
            'exclude_paths = ["**/tests/**", "**/test_*.py", "**/*_test.py"]'
        )
    project_toml.write_text("\n".join(lines) + "\n")


def _run_regen(data_dir: Path, target: Target, repo_path: Path) -> tuple[bool, str]:
    """Invoke `kg depgraph regen` against the cloned repo. Returns (ok, stderr_tail).

    Uses `--repo-key` alone (no `--repo-path`) so regen looks the repo
    up from the synthesized project.toml — that's the path that honors
    `exclude_paths` and `test_paths`. Mode B (both flags) would bypass
    project.toml and miss the Option-C exclude pattern.
    """
    cmd = [
        str(KG),
        "depgraph", "--data-dir", str(data_dir),
        "regen",
        "--repo-key", target.name,
        "--no-embeddings",
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True, text=True,
        timeout=600,
    )
    if proc.returncode != 0:
        # Capture the last few stderr lines for diagnosis.
        tail = "\n".join(proc.stderr.splitlines()[-20:])
        return False, tail
    return True, ""


def _depgraph_dir(data_dir: Path) -> Path:
    """Return the actual `depgraph/` subdir where regen writes nodes.
    Mode B writes under `<data_dir>/depgraph/`, not directly under
    `<data_dir>/nodes/`."""
    return data_dir / "depgraph"


def _read_meta(data_dir: Path) -> dict:
    meta_path = _depgraph_dir(data_dir) / "nodes" / "_meta.json"
    if not meta_path.exists():
        return {}
    return json.loads(meta_path.read_text())


def _read_test_coverage(data_dir: Path) -> dict:
    """Read the Option-C test-coverage stats block (#52). Returns an
    empty dict if no coverage file was written (TS-only target, or a
    Python target whose regen failed before the coverage pass)."""
    path = _depgraph_dir(data_dir) / "test_coverage.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text())
    return payload.get("stats") or {}


def _walk_corpus_stats(data_dir: Path) -> tuple[dict[str, int], dict[str, int], dict[str, int], int, int]:
    """Walk all node JSON files; return primitives_by_kind, edges_by_kind,
    edges_by_confidence, primitives_total, edges_total."""
    prims_by_kind: dict[str, int] = {}
    edges_by_kind: dict[str, int] = {}
    edges_by_conf: dict[str, int] = {}
    prims_total = 0
    edges_total = 0
    nodes_dir = _depgraph_dir(data_dir) / "nodes"
    if not nodes_dir.exists():
        return prims_by_kind, edges_by_kind, edges_by_conf, 0, 0
    for jf in nodes_dir.rglob("*.json"):
        if jf.parent.name == "_index" or jf.name.startswith("_"):
            continue
        try:
            node = json.loads(jf.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if "primitive" not in node:
            continue
        prims_total += 1
        prims_by_kind[node["primitive"]] = prims_by_kind.get(node["primitive"], 0) + 1
        for e in node.get("edges_out", []):
            edges_total += 1
            kind = e.get("kind", "unknown")
            edges_by_kind[kind] = edges_by_kind.get(kind, 0) + 1
            conf = e.get("confidence", "exact")
            edges_by_conf[conf] = edges_by_conf.get(conf, 0) + 1
    return prims_by_kind, edges_by_kind, edges_by_conf, prims_total, edges_total


def _surface_anomalies(result: ProbeResult, target: Target) -> None:
    """Inspect a successful probe's stats and append anomalies — patterns
    that look suspect on a real corpus (overclaimed exact, unresolved
    rate too high, missing edge kinds expected for the language)."""
    if result.edges_total == 0:
        result.anomalies.append("empty edge set — extractor produced no edges")
        return

    # Per-confidence sanity — issue #53 Option A subdivided the previously-
    # collapsed `unresolved` bucket into four (`external`,
    # `unresolved_internal`, `unresolved_receiver`, `dynamic`). The probe
    # warns if the taxonomy is degenerate on a non-trivial corpus: the
    # pre-#53 "0 fuzzy" warning is dropped (fuzzy is genuinely rare on
    # python corpora) and replaced with two new checks.
    if result.edges_total > 100:
        # `unresolved` is gone — its presence here is a regression that
        # would mean an extractor still hard-codes the old enum.
        if result.edges_by_confidence.get("unresolved", 0):
            result.anomalies.append(
                f"legacy `unresolved` confidence still present: "
                f"{result.edges_by_confidence['unresolved']} edges "
                f"(should be 0 after #53 Option A)"
            )
        # All non-`exact` edges should now bucket into one of the four
        # specific values. If `external` is the only non-`exact` bucket
        # populated, the corpus is healthier than expected — fine. But if
        # both `unresolved_internal` and `unresolved_receiver` are zero,
        # the maintainer can't distinguish resolver-bug gaps from
        # missing-typed-receiver gaps; surface the imbalance.
        n_internal = result.edges_by_confidence.get("unresolved_internal", 0)
        n_receiver = result.edges_by_confidence.get("unresolved_receiver", 0)
        if n_internal == 0 and n_receiver == 0 and result.edges_total > 500:
            result.anomalies.append(
                "no unresolved_internal/unresolved_receiver edges on a "
                f"{result.edges_total}-edge corpus — taxonomy may be under-populated"
            )

    # Gap-rate — sum of all non-`exact`/`fuzzy`/`external` confidences.
    # `external` is expected (deliberate library terminals) so we don't
    # count it as a gap; the new ratio is a tighter signal than the old
    # combined `unresolved` rate.
    n_gap = sum(
        result.edges_by_confidence.get(c, 0)
        for c in ("unresolved_internal", "unresolved_receiver", "dynamic")
    )
    gap_rate = n_gap / result.edges_total
    if gap_rate > 0.30:
        result.anomalies.append(
            f"high gap-edge rate: {gap_rate:.0%} ({n_gap}/{result.edges_total})"
        )

    # Language-specific expectations.
    if target.language == "python":
        if result.edges_by_kind.get("imports", 0) == 0:
            result.anomalies.append("python target with 0 imports edges")
        if "sqlalchemy-orm" in target.patterns:
            if result.edges_by_kind.get("references_orm", 0) == 0:
                result.anomalies.append(
                    "#54 expected: sqlalchemy-orm target has 0 references_orm edges"
                )
        # Option-C coverage sanity (#52). A Python target whose
        # synthesized project.toml excludes `**/tests/**` should have
        # SOME coverage if the repo ships any tests at all. Zero
        # `test_files_scanned` on a multi-file repo points at a
        # misconfiguration (the exclude pattern is wrong, the walker
        # didn't run, etc.).
        cs = result.test_coverage_stats or {}
        if (
            result.primitives_total > 50
            and cs.get("test_files_scanned", 0) == 0
        ):
            result.anomalies.append(
                "#52 sanity: 0 test files scanned on a non-trivial python "
                "corpus — coverage walker may have misfired"
            )
    if target.language == "typescript":
        if result.edges_by_kind.get("imports", 0) == 0:
            result.anomalies.append("typescript target with 0 imports edges")

    # Validation report — orphan edges, primitive errors, edge errors.
    # `validation_report` holds the actual lists; sibling `*_count` keys
    # at the meta root hold the counts. Use the lists so we can sample.
    vr = result.validation_report
    if vr:
        for k in ("orphan_edges", "primitive_errors", "edge_errors", "slug_collisions"):
            n = len(vr.get(k, []) or [])
            if n > 0:
                # Capture a sample (first 3) for context.
                sample = vr[k][:3]
                result.anomalies.append(f"{k}: {n} (sample: {sample})")


def run_one(target: Target, *, keep_clone: bool = False) -> ProbeResult:
    start = datetime.now(timezone.utc)
    print(f"\n=== {target.name} ({target.language}) ===", file=sys.stderr)
    print(f"    url: {target.url}", file=sys.stderr)
    print(f"    sha: {target.sha}", file=sys.stderr)

    result = ProbeResult(
        target=target.name,
        sha=target.sha,
        language=target.language,
        success=False,
        duration_s=0.0,
    )

    # Manual temp dir (not TemporaryDirectory) so --keep-clones actually
    # keeps the dir — TemporaryDirectory.__del__ cleans up on GC.
    import tempfile
    tmp_dir_name = tempfile.mkdtemp(prefix=f"wildprobe-{target.name}-")
    cleanup_needed = not keep_clone
    try:
        tmp_dir = Path(tmp_dir_name)
        repo_path = tmp_dir / "repo"
        data_dir = tmp_dir / "data"

        # Clone.
        print(f"    cloning...", file=sys.stderr)
        try:
            actual_sha = _shallow_clone(target, repo_path)
        except subprocess.CalledProcessError as e:
            result.error = f"clone failed: {e.stderr.decode()[:200] if e.stderr else str(e)}"
            return result
        if actual_sha != target.sha:
            result.anomalies.append(
                f"pinned sha unreachable; fell back to HEAD ({actual_sha[:12]})"
            )
            result.sha = actual_sha

        # Synthesize data dir.
        _build_data_dir(data_dir, target, repo_path)

        # Regen.
        print(f"    regenerating...", file=sys.stderr)
        ok, err = _run_regen(data_dir, target, repo_path)
        if not ok:
            result.error = f"regen failed: {err}"
            return result

        # Read meta + walk corpus.
        meta = _read_meta(data_dir)
        result.validation_report = meta.get("validation_report", {})
        (
            result.primitives_by_kind,
            result.edges_by_kind,
            result.edges_by_confidence,
            result.primitives_total,
            result.edges_total,
        ) = _walk_corpus_stats(data_dir)
        result.test_coverage_stats = _read_test_coverage(data_dir)
        result.success = True

        _surface_anomalies(result, target)
    finally:
        result.duration_s = (datetime.now(timezone.utc) - start).total_seconds()
        if keep_clone:
            print(f"    clone kept at: {tmp_dir_name}", file=sys.stderr)
        elif cleanup_needed:
            shutil.rmtree(tmp_dir_name, ignore_errors=True)

    return result


def _format_summary(result: ProbeResult) -> str:
    lines = [
        f"    duration: {result.duration_s:.1f}s",
        f"    success:  {result.success}",
    ]
    if not result.success:
        lines.append(f"    error:    {result.error}")
        return "\n".join(lines)
    lines.extend([
        f"    primitives: {result.primitives_total} "
        f"({', '.join(f'{k}={v}' for k,v in sorted(result.primitives_by_kind.items()))})",
        f"    edges:      {result.edges_total} "
        f"({', '.join(f'{k}={v}' for k,v in sorted(result.edges_by_kind.items()))})",
        f"    confidence: "
        f"{', '.join(f'{k}={v}' for k,v in sorted(result.edges_by_confidence.items()))}",
    ])
    if result.test_coverage_stats:
        cs = result.test_coverage_stats
        lines.append(
            f"    coverage:   "
            f"test_files_scanned={cs.get('test_files_scanned', 0)}, "
            f"tested_nodes={cs.get('tested_nodes', 0)}, "
            f"ratio={cs.get('tested_node_ratio', 0.0):.3f}"
        )
    if result.anomalies:
        lines.append("    anomalies:")
        for a in result.anomalies:
            lines.append(f"      - {a}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("names", nargs="*",
                        help="Optional list of target names; runs all if omitted.")
    parser.add_argument("--keep-clones", action="store_true",
                        help="Don't delete cloned repos on exit.")
    args = parser.parse_args()

    targets = load_targets()
    if args.names:
        wanted = set(args.names)
        targets = [t for t in targets if t.name in wanted]
        if not targets:
            print(f"No targets matched: {sorted(wanted)}", file=sys.stderr)
            return 1

    results: list[ProbeResult] = []
    for target in targets:
        r = run_one(target, keep_clone=args.keep_clones)
        print(_format_summary(r), file=sys.stderr)
        results.append(r)

    # Write results.
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    out_path = RESULTS_DIR / f"{ts}.json"
    out_path.write_text(json.dumps(
        [asdict(r) for r in results], indent=2, sort_keys=True,
    ) + "\n")
    print(f"\nResults written to: {out_path}", file=sys.stderr)

    # Exit nonzero if any target failed.
    return 0 if all(r.success for r in results) else 2


if __name__ == "__main__":
    sys.exit(main())
