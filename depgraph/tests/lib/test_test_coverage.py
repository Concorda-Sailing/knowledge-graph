"""Unit tests for the Option-C test-coverage walker (issue #52)."""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from depgraph.extractors.python.extract import extract_repo
from depgraph.lib.test_coverage import (
    DEFAULT_TEST_PATTERNS,
    build_test_coverage_index,
    stamp_tested_by_count,
    write_test_coverage,
)


# ----------------------------------------------------------------------
# Synthetic-pin fixture exercise (issue #52, Option C verification step 1)
# ----------------------------------------------------------------------

FIXTURE_DIR = (
    Path(__file__).resolve().parents[1]
    / "fixtures" / "wild" / "test_coverage" / "basic_python"
)


def _extract_with_tests_excluded(repo_path: Path) -> list[dict]:
    """Mimic the production-graph configuration: tests live under
    `src/tests/` and are excluded from the corpus proper."""
    return list(extract_repo(
        repo_key="fixture",
        repo_path=repo_path,
        exclude_paths=["**/tests/**"],
    ))


def test_basic_python_fixture_extracts_only_production():
    """Production extraction with exclude_paths must NOT emit any
    primitives whose path lives under `src/tests/` — that's the
    "tests excluded from corpus by design" precondition #52 starts
    from."""
    prims = _extract_with_tests_excluded(FIXTURE_DIR)
    test_paths = [p["source"]["path"] for p in prims
                  if "tests/" in p["source"]["path"]]
    assert test_paths == [], (
        f"production extractor leaked test-file primitives: {test_paths}"
    )
    # Sanity: we DID emit production primitives.
    ids = {p["id"] for p in prims}
    assert "fixture::src/widget.py::make_widget" in ids
    assert "fixture::src/widget.py::WIDGET_DEFAULT" in ids
    assert "fixture::src/helpers.py::format_label" in ids


def test_basic_python_fixture_coverage_walker_maps_test_to_production():
    """End-to-end pin: production extraction + Option-C walker must
    produce the expected production-id → test-file mapping."""
    prims = _extract_with_tests_excluded(FIXTURE_DIR)
    payload = build_test_coverage_index(
        prims,
        repos=[{"key": "fixture", "path": FIXTURE_DIR,
                "languages": ["python"], "test_paths": None}],
    )
    mapping = payload["production_to_tests"]

    # The test file should cover the imported symbols.
    test_rel = "fixture::src/tests/test_widget.py"
    assert test_rel in mapping["fixture::src/widget.py::make_widget"]
    assert test_rel in mapping["fixture::src/widget.py::WIDGET_DEFAULT"]
    # And the module-level edge: importing FROM widget.py implicates
    # the module id at minimum (even when individual symbols resolve).
    # (Only the symbol-level edge is required; the module edge is best-
    # effort. We don't assert its absence either.)

    # Helpers.py is NOT imported by any test — must not appear in the
    # mapping at all.
    assert "fixture::src/helpers.py::format_label" not in mapping
    # The helpers MODULE id also shouldn't appear, since no test
    # imports it.
    assert "fixture::src/helpers.py" not in mapping


def test_basic_python_fixture_stats_match_expectation():
    prims = _extract_with_tests_excluded(FIXTURE_DIR)
    payload = build_test_coverage_index(
        prims,
        repos=[{"key": "fixture", "path": FIXTURE_DIR,
                "languages": ["python"], "test_paths": None}],
    )
    stats = payload["stats"]
    # One test file, under src/tests/.
    assert stats["test_files_scanned"] == 1
    # At least the two named symbols (and maybe the module) are tested.
    assert stats["tested_nodes"] >= 2
    # Ratio is between 0 and 1, derivable from the two prior fields.
    assert 0.0 < stats["tested_node_ratio"] <= 1.0


# ----------------------------------------------------------------------
# Schema / writer-level tests
# ----------------------------------------------------------------------


def test_schema_version_is_string():
    """`schema_version` is the contract — pin its type so a future
    rewrite that switches to int doesn't silently break consumers."""
    payload = build_test_coverage_index([], repos=[])
    assert payload["schema_version"] == "1"
    assert isinstance(payload["generated_at"], str)
    assert payload["production_to_tests"] == {}
    assert payload["stats"]["test_files_scanned"] == 0
    assert payload["stats"]["tested_nodes"] == 0
    assert payload["stats"]["tested_node_ratio"] == 0.0


