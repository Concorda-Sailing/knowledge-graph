from pathlib import Path
from depgraph.lib.sql.migration import extract_migration
from depgraph.lib.sql.reconcile import reconcile_schema, SchemaPrimitive

FIXTURES = Path(__file__).parent / "fixtures" / "migrations"


def _load_all():
    files = sorted(FIXTURES.glob("*.py"))
    return [extract_migration(f) for f in files]


def test_create_table_produces_schema_primitive():
    migrations = _load_all()
    tables = {t.name: t for t in reconcile_schema(migrations, repo_key="fixture")}
    assert "users" in tables
    user = tables["users"]
    assert user.kind == "schema"
    assert {col["name"] for col in user.columns} == {"id", "email", "role", "bio"}


def test_alter_add_column_extends_table():
    migrations = _load_all()
    tables = {t.name: t for t in reconcile_schema(migrations, repo_key="fixture")}
    user = tables["users"]
    role = next(c for c in user.columns if c["name"] == "role")
    assert role["type"] == "VARCHAR(50)"


def test_unnumbered_migration_runs_after_ordered():
    """add_unnumbered_thing.py adds `bio` to users. It has no ordinal,
    so it runs after the ordered migrations. The final `users` table
    must include `bio`."""
    migrations = _load_all()
    tables = {t.name: t for t in reconcile_schema(migrations, repo_key="fixture")}
    bio = next(c for c in tables["users"].columns if c["name"] == "bio")
    assert bio["type"] == "TEXT"


def test_schema_primitive_id_shape():
    migrations = _load_all()
    tables = {t.name: t for t in reconcile_schema(migrations, repo_key="fixture")}
    user = tables["users"]
    assert user.id == "fixture::schema::users"


def test_schema_primitive_source_points_at_creating_migration():
    """The schema primitive's source.path is the migration that CREATE'd it.
    Later ALTER migrations are recorded as additional `defines` edges, but
    the primitive's source field stays anchored to its origin."""
    migrations = _load_all()
    tables = {t.name: t for t in reconcile_schema(migrations, repo_key="fixture")}
    user = tables["users"]
    assert user.source["path"].endswith("001_create_users.py")


def test_alter_column_type_updates_in_place():
    """A migration that runs `ALTER TABLE users ALTER COLUMN email TYPE VARCHAR(255)`
    should leave the final-state column with type VARCHAR(255)."""
    from depgraph.lib.sql.migration import MigrationFile, MigrationOperation
    from depgraph.lib.sql.parser import Operation, parse_operations
    base = MigrationFile(
        path=Path("/fake/001_init.py"), migration_order=1,
        operations=[MigrationOperation(
            operation=parse_operations(
                "CREATE TABLE users (id INTEGER PRIMARY KEY, email VARCHAR(64))"
            )[0],
            source_line=1, raw_sql="",
        )],
    )
    alter = MigrationFile(
        path=Path("/fake/002_widen.py"), migration_order=2,
        operations=[MigrationOperation(
            operation=Operation(kind="alter_column_type", table="users",
                                  column_name="email", new_type="VARCHAR(255)"),
            source_line=1, raw_sql="",
        )],
    )
    tables = {t.name: t for t in reconcile_schema([base, alter], repo_key="fixture")}
    email = next(c for c in tables["users"].columns if c["name"] == "email")
    assert email["type"] == "VARCHAR(255)"


def test_drop_column_garbage_collects_index_and_fk():
    """Dropping a column removes any index/FK that referenced it."""
    from depgraph.lib.sql.migration import MigrationFile, MigrationOperation
    from depgraph.lib.sql.parser import Operation
    create = MigrationFile(
        path=Path("/fake/001_init.py"), migration_order=1,
        operations=[MigrationOperation(
            operation=Operation(
                kind="create_table", table="users",
                columns=[{"name": "id", "type": "INTEGER", "nullable": False,
                            "default": None, "primary_key": True},
                          {"name": "team_id", "type": "INTEGER", "nullable": True,
                            "default": None, "primary_key": False}],
                foreign_keys=[{"column": "team_id", "references_table": "teams",
                                 "references_column": "id"}],
            ),
            source_line=1, raw_sql="",
        )],
    )
    add_idx = MigrationFile(
        path=Path("/fake/002_idx.py"), migration_order=2,
        operations=[MigrationOperation(
            operation=Operation(kind="create_index", index_name="idx_users_team",
                                  table="users", columns_indexed=["team_id"]),
            source_line=1, raw_sql="",
        )],
    )
    drop_col = MigrationFile(
        path=Path("/fake/003_drop.py"), migration_order=3,
        operations=[MigrationOperation(
            operation=Operation(kind="alter_drop_column", table="users",
                                  column_name="team_id"),
            source_line=1, raw_sql="",
        )],
    )
    tables = {t.name: t for t in reconcile_schema(
        [create, add_idx, drop_col], repo_key="fixture")}
    users = tables["users"]
    assert all(c["name"] != "team_id" for c in users.columns)
    assert users.indexes == [], f"orphan index left behind: {users.indexes}"
    assert users.foreign_keys == [], f"dangling FK left behind: {users.foreign_keys}"


