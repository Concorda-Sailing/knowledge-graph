from pathlib import Path
from depgraph.lib.sql.migration import (
    is_migration_file, extract_migration, MigrationFile,
)

FIXTURES = Path(__file__).parent / "fixtures" / "migrations"


def test_recognizes_numbered_migration():
    assert is_migration_file(FIXTURES / "001_create_users.py") is True


def test_recognizes_unnumbered_migration_with_sql():
    assert is_migration_file(FIXTURES / "add_unnumbered_thing.py") is True


def test_rejects_non_migration_python():
    """A Python file outside a migrations/ directory or without text() calls."""
    p = FIXTURES.parent / "not_a_migration.py"
    p.write_text("def foo(): return 1\n")
    try:
        assert is_migration_file(p) is False
    finally:
        p.unlink()


def test_extract_migration_order_from_prefix():
    m = extract_migration(FIXTURES / "001_create_users.py")
    assert m.migration_order == 1
    assert m.operations[0].kind == "create_table"
    assert m.operations[0].table == "users"


def test_extract_migration_order_null_for_unnumbered():
    m = extract_migration(FIXTURES / "add_unnumbered_thing.py")
    assert m.migration_order is None
    assert m.operations[0].kind == "alter_add_column"


def test_extract_records_text_call_line():
    m = extract_migration(FIXTURES / "001_create_users.py")
    # The text(...) call is on line 5 in the fixture
    assert m.operations[0].source_line >= 5
    assert m.operations[0].source_line <= 12  # within the text(...) block


def test_dynamic_sql_recorded_as_warning_not_parsed():
    m = extract_migration(FIXTURES / "004_dynamic_sql.py")
    assert m.operations == []
    assert any("dynamic" in w.lower() or "interpolation" in w.lower()
               for w in m.warnings)
