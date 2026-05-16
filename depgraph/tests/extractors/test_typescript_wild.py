"""Wild-corpus runner for Phase 1.

For each fixture dir under wild/primitives_ts/, run the extractor and
compare emitted primitives + edges against expected.json.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

WILD_DIR = Path(__file__).parent.parent / "fixtures" / "wild" / "primitives_ts"
EXTRACTOR = Path(__file__).resolve().parents[2] / "extractors" / "typescript" / "extract.ts"


def _fixtures():
    return sorted(d for d in WILD_DIR.iterdir() if d.is_dir() and (d / "src").exists())


def _run_extractor(fixture_root: Path) -> list[dict]:
    proc = subprocess.run([
        "npx", "tsx", str(EXTRACTOR),
        "--repo-key", "fixture", "--repo-path", str(fixture_root),
        "--format", "ndjson",
    ], capture_output=True, text=True, check=True, cwd=EXTRACTOR.parent)
    return [json.loads(l) for l in proc.stdout.splitlines() if l.strip()]


@pytest.mark.parametrize("fixture", _fixtures(), ids=lambda f: f.name)
def test_wild_fixture_primitives_match_expected(fixture):
    expected = json.loads((fixture / "expected.json").read_text())
    actual = _run_extractor(fixture)
    actual_ids = {p["id"] for p in actual}
    expected_ids = {p["id"] for p in expected["primitives"]}
    missing = expected_ids - actual_ids
    extra = actual_ids - expected_ids
    assert not missing and not extra, (
        f"{fixture.name}: missing={missing}, extra={extra}")


@pytest.mark.parametrize("fixture", _fixtures(), ids=lambda f: f.name)
def test_wild_fixture_edges_subset_of_actual(fixture):
    expected = json.loads((fixture / "expected.json").read_text())
    actual = _run_extractor(fixture)
    actual_edges = {(p["id"], e["kind"], e["target"])
                    for p in actual for e in p.get("edges_out", [])}
    for e in expected.get("edges", []):
        triple = (e["source"], e["kind"], e["target"])
        assert triple in actual_edges, (
            f"{fixture.name}: expected edge {triple} missing from actual")
