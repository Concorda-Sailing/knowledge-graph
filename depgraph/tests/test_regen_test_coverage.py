"""End-to-end regen pass test for Option-C test coverage (#52).

The unit tests in `lib/test_test_coverage.py` exercise the walker in
isolation; this file verifies that `kg depgraph regen` actually runs
the coverage pass and writes the index + per-node stamps as part of
the standard regen flow.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _make_project_with_tests(tmp_path: Path) -> tuple[Path, Path]:
    """Build a tiny project: one production module + one test file.

    The test file lives under `tests/` and is excluded from production
    extraction via `exclude_paths`. Returns (data_dir, repo_path).
    """
    repo = tmp_path / "api"
    (repo / "src").mkdir(parents=True)
    (repo / "tests").mkdir()

    (repo / "src" / "widget.py").write_text(
        "WIDGET_DEFAULT = 'default'\n"
        "\n"
        "def make_widget(name=WIDGET_DEFAULT):\n"
        "    return {'name': name}\n"
    )
    (repo / "src" / "uncovered.py").write_text(
        "def lonely():\n    return 42\n"
    )
    (repo / "tests" / "test_widget.py").write_text(
        "from src.widget import make_widget, WIDGET_DEFAULT\n"
        "\n"
        "def test_default():\n"
        "    assert make_widget()['name'] == WIDGET_DEFAULT\n"
    )

    data_dir = tmp_path / "project"
    data_dir.mkdir()
    (data_dir / "project.toml").write_text(
        f'[repos.api]\n'
        f'path = "{repo}"\n'
        f'languages = ["python"]\n'
        f'exclude_paths = ["**/tests/**"]\n'
    )
    return data_dir, repo


def _run_regen(data_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable, "-m", "kg.cli",
            "depgraph", "--data-dir", str(data_dir),
            "regen",
        ],
        capture_output=True, text=True, timeout=180,
    )


def test_regen_writes_test_coverage_json(tmp_path: Path):
    data_dir, _repo = _make_project_with_tests(tmp_path)
    r = _run_regen(data_dir)
    assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"

    coverage_path = data_dir / "depgraph" / "test_coverage.json"
    assert coverage_path.exists(), (
        f"test_coverage.json was not written; stdout={r.stdout}"
    )

    payload = json.loads(coverage_path.read_text())
    assert payload["schema_version"] == "1"
    assert payload["stats"]["test_files_scanned"] >= 1
    assert payload["stats"]["tested_nodes"] >= 1
    assert 0.0 < payload["stats"]["tested_node_ratio"] <= 1.0

    mapping = payload["production_to_tests"]
    assert "api::src/widget.py::make_widget" in mapping
    # The lonely module isn't imported by any test.
    assert "api::src/uncovered.py::lonely" not in mapping


def test_regen_stamps_tested_by_count_on_covered_nodes(tmp_path: Path):
    data_dir, _repo = _make_project_with_tests(tmp_path)
    r = _run_regen(data_dir)
    assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"

    # Find the covered function's node JSON.
    nodes_dir = data_dir / "depgraph" / "nodes"
    found_covered = False
    found_uncovered_without_field = False
    for jf in nodes_dir.rglob("*.json"):
        if jf.name.startswith("_") or jf.parent.name == "_index":
            continue
        try:
            node = json.loads(jf.read_text())
        except json.JSONDecodeError:
            continue
        nid = node.get("id")
        if nid == "api::src/widget.py::make_widget":
            assert node.get("tested_by_count") == 1, (
                f"covered node missing/wrong tested_by_count: "
                f"{node.get('tested_by_count')}"
            )
            found_covered = True
        if nid == "api::src/uncovered.py::lonely":
            # Uncovered nodes must NOT carry tested_by_count: the
            # absence of the field is the signal.
            assert "tested_by_count" not in node, (
                f"uncovered node has stray tested_by_count: {node}"
            )
            found_uncovered_without_field = True

    assert found_covered, "covered node never seen on disk"
    assert found_uncovered_without_field, "uncovered node never seen on disk"


def test_regen_test_coverage_stats_in_meta(tmp_path: Path):
    """The _meta.json should surface the same stats — health/dossier-rank
    readers shouldn't need to load test_coverage.json just to know how
    many test files were scanned."""
    data_dir, _repo = _make_project_with_tests(tmp_path)
    r = _run_regen(data_dir)
    assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"

    meta_path = data_dir / "depgraph" / "nodes" / "_meta.json"
    meta = json.loads(meta_path.read_text())
    stats = meta.get("test_coverage_stats")
    assert stats is not None, "test_coverage_stats missing from _meta.json"
    assert stats["test_files_scanned"] >= 1
    assert stats["tested_nodes"] >= 1
