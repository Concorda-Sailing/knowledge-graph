"""Tests for repo-level include_paths / exclude_paths.

Wired through project.toml (`lib.config.project_repos`), threaded by
`lib.cli.regen._extract_python`, and applied in
`extractors.python.extract._iter_py_files`.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from depgraph.extractors.python.extract import _iter_py_files, extract_repo
from depgraph.lib.config import _load_project_config_cached, project_repos


# ---------------------------------------------------------------------------
# _iter_py_files
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_repo(tmp_path):
    """Layout:
        repo/
          api/routers.py
          api/services.py
          tests/test_routers.py
          tests/helpers/conftest.py
          docs/example.py        # not source
          scripts/migrate.py
          .venv/site-packages/lib.py   # hardcoded-skip
    """
    repo = tmp_path / "repo"
    for rel in [
        "api/routers.py",
        "api/services.py",
        "tests/test_routers.py",
        "tests/helpers/conftest.py",
        "docs/example.py",
        "scripts/migrate.py",
        ".venv/site-packages/lib.py",
    ]:
        f = repo / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("# empty\n")
    return repo


def _rels(files, repo):
    return sorted(str(f.relative_to(repo)) for f in files)


def test_iter_py_files_default_skips_hardcoded_dirs(sample_repo):
    rels = _rels(_iter_py_files(sample_repo), sample_repo)
    assert ".venv/site-packages/lib.py" not in rels
    assert set(rels) == {
        "api/routers.py", "api/services.py",
        "tests/test_routers.py", "tests/helpers/conftest.py",
        "docs/example.py", "scripts/migrate.py",
    }


def test_exclude_paths_skips_matching_tests_subtree(sample_repo):
    rels = _rels(
        _iter_py_files(sample_repo, exclude_paths=["**/tests/**"]),
        sample_repo,
    )
    assert all("/tests/" not in r and not r.startswith("tests/") for r in rels), rels
    assert "api/routers.py" in rels
    assert "scripts/migrate.py" in rels


def test_exclude_paths_matches_nested_dirs(sample_repo):
    """`**/tests/**` matches the nested `tests/helpers/conftest.py` too."""
    rels = _rels(
        _iter_py_files(sample_repo, exclude_paths=["**/tests/**"]),
        sample_repo,
    )
    assert "tests/helpers/conftest.py" not in rels


def test_include_paths_restricts_to_api_subtree(sample_repo):
    rels = _rels(
        _iter_py_files(sample_repo, include_paths=["api/**"]),
        sample_repo,
    )
    assert set(rels) == {"api/routers.py", "api/services.py"}


def test_include_and_exclude_compose(sample_repo):
    """Include narrows first, then exclude removes from the narrowed set."""
    rels = _rels(
        _iter_py_files(
            sample_repo,
            include_paths=["api/**", "tests/**"],
            exclude_paths=["**/tests/**"],
        ),
        sample_repo,
    )
    assert set(rels) == {"api/routers.py", "api/services.py"}


def test_extract_repo_threads_filters(sample_repo):
    """End-to-end: extract_repo with exclude_paths drops test-module primitives."""
    prims_all = list(extract_repo(repo_key="repo", repo_path=sample_repo))
    mod_paths_all = {p["source"]["path"] for p in prims_all if p["primitive"] == "module"}
    assert any(p.startswith("tests/") for p in mod_paths_all)

    prims_filtered = list(extract_repo(
        repo_key="repo",
        repo_path=sample_repo,
        exclude_paths=["**/tests/**"],
    ))
    mod_paths_filtered = {p["source"]["path"] for p in prims_filtered if p["primitive"] == "module"}
    assert not any(p.startswith("tests/") or "/tests/" in p for p in mod_paths_filtered)


# ---------------------------------------------------------------------------
# project_repos pulls include/exclude_paths through from project.toml
# ---------------------------------------------------------------------------

def test_project_repos_passes_through_path_filters(tmp_path):
    """project.toml [repos.<key>] include_paths/exclude_paths reach project_repos()."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "project.toml").write_text(
        '[project]\nname = "p"\n'
        '[repos.api]\npath = "/tmp"\n'
        'include_paths = ["api/**"]\n'
        'exclude_paths = ["**/tests/**", "**/migrations/**"]\n'
    )
    _load_project_config_cached.cache_clear()
    try:
        repos = project_repos(data_dir)
    finally:
        _load_project_config_cached.cache_clear()
    assert repos["api"]["include_paths"] == ["api/**"]
    assert repos["api"]["exclude_paths"] == ["**/tests/**", "**/migrations/**"]


def test_project_repos_defaults_path_filters_empty(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "project.toml").write_text(
        '[project]\nname = "p"\n'
        '[repos.api]\npath = "/tmp"\n'
    )
    _load_project_config_cached.cache_clear()
    try:
        repos = project_repos(data_dir)
    finally:
        _load_project_config_cached.cache_clear()
    assert repos["api"]["include_paths"] == []
    assert repos["api"]["exclude_paths"] == []
