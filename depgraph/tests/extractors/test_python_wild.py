"""Wild-corpus runner for Phase 2."""
import json
from pathlib import Path
import pytest
from depgraph.extractors.python.extract import extract_repo

WILD_DIR = Path(__file__).parent.parent / "fixtures" / "wild" / "primitives_py"


def _fixtures():
    return sorted(d for d in WILD_DIR.iterdir() if d.is_dir() and (d / "src").exists())


@pytest.mark.parametrize("fixture", _fixtures(), ids=lambda f: f.name)
def test_wild_primitives_match_expected(fixture):
    expected = json.loads((fixture / "expected.json").read_text())
    actual = list(extract_repo(repo_key="fixture", repo_path=fixture))
    actual_ids = {p["id"] for p in actual}
    expected_ids = {p["id"] for p in expected["primitives"]}
    missing = expected_ids - actual_ids
    extra = actual_ids - expected_ids
    assert not missing and not extra, f"{fixture.name}: missing={missing}, extra={extra}"


@pytest.mark.parametrize("fixture", _fixtures(), ids=lambda f: f.name)
def test_wild_edges_subset_of_actual(fixture):
    expected = json.loads((fixture / "expected.json").read_text())
    actual = list(extract_repo(repo_key="fixture", repo_path=fixture))
    actual_edges = {(p["id"], e["kind"], e["target"])
                    for p in actual for e in p.get("edges_out", [])}
    for e in expected.get("edges", []):
        triple = (e["source"], e["kind"], e["target"])
        assert triple in actual_edges, f"{fixture.name}: expected edge {triple} missing"
