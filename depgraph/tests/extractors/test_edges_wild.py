"""Wild edge-resolution gate. Runs each fixture's extractor (TS or Python
based on src/ contents), compares edges_out against expected.json.

Fixture layout:
  edges/<name>/
    src/          -- source files
    expected.json -- ground-truth edges (and unresolved_edges_expected flag)
    README.md     -- what's tested
    verification.md -- prediction + accuracy log

Language detection: any .ts/.tsx/.js file in src/ → TS extractor;
otherwise → Python in-process.

For Python: repo_path = fixture / "src"  (ids: fixture::file.py::Symbol)
For TS:     repo_path = fixture (root)   (ids: fixture::src/file.ts::Symbol)
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

WILD_DIR = Path(__file__).parent.parent / "fixtures" / "wild" / "edges"
TS_EXTRACTOR = Path(__file__).resolve().parents[2] / "extractors" / "typescript" / "extract.ts"


def _fixtures():
    return sorted(d for d in WILD_DIR.iterdir() if d.is_dir() and (d / "src").exists())


def _is_ts_fixture(fixture: Path) -> bool:
    src = fixture / "src"
    return any(f.suffix in {".ts", ".tsx", ".js"} for f in src.iterdir())


def _run(fixture: Path) -> list[dict]:
    if _is_ts_fixture(fixture):
        proc = subprocess.run(
            ["npx", "tsx", str(TS_EXTRACTOR),
             "--repo-key", "fixture", "--repo-path", str(fixture),
             "--format", "ndjson"],
            capture_output=True, text=True, check=True,
            cwd=TS_EXTRACTOR.parent,
        )
        return [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    else:
        from depgraph.extractors.python.extract import extract_repo
        return list(extract_repo(repo_key="fixture", repo_path=fixture / "src"))


@pytest.mark.parametrize("fixture", _fixtures(), ids=lambda f: f.name)
def test_wild_edges_match_expected(fixture):
    """Every edge declared in expected.json must appear in the actual corpus."""
    expected = json.loads((fixture / "expected.json").read_text())
    actual = _run(fixture)
    actual_edges = {
        (p["id"], e["kind"], e["target"], e.get("confidence"))
        for p in actual
        for e in p.get("edges_out", [])
    }
    for e in expected.get("edges", []):
        triple = (e["source"], e["kind"], e["target"], e.get("confidence", "exact"))
        assert triple in actual_edges, (
            f"{fixture.name}: expected edge {triple} missing.\n"
            f"  Actual edges from source '{e['source']}':\n"
            + "\n".join(
                f"    {ae}" for ae in actual_edges if ae[0] == e["source"]
            )
        )


@pytest.mark.parametrize("fixture", _fixtures(), ids=lambda f: f.name)
def test_wild_unresolved_edges_present_where_expected(fixture):
    """Some fixtures (dynamic_dispatch) MUST emit at least one
    gap-bucket edge (any of the four post-#53 non-`exact`/`fuzzy` values:
    external, unresolved_internal, unresolved_receiver, dynamic). This
    test fires only when expected.json has unresolved_edges_expected: true."""
    expected = json.loads((fixture / "expected.json").read_text())
    if not expected.get("unresolved_edges_expected"):
        return  # nothing to assert for this fixture
    actual = _run(fixture)
    gap_confidences = {
        "external", "unresolved_internal", "unresolved_receiver", "dynamic",
    }
    gaps = [
        e for p in actual
        for e in p.get("edges_out", [])
        if e.get("confidence") in gap_confidences
    ]
    assert gaps, (
        f"{fixture.name}: expected at least one gap-bucket edge "
        f"(confidence in {sorted(gap_confidences)}) but got none"
    )
