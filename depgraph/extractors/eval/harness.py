"""Evaluation harness for language extractors.

Two modes:
- Deterministic: run extractor on case source/, diff against expected.json.
- Judgment: emit a package for a Claude Code session to review.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
EXTRACTORS = REPO_ROOT / "depgraph" / "extractors" / "generic"

LANG_TO_CMD = {
    "python": [sys.executable, str(EXTRACTORS / "python" / "extract.py")],
    "typescript": ["npx", "tsx", str(EXTRACTORS / "typescript" / "extract.ts")],
    "go": [sys.executable, str(EXTRACTORS / "go" / "extract.py")],
    "rust": [sys.executable, str(EXTRACTORS / "rust" / "extract.py")],
}


@dataclass(frozen=True)
class EvalCase:
    path: Path
    language: str
    detectors: list[str]
    expected: dict


def load_case(case_dir: Path) -> EvalCase:
    cfg = tomllib.loads((case_dir / "case.toml").read_text())
    expected = json.loads((case_dir / "expected.json").read_text())
    return EvalCase(
        path=case_dir,
        language=cfg["language"],
        detectors=cfg.get("detectors", []),
        expected=expected,
    )


def _run_extractor(case: EvalCase, repo_key: str, data_dir: Path) -> None:
    cmd = LANG_TO_CMD[case.language] + [
        "--repo-key", repo_key,
        "--repo-path", str(case.path / "source"),
        "--data-dir", str(data_dir),
        "--detectors", ",".join(case.detectors),
    ]
    cwd = (
        EXTRACTORS / case.language
        if case.language == "typescript" else None
    )
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if r.returncode != 0:
        raise RuntimeError(f"extractor failed: {r.stderr}")


def _collect_node_ids(data_dir: Path) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    nodes_dir = data_dir / "nodes"
    if not nodes_dir.exists():
        return out
    for sub in nodes_dir.iterdir():
        if not sub.is_dir():
            continue
        for f in sub.glob("*.json"):
            n = json.loads(f.read_text())
            out.setdefault(n["kind"], set()).add(n["id"])
    return out


def run_deterministic(case_dir: Path, *, repo_key: str = "r") -> dict[str, Any]:
    case = load_case(case_dir)
    with tempfile.TemporaryDirectory() as tmp:
        data = Path(tmp)
        _run_extractor(case, repo_key, data)
        emitted = _collect_node_ids(data)

    precision: dict[str, float] = {}
    recall: dict[str, float] = {}
    missing: dict[str, list[str]] = {}
    expected_nodes = case.expected.get("nodes", {})
    passed = True
    for kind, exp_ids in expected_nodes.items():
        exp = set(exp_ids)
        got = emitted.get(kind, set())
        tp = len(exp & got)
        precision[kind] = tp / len(exp) if exp else 1.0
        recall[kind] = tp / len(exp) if exp else 1.0
        miss = sorted(exp - got)
        if miss:
            passed = False
            missing[kind] = miss
    return {
        "case": case_dir.name, "passed": passed,
        "precision": precision, "recall": recall, "missing": missing,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["run", "judge"])
    p.add_argument("language")
    p.add_argument("--case", default=None,
                   help="case name; default: all cases under corpus/<lang>/")
    args = p.parse_args(argv)

    corpus_dir = Path(__file__).parent / "corpus" / args.language
    cases = (
        [corpus_dir / args.case]
        if args.case else sorted(c for c in corpus_dir.iterdir() if c.is_dir())
    )
    any_failed = False
    for c in cases:
        if args.mode == "run":
            rpt = run_deterministic(c)
            print(json.dumps(rpt, indent=2))
            if not rpt["passed"]:
                any_failed = True
        else:
            from extractors.eval.judge import write_judgment_package
            out = write_judgment_package(c)
            print(f"judgment package written to {out}")
    return 1 if any_failed else 0


if __name__ == "__main__":
    sys.exit(main())
