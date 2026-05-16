from depgraph.lib.sql.parser import parse_operations, Operation


def test_create_table_emits_create_op():
    sql = """
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        email VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    ops = parse_operations(sql)
    assert len(ops) == 1
    op = ops[0]
    assert op.kind == "create_table"
    assert op.table == "users"
    assert op.columns == [
        {"name": "id", "type": "INTEGER", "nullable": True,
         "default": None, "primary_key": True},
        {"name": "email", "type": "VARCHAR(255)", "nullable": False,
         "default": None, "primary_key": False},
        {"name": "created_at", "type": "TIMESTAMP", "nullable": True,
         "default": "CURRENT_TIMESTAMP", "primary_key": False},
    ]


def test_create_table_if_not_exists():
    ops = parse_operations("CREATE TABLE IF NOT EXISTS foo (id INTEGER)")
    assert ops[0].kind == "create_table"
    assert ops[0].table == "foo"
    assert ops[0].if_not_exists is True


def test_foreign_key_recorded():
    sql = """
    CREATE TABLE event_crew (
        id INTEGER PRIMARY KEY,
        event_id INTEGER NOT NULL,
        FOREIGN KEY (event_id) REFERENCES events(id)
    )
    """
    op = parse_operations(sql)[0]
    assert op.foreign_keys == [
        {"column": "event_id", "references_table": "events", "references_column": "id"}
    ]


def test_alter_table_add_column():
    op = parse_operations("ALTER TABLE users ADD COLUMN role VARCHAR(50)")[0]
    assert op.kind == "alter_add_column"
    assert op.table == "users"
    assert op.column == {"name": "role", "type": "VARCHAR(50)", "nullable": True,
                          "default": None, "primary_key": False}


def test_alter_table_drop_column():
    op = parse_operations("ALTER TABLE users DROP COLUMN legacy_field")[0]
    assert op.kind == "alter_drop_column"
    assert op.table == "users"
    assert op.column_name == "legacy_field"


def test_alter_column_type():
    op = parse_operations(
        "ALTER TABLE users ALTER COLUMN email TYPE VARCHAR(255)",
        dialect="postgres",
    )[0]
    assert op.kind == "alter_column_type"
    assert op.table == "users"
    assert op.column_name == "email"
    assert "VARCHAR" in op.new_type.upper()


def test_alter_column_default():
    op = parse_operations(
        "ALTER TABLE users ALTER COLUMN role SET DEFAULT 'member'",
        dialect="postgres",
    )[0]
    assert op.kind == "alter_column_default"
    assert op.column_name == "role"
    assert "member" in (op.new_default or "")


def test_alter_column_drop_not_null():
    op = parse_operations(
        "ALTER TABLE users ALTER COLUMN email DROP NOT NULL",
        dialect="postgres",
    )[0]
    assert op.kind == "alter_column_nullable"
    assert op.new_nullable is True


def test_rename_column():
    op = parse_operations(
        "ALTER TABLE users RENAME COLUMN email_addr TO email",
        dialect="postgres",
    )[0]
    assert op.kind == "rename_column"
    assert op.column_name == "email_addr"
    assert op.new_column_name == "email"


def test_drop_table():
    op = parse_operations("DROP TABLE old_audit_log")[0]
    assert op.kind == "drop_table"
    assert op.table == "old_audit_log"


def test_create_index():
    op = parse_operations("CREATE INDEX idx_users_email ON users(email)")[0]
    assert op.kind == "create_index"
    assert op.index_name == "idx_users_email"
    assert op.table == "users"
    assert op.columns_indexed == ["email"]


def test_multiple_statements_in_one_string():
    sql = """
    CREATE TABLE a (id INTEGER);
    CREATE TABLE b (id INTEGER);
    """
    ops = parse_operations(sql)
    assert [op.table for op in ops] == ["a", "b"]


def test_select_statement_returns_empty_for_ddl_parser():
    """Parser is DDL-focused; SELECTs return no operations.
    The db_access logic uses a different parse path for SELECT/UPDATE/etc."""
    ops = parse_operations("SELECT * FROM users")
    assert ops == []
