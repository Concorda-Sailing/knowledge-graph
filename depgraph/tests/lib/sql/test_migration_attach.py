from pathlib import Path
from depgraph.lib.sql.migration import extract_migration
from depgraph.lib.sql.reconcile import reconcile_schema, schema_to_primitives
from depgraph.lib.sql.attach import attach_migration_attributes

FIXTURES = Path(__file__).parent / "fixtures" / "migrations"


def test_migration_module_gets_order_and_up_operations():
    # A synthetic module primitive as the Python extractor would emit
    module_prim = {
        "schema_version": 2,
        "id": "fixture::001_create_users.py",
        "primitive": "module",
        "name": "001_create_users.py",
        "owner": None,
        "source": {"repo": "fixture", "path": "001_create_users.py",
                   "language": "python", "line": 1, "end_line": 10},
        "signature": {}, "attributes": {},
        "edges_out": [], "structural_hash": "0", "kind": None,
        "extractor": "test",
    }
    migrations = [extract_migration(FIXTURES / "001_create_users.py")]
    schemas = reconcile_schema(migrations, repo_key="fixture")
    schema_prims = schema_to_primitives(schemas)

    attach_migration_attributes(
        primitives=[module_prim] + schema_prims,
        migrations=migrations,
    )

    assert module_prim["attributes"].get("migration_order") == 1
    up_ops = module_prim["attributes"].get("up_operations", [])
    assert any("schema::users" in oid for oid in up_ops), up_ops
