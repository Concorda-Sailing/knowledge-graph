from pathlib import Path
from depgraph.lib.sql.migration import (
    is_migration_file, extract_migration, MigrationFile,
)

FIXTURES = Path(__file__).parent / "fixtures" / "migrations"
VAR_FIXTURES = Path(__file__).parent / "fixtures" / "migrations_var"


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


def test_variable_sql_resolves_module_level_binding():
    """`var = "CREATE TABLE ..."; text(var)` resolves through the
    module-level binding instead of dropping the schema as dynamic SQL."""
    m = extract_migration(VAR_FIXTURES / "005_variable_sql.py")
    assert m.warnings == []
    assert len(m.operations) == 1
    assert m.operations[0].kind == "create_table"
    assert m.operations[0].table == "accounts"


def test_variable_sql_skips_rebound_name():
    """A name assigned more than once at module scope is ambiguous —
    drop the binding and surface the dynamic-SQL warning."""
    m = extract_migration(VAR_FIXTURES / "006_rebound_var.py")
    assert m.operations == []
    assert any("unresolved name 'DDL'" in w for w in m.warnings), m.warnings


def test_variable_sql_resolves_ann_assign():
    """`var: str = "..."` (AnnAssign) is recognized alongside plain Assign."""
    m = extract_migration(VAR_FIXTURES / "007_typed_var.py")
    assert m.warnings == []
    assert len(m.operations) == 1
    assert m.operations[0].kind == "create_table"
    assert m.operations[0].table == "invites"