def test_write_test_coverage_round_trips(tmp_path: Path):
    payload = build_test_coverage_index([], repos=[])
    out = write_test_coverage(tmp_path, payload)
    assert out == tmp_path / "test_coverage.json"
    loaded = json.loads(out.read_text())
    assert loaded["schema_version"] == "1"


def test_stamp_tested_by_count_only_stamps_covered_nodes():
    """Primitives without coverage must NOT get `tested_by_count: 0`.
    The absence of the field is itself the signal — see the helper's
    docstring for rationale."""
    prims = [
        {"id": "a", "primitive": "function"},
        {"id": "b", "primitive": "function"},
        {"id": "c", "primitive": "function"},
    ]
    payload = {"production_to_tests": {
        "a": ["repo::tests/t.py"],
        "b": ["repo::tests/t.py", "repo::tests/u.py"],
    }}
    n = stamp_tested_by_count(prims, payload)
    assert n == 2
    by_id = {p["id"]: p for p in prims}
    assert by_id["a"]["tested_by_count"] == 1
    assert by_id["b"]["tested_by_count"] == 2
    assert "tested_by_count" not in by_id["c"]


# ----------------------------------------------------------------------
# Walker resolution edge cases
# ----------------------------------------------------------------------


def test_walker_skips_non_python_repos():
    """A repo whose `languages` doesn't include 'python' must NOT have
    its test files walked — the Python walker is the only walker
    today, and a TS repo would otherwise look like 'zero tests scanned'
    even though the user wanted tests scanned."""
    payload = build_test_coverage_index(
        [],
        repos=[{"key": "ts-repo", "path": Path("/nonexistent"),
                "languages": ["typescript"], "test_paths": None}],
    )
    assert payload["stats"]["test_files_scanned"] == 0


def test_walker_honors_explicit_empty_test_paths(tmp_path: Path):
    """Setting `test_paths = []` in project.toml means 'scan no files
    for coverage' — must NOT fall through to the default globs."""
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "tests").mkdir()
    (repo / "src" / "lib.py").write_text("def f(): pass\n")
    (repo / "tests" / "test_lib.py").write_text(
        "from src.lib import f\n\ndef test_f(): assert f() is None\n"
    )
    prims = list(extract_repo(
        repo_key="r", repo_path=repo, exclude_paths=["**/tests/**"],
    ))
    payload = build_test_coverage_index(
        prims,
        repos=[{"key": "r", "path": repo, "languages": ["python"],
                "test_paths": []}],
    )
    assert payload["stats"]["test_files_scanned"] == 0
    assert payload["production_to_tests"] == {}


def test_walker_handles_broken_test_file(tmp_path: Path):
    """A syntactically-invalid test file must NOT abort the walker —
    one broken test must not erase coverage for every other test in
    the corpus."""
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "tests").mkdir()
    (repo / "src" / "lib.py").write_text("def f(): return 1\n")
    (repo / "tests" / "test_broken.py").write_text("def test_bad(:\n")  # SyntaxError
    (repo / "tests" / "test_good.py").write_text(
        "from src.lib import f\n\ndef test_f(): assert f() == 1\n"
    )
    prims = list(extract_repo(
        repo_key="r", repo_path=repo, exclude_paths=["**/tests/**"],
    ))
    payload = build_test_coverage_index(
        prims,
        repos=[{"key": "r", "path": repo, "languages": ["python"],
                "test_paths": None}],
    )
    assert payload["stats"]["test_files_scanned"] == 2
    assert "r::src/lib.py::f" in payload["production_to_tests"]


