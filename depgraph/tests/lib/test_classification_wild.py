"""Wild corpus tests for the classification engine.

Each fixture under fixtures/wild/classification/ contains:
  corpus.json   — pre-built list of primitives (what Phases 1-4 would emit)
  expected.json — {"classifications": [...], "conflicts": [...]}
  verification.md — prediction written before expected.json; documents
                    any discrepancy between predicted and actual behaviour.

This avoids re-running extraction for every classification edge case: the
corpus is hand-built to make the classifier rules fire in a controlled way.
"""
import json
from pathlib import Path

import pytest

from depgraph.lib.classification.engine import classify_corpus

WILD_DIR = Path(__file__).parent.parent / "fixtures" / "wild" / "classification"


def _fixtures():
    return sorted(
        d for d in WILD_DIR.iterdir()
        if d.is_dir() and (d / "corpus.json").exists()
    )


@pytest.mark.parametrize("fixture", _fixtures(), ids=lambda f: f.name)
def test_wild_classifications_match_expected(fixture):
    corpus = json.loads((fixture / "corpus.json").read_text())
    expected = json.loads((fixture / "expected.json").read_text())

    decisions = classify_corpus(corpus)

    # Check every explicitly listed classification
    expected_kinds = {e["id"]: e["kind"] for e in expected["classifications"]}
    for prim_id, expected_kind in expected_kinds.items():
        assert prim_id in decisions, (
            f"{fixture.name}: primitive {prim_id!r} not in decisions"
        )
        assert decisions[prim_id].kind == expected_kind, (
            f"{fixture.name}: {prim_id!r} expected kind={expected_kind!r}, "
            f"got kind={decisions[prim_id].kind!r} (rule={decisions[prim_id].rule!r})"
        )

    # Check that primitives NOT listed in classifications are unclassified
    all_ids = {p["id"] for p in corpus}
    unlisted_ids = all_ids - set(expected_kinds)
    for prim_id in unlisted_ids:
        assert decisions[prim_id].kind is None, (
            f"{fixture.name}: {prim_id!r} not in expected classifications "
            f"but got kind={decisions[prim_id].kind!r}"
        )

    # Check conflict entries
    for ec in expected.get("conflicts", []):
        prim_id, conflict_kind = ec["id"], ec["kind"]
        assert prim_id in decisions, (
            f"{fixture.name}: conflict primitive {prim_id!r} not in decisions"
        )
        assert conflict_kind in decisions[prim_id].conflicts, (
            f"{fixture.name}: expected conflict kind={conflict_kind!r} for "
            f"{prim_id!r}, got conflicts={decisions[prim_id].conflicts!r}"
        )
