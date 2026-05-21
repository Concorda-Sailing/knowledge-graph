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
    has the project context it expects."""
    (data_dir / "nodes" / "_index").mkdir(parents=True, exist_ok=True)
    (data_dir / "telemetry").mkdir(exist_ok=True)
    project_toml = data_dir / "project.toml"
    project_toml.write_text(
        f'[project]\n'
        f'name = "{target.name}"\n'
        f'primary_repo = "{target.name}"\n'
        f'\n'
        f'[repos.{target.name}]\n'
        f'path = "{repo_path}"\n'
        f'languages = ["{target.language}"]\n'
    )


def _run_regen(data_dir: Path, target: Target, repo_path: Path) -> tuple[bool, str]:
    """Invoke `kg depgraph regen` against the cloned repo. Returns (ok, stderr_tail)."""
    cmd = [
        str(KG),
        "depgraph", "--data-dir", str(data_dir),
        "regen",
        "--repo-key", target.name,
        "--repo-path", str(repo_path),
        "--languages", target.language,
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

    # Per-confidence breakdown — flag when 'fuzzy' is unused (taxonomy collapse, #53).
    n_fuzzy = result.edges_by_confidence.get("fuzzy", 0)
    if n_fuzzy == 0 and result.edges_total > 100:
        result.anomalies.append(
            f"taxonomy collapse: 0 fuzzy edges out of {result.edges_total} "
            f"(per #53, the bucket is unused in practice)"
        )

    # Unresolved rate.
    n_unresolved = result.edges_by_confidence.get("unresolved", 0)
    rate = n_unresolved / result.edges_total
    if rate > 0.50:
        result.anomalies.append(
            f"high unresolved rate: {rate:.0%} ({n_unresolved}/{result.edges_total})"
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