def test_walker_default_globs_match_common_layouts():
    """Sanity check that the default globs cover the common conventions
    listed in the project.toml schema docstring."""
    from depgraph.lib.path_filters import matches_any
    assert matches_any("tests/test_x.py", DEFAULT_TEST_PATTERNS)
    assert matches_any("src/tests/test_x.py", DEFAULT_TEST_PATTERNS)
    assert matches_any("pkg/test_helpers.py", DEFAULT_TEST_PATTERNS)
    assert matches_any("pkg/helpers_test.py", DEFAULT_TEST_PATTERNS)
    assert matches_any("web/__tests__/Button.test.py", DEFAULT_TEST_PATTERNS)
    # A production file at root should NOT match.
    assert not matches_any("lib.py", DEFAULT_TEST_PATTERNS)
    assert not matches_any("src/widget.py", DEFAULT_TEST_PATTERNS)


def test_walker_resolves_attribute_chain_through_module_import(tmp_path: Path):
    """`import pkg.mod` + `pkg.mod.Symbol(...)` must resolve to the
    Symbol primitive id, not just the module id."""
    repo = tmp_path / "repo"
    (repo / "pkg").mkdir(parents=True)
    (repo / "tests").mkdir()
    (repo / "pkg" / "__init__.py").write_text("")
    (repo / "pkg" / "mod.py").write_text("class Symbol:\n    pass\n")
    (repo / "tests" / "test_mod.py").write_text(
        "import pkg.mod\n\n"
        "def test_uses_symbol():\n"
        "    assert pkg.mod.Symbol() is not None\n"
    )
    prims = list(extract_repo(
        repo_key="r", repo_path=repo, exclude_paths=["**/tests/**"],
    ))
    payload = build_test_coverage_index(
        prims,
        repos=[{"key": "r", "path": repo, "languages": ["python"],
                "test_paths": None}],
    )
    mapping = payload["production_to_tests"]
    # The Symbol class id must appear, not just the module.
    assert "r::pkg/mod.py::Symbol" in mapping


def test_walker_resolves_src_layout_through_aliasing(tmp_path: Path):
    """`src/`-layout repos (pallets-click, etc.) install the package at
    its bare name — `src/click/__init__.py` is importable as `click`,
    not `src.click`. The production extractor stores the path-derived
    dotted name (`src.click`), so the walker must alias the stripped
    form back to find the right module. Without this, every `src/`-
    layout corpus reports zero coverage."""
    repo = tmp_path / "repo"
    (repo / "src" / "pkg").mkdir(parents=True)
    (repo / "tests").mkdir()
    (repo / "src" / "pkg" / "__init__.py").write_text(
        "def public_api():\n    return True\n"
    )
    (repo / "tests" / "test_pkg.py").write_text(
        "import pkg\n\n"
        "def test_api(): assert pkg.public_api()\n"
    )
    prims = list(extract_repo(
        repo_key="r", repo_path=repo, exclude_paths=["**/tests/**"],
    ))
    payload = build_test_coverage_index(
        prims,
        repos=[{"key": "r", "path": repo, "languages": ["python"],
                "test_paths": None}],
    )
    mapping = payload["production_to_tests"]
    # The package __init__ module id MUST be covered — the `import pkg`
    # statement implicates it directly.
    assert "r::src/pkg/__init__.py" in mapping
    # And the attribute walker should pick up `pkg.public_api`.
    assert "r::src/pkg/__init__.py::public_api" in mapping


def test_walker_resolves_relative_import_inside_repo(tmp_path: Path):
    """`from ..pkg.sub import X` inside a tests/ subdir must resolve
    relative to the test file's path, not to nothing."""
    repo = tmp_path / "repo"
    (repo / "src" / "tests").mkdir(parents=True)
    (repo / "src" / "lib.py").write_text("def utility(): return 1\n")
    (repo / "src" / "__init__.py").write_text("")
    (repo / "src" / "tests" / "__init__.py").write_text("")
    (repo / "src" / "tests" / "test_lib.py").write_text(
        "from ..lib import utility\n\n"
        "def test_u(): assert utility() == 1\n"
    )
    prims = list(extract_repo(
        repo_key="r", repo_path=repo, exclude_paths=["**/tests/**"],
    ))
    payload = build_test_coverage_index(
        prims,
        repos=[{"key": "r", "path": repo, "languages": ["python"],
                "test_paths": None}],
    )
    mapping = payload["production_to_tests"]
    assert "r::src/lib.py::utility" in mapping
