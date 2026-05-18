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

# Fixture has no package.json / pyproject.toml for plugin auto-detection,
# so force the framework set this fixture is written against.
[classification.plugins]
enable = ["fastapi", "sqlalchemy", "pytest", "react", "vitest"]

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
    nodes_root = data_dir / "nodes"
    for p in nodes_root.rglob("*.json"):
        # Skip every corpus-meta path component (_index/, _meta.json,
        # _manifests/, _archive/, etc.) — only node files live elsewhere.
        if p.name.startswith("_") or any(
            part.startswith("_") for part in p.relative_to(nodes_root).parts
        ):
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
# Unified-kind contract — every node, every language, non-null kind
# ---------------------------------------------------------------------------

# Mirrors lib/classification/writer.py — kept inline so a writer change
# that adds/renames a kind dir has to update this contract too.
_CLASSIFIED_KINDS = {
    "component", "hook", "endpoint", "service",
    "model", "schema", "test", "util", "route_call",
}
_PRIMITIVE_KINDS = {"module", "package", "class", "function", "variable"}
_VALID_KINDS = _CLASSIFIED_KINDS | _PRIMITIVE_KINDS


def test_every_node_has_non_null_kind_in_valid_union(regen_kitchen_sink):
    """Contract: every node written to disk carries a non-null `kind` from
    the unified taxonomy. Catches an extractor that emits kind=None and
    nobody noticing because the writer silently fills it in — and a
    classifier that returns a misspelled kind value."""
    nodes = _load_all_nodes(regen_kitchen_sink)
    assert nodes, "kitchen-sink fixture produced zero nodes"
    null_kind = [n["id"] for n in nodes if n.get("kind") is None]
    bad_kind = [(n["id"], n.get("kind")) for n in nodes if n.get("kind") not in _VALID_KINDS]
    assert not null_kind, f"{len(null_kind)} node(s) have kind=None: {null_kind[:5]}"
    assert not bad_kind, f"{len(bad_kind)} node(s) have unknown kind: {bad_kind[:5]}"


def test_primitive_default_rule_holds(regen_kitchen_sink):
    """When no classifier fires AND the extractor didn't set a kind, the
    writer must default kind to the primitive value (so kind == primitive
    for the "raw" tier of the taxonomy)."""
    nodes = _load_all_nodes(regen_kitchen_sink)
    mismatches = []
    for n in nodes:
        kind = n.get("kind")
        primitive = n.get("primitive")
        if kind in _CLASSIFIED_KINDS:
            continue  # classifier upgraded; primitive may differ from kind
        if kind != primitive:
            mismatches.append((n["id"], primitive, kind))
    assert not mismatches, (
        f"{len(mismatches)} non-classified node(s) have kind != primitive: "
        f"{mismatches[:5]}"
    )


def test_every_language_in_fixture_emits_at_least_one_node(regen_kitchen_sink):
    """Sanity gate: the kitchen-sink fixture spans Python + TypeScript + SQL.
    If any language drops to zero nodes between runs, the per-language
    extractor or its config likely broke — and the rest of these tests
    would silently pass for the wrong reason."""
    by_lang: dict[str, int] = {}
    for n in _load_all_nodes(regen_kitchen_sink):
        lang = n.get("source", {}).get("language")
        if lang:
            by_lang[lang] = by_lang.get(lang, 0) + 1
    for expected in ("python", "typescript", "sql"):
        assert by_lang.get(expected, 0) > 0, (
            f"expected {expected} primitives from the kitchen-sink fixture, "
            f"got 0 (full breakdown: {by_lang})"
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
        """rel-path → content for all node JSON files (excluding `_*` paths)."""
        result = {}
        root = base / "nodes"
        for p in root.rglob("*.json"):
            if p.name.startswith("_") or any(
                part.startswith("_") for part in p.relative_to(root).parts
            ):
                continue
            rel = str(p.relative_to(root))
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
