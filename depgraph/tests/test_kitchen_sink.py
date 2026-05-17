"""End-to-end gate on the kitchen-sink mini-project.

Runs the full pipeline (extract → edges → SQL → cross-ref → db_access →
classify → reconcile) and asserts kind distribution + invariants.

The regen subprocess needs a project.toml with absolute paths at
data_dir/project.toml — written by the fixture before invoking regen.
"""
import filecmp
import json
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "wild" / "kitchen_sink"
# depgraph/ is one level below knowledge-graph root
KG_ROOT = Path(__file__).parent.parent.parent
VENV_PY = Path(__file__).parent.parent / "venv" / "bin" / "python"
PYTHON = str(VENV_PY) if VENV_PY.exists() else sys.executable


def _write_project_toml(data_dir: Path) -> None:
    """Write a project.toml with absolute fixture paths to data_dir."""
    api_path = FIXTURE / "api"
    web_path = FIXTURE / "web"
    content = f"""[project]
name = "kitchen-sink"

[repos.kitchen-sink-api]
path = "{api_path}"
languages = ["python", "sql"]
migrations_dirs = ["migrations"]

[repos.kitchen-sink-web]
path = "{web_path}"
languages = ["typescript"]
"""
    (data_dir).mkdir(parents=True, exist_ok=True)
    (data_dir / "project.toml").write_text(content)


def _run_regen(data_dir: Path) -> None:
    import os
    env = {**os.environ, "PYTHONPATH": str(KG_ROOT)}
    result = subprocess.run(
        [PYTHON, "-m", "kg.cli", "depgraph", "--data-dir", str(data_dir), "regen"],
        capture_output=True,
        text=True,
        cwd=str(KG_ROOT),
        env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"regen failed (rc={result.returncode}):\n"
            f"STDOUT: {result.stdout[-2000:]}\n"
            f"STDERR: {result.stderr[-2000:]}"
        )


@pytest.fixture(scope="module")
def regen_kitchen_sink(tmp_path_factory):
    out = tmp_path_factory.mktemp("kitchen_sink_corpus")
    _write_project_toml(out)
    _run_regen(out)
    # regen writes under out/depgraph/nodes/ (resolver appends depgraph/)
    return out / "depgraph"


def _load_all_nodes(data_dir: Path):
    nodes = []
    for p in (data_dir / "nodes").rglob("*.json"):
        if "_index" in p.parts or p.name == "_meta.json":
            continue
        nodes.append(json.loads(p.read_text()))
    return nodes


# ---------------------------------------------------------------------------
# Test 1 — exact kind distribution
# ---------------------------------------------------------------------------

def test_kitchen_sink_kind_distribution(regen_kitchen_sink):
    expected = json.loads((FIXTURE / "expected.json").read_text())
    nodes = _load_all_nodes(regen_kitchen_sink)
    counts: dict[str, int] = {}
    for n in nodes:
        if n.get("kind"):
            counts[n["kind"]] = counts.get(n["kind"], 0) + 1
    for kind, expected_count in expected["kind_counts"].items():
        assert counts.get(kind) == expected_count, (
            f"{kind}: expected {expected_count}, got {counts.get(kind, 0)}"
        )


# ---------------------------------------------------------------------------
# Test 2 — spot-check known primitive classifications
# ---------------------------------------------------------------------------

def test_kitchen_sink_spot_check_classifications(regen_kitchen_sink):
    expected = json.loads((FIXTURE / "expected.json").read_text())
    by_id = {n["id"]: n for n in _load_all_nodes(regen_kitchen_sink)}
    for check in expected["spot_check_classifications"]:
        actual_kind = by_id.get(check["id"], {}).get("kind")
        assert actual_kind == check["kind"], (
            f"{check['id']}: expected kind={check['kind']!r}, got {actual_kind!r}"
        )


# ---------------------------------------------------------------------------
# Test 3 — no orphan edges
# ---------------------------------------------------------------------------

def test_kitchen_sink_no_orphan_edges(regen_kitchen_sink):
    """Every non-external edge target must resolve to a known primitive."""
    nodes = _load_all_nodes(regen_kitchen_sink)
    by_id = {n["id"]: n for n in nodes}
    orphans = []
    for n in nodes:
        for e in n.get("edges_out", []):
            tgt = e["target"]
            if tgt.startswith("external::"):
                continue
            if tgt not in by_id:
                orphans.append({"source": n["id"], "target": tgt, "kind": e["kind"]})
    assert not orphans, f"orphan edges found: {orphans[:10]}"


# ---------------------------------------------------------------------------
# Test 4 — every model has exactly one references→schema edge
# ---------------------------------------------------------------------------

def test_kitchen_sink_models_reference_schemas(regen_kitchen_sink):
    """Invariant: every model has exactly one references→schema edge."""
    nodes = _load_all_nodes(regen_kitchen_sink)
    by_id = {n["id"]: n for n in nodes}
    for n in nodes:
        if n.get("kind") != "model":
            continue
        schema_refs = [
            e for e in n.get("edges_out", [])
            if e["kind"] == "references"
            and by_id.get(e["target"], {}).get("kind") == "schema"
        ]
        assert len(schema_refs) == 1, (
            f"model {n['id']} has {len(schema_refs)} schema refs (expected 1)"
        )


# ---------------------------------------------------------------------------
# Test 5 — determinism: two consecutive regens produce identical output
# ---------------------------------------------------------------------------

def test_kitchen_sink_determinism(regen_kitchen_sink, tmp_path):
    """Second regen must produce byte-identical output."""
    second = tmp_path / "second"
    _write_project_toml(second)
    _run_regen(second)
    second_depgraph = second / "depgraph"

    def collect_node_files(base: Path) -> dict[str, str]:
        """rel-path → content for all node JSON files (excluding _index, _meta)."""
        result = {}
        for p in (base / "nodes").rglob("*.json"):
            if "_index" in p.parts or p.name == "_meta.json":
                continue
            rel = str(p.relative_to(base / "nodes"))
            result[rel] = p.read_text()
        return result

    first_files = collect_node_files(regen_kitchen_sink)
    second_files = collect_node_files(second_depgraph)

    assert set(first_files) == set(second_files), (
        f"file-set differs between runs:\n"
        f"  only in first: {sorted(set(first_files) - set(second_files))[:5]}\n"
        f"  only in second: {sorted(set(second_files) - set(first_files))[:5]}"
    )
    diffs = [k for k in first_files if first_files[k] != second_files[k]]
    assert not diffs, (
        f"non-deterministic files ({len(diffs)}): {diffs[:5]}"
    )
