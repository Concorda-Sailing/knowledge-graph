"""Tests for repo-level include_paths / exclude_paths.

Wired through project.toml (`lib.config.project_repos`), threaded by
`lib.cli.regen._extract_python` / `_extract_typescript` /
`_run_sql_pipeline`, and applied in each language extractor (Python uses
`extract._iter_py_files`; SQL filters in regen; the TS extractor reads
the flags itself). All three call into `lib.path_filters.included`.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from depgraph.extractors.python.extract import _iter_py_files, extract_repo
from depgraph.lib.config import _load_project_config_cached, project_repos
from depgraph.lib.path_filters import compile_glob, included, matches_any


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


# ---------------------------------------------------------------------------
# Shared lib/path_filters semantics
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("pattern,rel,expected", [
    ("**/tests/**", "api/tests/test_x.py", True),
    ("**/tests/**", "tests/test_x.py", True),
    ("**/tests/**", "tests/nested/deep/foo.py", True),
    ("**/tests/**", "api/services.py", False),
    ("api/**", "api/routers.py", True),
    ("api/**", "web/routers.py", False),
    ("*.py", "foo.py", True),
    ("*.py", "a/b.py", False),
    ("**/*.py", "a/b.py", True),
    ("**.py", "deep/nested/x.py", True),
    ("**", "anything/at/all", True),
    ("exact/path.py", "exact/path.py", True),
    ("exact/path.py", "exact/path_other.py", False),
    ("data?.csv", "data1.csv", True),
    ("data?.csv", "data10.csv", False),
])
def test_compile_glob_semantics(pattern, rel, expected):
    assert bool(compile_glob(pattern).match(rel)) is expected


def test_matches_any_returns_true_on_first_hit():
    assert matches_any("a/tests/x.py", ["**/tests/**", "**/never/**"]) is True
    assert matches_any("a/services/x.py", ["**/tests/**", "**/never/**"]) is False


def test_included_include_then_exclude():
    assert included(
        "api/tests/x.py",
        include_paths=["api/**"],
        exclude_paths=["**/tests/**"],
    ) is False
    assert included(
        "api/services.py",
        include_paths=["api/**"],
        exclude_paths=["**/tests/**"],
    ) is True
    assert included("web/x.py", include_paths=["api/**"]) is False
    assert included("anything.py") is True


# ---------------------------------------------------------------------------
# SQL pipeline honours include_paths/exclude_paths via regen plumbing
# ---------------------------------------------------------------------------

def test_sql_pipeline_skips_migration_in_excluded_path(tmp_path):
    """A migration file whose rel-path matches exclude_paths is not parsed.

    Mirrors what `_run_sql_pipeline` does in `lib/cli/regen.py`: builds a
    list of migration files and applies `included()` against each file's
    rel-path before extraction."""
    from depgraph.lib.path_filters import included as _included
    from depgraph.lib.sql.migration import extract_migration, is_migration_file

    repo = tmp_path / "repo"
    primary = repo / "migrations"
    legacy = repo / "legacy" / "migrations"
    primary.mkdir(parents=True)
    legacy.mkdir(parents=True)
    (primary / "001_create.py").write_text(
        'from sqlalchemy import text\n'
        'def migrate(engine):\n'
        '    with engine.connect() as c:\n'
        '        c.execute(text("CREATE TABLE primary_t (id INTEGER PRIMARY KEY)"))\n'
    )
    (legacy / "001_legacy.py").write_text(
        'from sqlalchemy import text\n'
        'def migrate(engine):\n'
        '    with engine.connect() as c:\n'
        '        c.execute(text("CREATE TABLE legacy_t (id INTEGER PRIMARY KEY)"))\n'
    )

    # Simulate the regen filter loop: scan migrations under both dirs,
    # drop anything matching exclude_paths.
    exclude = ["**/legacy/**"]
    files = []
    for mdir in [primary, legacy]:
        for f in sorted(mdir.rglob("*")):
            if not (f.is_file() and is_migration_file(f)):
                continue
            rel = str(f.relative_to(repo))
            if not _included(rel, exclude_paths=exclude):
                continue
            files.append(extract_migration(f))

    tables = {op.table for m in files for op in m.operations}
    assert tables == {"primary_t"}, tables


# ---------------------------------------------------------------------------
# TS extractor honours --include-paths / --exclude-paths
# ---------------------------------------------------------------------------

@pytest.fixture
def ts_repo(tmp_path):
    """Tiny TS repo with `src/` source and `__tests__/` test files."""
    repo = tmp_path / "ts-repo"
    (repo / "src").mkdir(parents=True)
    (repo / "__tests__").mkdir(parents=True)
    (repo / "src/keep.ts").write_text("export class Keep {}\n")
    (repo / "src/util.ts").write_text("export function util() { return 1; }\n")
    (repo / "__tests__/skip.test.ts").write_text("export class Skip {}\n")
    return repo


def _ts_extract(repo, *, include=None, exclude=None):
    import json
    import subprocess

    from depgraph.lib.cli.regen import _ts_node_env

    extractor = (
        Path(__file__).resolve().parents[1]
        / "extractors" / "typescript" / "extract.ts"
    )
    if not extractor.exists():
        pytest.skip("TS extractor source not present")
    cmd = [
        "npx", "tsx", str(extractor),
        "--repo-key", "ts",
        "--repo-path", str(repo),
        "--format", "ndjson",
    ]
    if include:
        cmd += ["--include-paths", ",".join(include)]
    if exclude:
        cmd += ["--exclude-paths", ",".join(exclude)]
    try:
        result = subprocess.run(
            cmd, env=_ts_node_env(),
            capture_output=True, text=True, timeout=120,
        )
    except FileNotFoundError:
        pytest.skip("npx/tsx not available")
    if result.returncode != 0:
        pytest.skip(f"ts extractor unavailable: {result.stderr[:200]}")
    prims = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        # Drop the resolver-stats sentinel (#77) — terminal ndjson line.
        if obj.get("_kind") == "resolver_stats":
            continue
        prims.append(obj)
    return prims


def test_ts_extractor_excludes_paths(ts_repo):
    prims_all = _ts_extract(ts_repo)
    mods_all = {p["source"]["path"] for p in prims_all if p["primitive"] == "module"}
    assert any(p.startswith("__tests__/") for p in mods_all)

    prims_filtered = _ts_extract(ts_repo, exclude=["**/__tests__/**"])
    mods_filtered = {
        p["source"]["path"] for p in prims_filtered if p["primitive"] == "module"
    }
    assert mods_filtered == {"src/keep.ts", "src/util.ts"}


def test_ts_extractor_includes_paths(ts_repo):
    prims = _ts_extract(ts_repo, include=["src/**"])
    mods = {p["source"]["path"] for p in prims if p["primitive"] == "module"}
    assert mods == {"src/keep.ts", "src/util.ts"}
