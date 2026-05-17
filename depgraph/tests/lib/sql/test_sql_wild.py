"""Phase 4 wild corpus — 8 pathological SQL/migration fixtures.

Each fixture lives under depgraph/tests/fixtures/wild/sql/<name>/ with:
  README.md       — description of the tricky pattern
  src/migrations/ — Python migration files (or .sql for bare_sql_file)
  expected.json   — predicted schema + warning flags
  verification.md — pre-read prediction + post-run verdict

Fixtures with expected.json["skip_reason"] are skipped via pytest.skip()
to document out-of-scope behaviour without pretending it works.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from depgraph.lib.sql.migration import extract_migration, is_migration_file
from depgraph.lib.sql.reconcile import reconcile_schema

WILD_DIR = Path(__file__).parent.parent.parent / "fixtures" / "wild" / "sql"


def _fixtures():
    return sorted(d for d in WILD_DIR.iterdir() if d.is_dir() and (d / "src").exists())


@pytest.mark.parametrize("fixture", _fixtures(), ids=lambda f: f.name)
def test_wild_schema_matches_expected(fixture):
    expected = json.loads((fixture / "expected.json").read_text())
    if expected.get("skip_reason"):
        pytest.skip(expected["skip_reason"])
    src = fixture / "src"
    migrations = [
        extract_migration(p)
        for p in sorted(src.rglob("*.py"))
        if is_migration_file(p)
    ]
    tables = reconcile_schema(migrations, repo_key="fixture")
    actual = {t.name: t for t in tables}
    expected_tables = {t["name"]: t for t in expected.get("tables", [])}
    assert set(actual) == set(expected_tables), (
        f"{fixture.name}: tables mismatch: actual={set(actual)} "
        f"expected={set(expected_tables)}"
    )
    for name, t_actual in actual.items():
        t_expected = expected_tables[name]
        actual_cols = {c["name"] for c in t_actual.columns}
        expected_cols = set(t_expected["columns"])
        assert actual_cols == expected_cols, (
            f"{fixture.name}/{name}: columns mismatch: "
            f"actual={actual_cols} expected={expected_cols}"
        )


@pytest.mark.parametrize("fixture", _fixtures(), ids=lambda f: f.name)
def test_wild_warnings_match_expected(fixture):
    expected = json.loads((fixture / "expected.json").read_text())
    if expected.get("skip_reason"):
        pytest.skip(expected["skip_reason"])
    expected_warnings = expected.get("expect_warnings", False)
    src = fixture / "src"
    migrations = [
        extract_migration(p)
        for p in sorted(src.rglob("*.py"))
        if is_migration_file(p)
    ]
    has_warnings = any(m.warnings for m in migrations)
    if expected_warnings:
        assert has_warnings, f"{fixture.name}: expected warnings but got none"
    else:
        assert not has_warnings, (
            f"{fixture.name}: expected no warnings but got: "
            + "; ".join(w for m in migrations for w in m.warnings)
        )