def test_drop_table_clears_incoming_fks():
    """Dropping a referenced table removes FKs pointing at it from other tables."""
    from depgraph.lib.sql.migration import MigrationFile, MigrationOperation
    from depgraph.lib.sql.parser import Operation
    create_teams = MigrationFile(
        path=Path("/fake/001.py"), migration_order=1,
        operations=[MigrationOperation(
            operation=Operation(kind="create_table", table="teams",
                                  columns=[{"name": "id", "type": "INTEGER",
                                              "nullable": False, "default": None,
                                              "primary_key": True}]),
            source_line=1, raw_sql="",
        )],
    )
    create_users = MigrationFile(
        path=Path("/fake/002.py"), migration_order=2,
        operations=[MigrationOperation(
            operation=Operation(kind="create_table", table="users",
                                  columns=[{"name": "id", "type": "INTEGER",
                                              "nullable": False, "default": None,
                                              "primary_key": True},
                                            {"name": "team_id", "type": "INTEGER",
                                              "nullable": True, "default": None,
                                              "primary_key": False}],
                                  foreign_keys=[{"column": "team_id",
                                                   "references_table": "teams",
                                                   "references_column": "id"}]),
            source_line=1, raw_sql="",
        )],
    )
    drop_teams = MigrationFile(
        path=Path("/fake/003.py"), migration_order=3,
        operations=[MigrationOperation(
            operation=Operation(kind="drop_table", table="teams"),
            source_line=1, raw_sql="",
        )],
    )
    tables = {t.name: t for t in reconcile_schema(
        [create_teams, create_users, drop_teams], repo_key="fixture")}
    assert "teams" not in tables
    assert tables["users"].foreign_keys == []


# ── Task 4.4 tests (schema_to_primitives) ──────────────────────────────────
from depgraph.lib.sql.reconcile import schema_to_primitives


def test_schema_to_primitives_table_class_plus_column_variables():
    migrations = _load_all()
    tables = reconcile_schema(migrations, repo_key="fixture")
    prims = schema_to_primitives(tables)
    # One class per table
    classes = [p for p in prims if p["primitive"] == "class"]
    assert {p["name"] for p in classes} == {"users"}
    # One variable per column (id, email, role, bio)
    variables = [p for p in prims if p["primitive"] == "variable"]
    assert {p["name"] for p in variables} == {
        "users.id", "users.email", "users.role", "users.bio",
    }
    # Column variables owned by table class
    email = next(v for v in variables if v["name"] == "users.email")
    assert email["owner"] == "fixture::schema::users"
    assert email["signature"]["type_annotation"] == "VARCHAR(255)"
    assert email["attributes"]["nullable"] is False


def test_table_primitive_has_kind_schema():
    migrations = _load_all()
    tables = reconcile_schema(migrations, repo_key="fixture")
    prims = schema_to_primitives(tables)
    classes = [p for p in prims if p["primitive"] == "class"]
    assert all(p["kind"] == "schema" for p in classes)


def test_column_primitive_id_format():
    migrations = _load_all()
    tables = reconcile_schema(migrations, repo_key="fixture")
    prims = schema_to_primitives(tables)
    email = next(p for p in prims if p["name"] == "users.email")
    assert email["id"] == "fixture::schema::users.email"


# ── Task 4.8: Schema validation sweep ─────────────────────────────────────────
from depgraph.lib.primitives import validate_primitive


def test_all_schema_primitives_validate():
    migrations = _load_all()
    tables = reconcile_schema(migrations, repo_key="fixture")
    prims = schema_to_primitives(tables)
    for p in prims:
        errors = validate_primitive(p)
        assert not errors, f"{p['id']}: {errors}"
