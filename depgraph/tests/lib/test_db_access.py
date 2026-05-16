from pathlib import Path
from depgraph.extractors.python.extract import extract_repo
from depgraph.lib.sql.cross_ref import attach_model_schema_references
from depgraph.lib.system_stub.db_access import attach_db_access_edges

FIXTURE = Path(__file__).parent / "test_db_access_fixtures"


def _setup_corpus():
    """Extract Python primitives + add a schema primitive for the users table."""
    py_prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE))
    schema_prim = {
        "id": "fixture::schema::users", "primitive": "class", "name": "users",
        "owner": None,
        "source": {"repo": "fixture", "path": "schema/users",
                   "language": "sql", "line": 1, "end_line": 1},
        "signature": {}, "attributes": {}, "edges_out": [],
        "structural_hash": "0", "kind": "schema",
        "extractor": "test", "schema_version": 2,
    }
    all_prims = py_prims + [schema_prim]
    attach_model_schema_references(all_prims)
    return all_prims


def test_session_query_targets_schema_primitive():
    prims = _setup_corpus()
    attach_db_access_edges(prims, repo_path=FIXTURE)
    fn = next(p for p in prims if p["name"] == "get_user")
    dba = [e for e in fn["edges_out"] if e["kind"] == "db_access"]
    targets = {e["target"] for e in dba}
    assert "fixture::schema::users" in targets


def test_session_add_targets_schema_primitive_via_inferred_type():
    """`session.add(user)` -- `user` is a function parameter typed `User`.
    Resolve via the parameter annotation if present; otherwise emit
    unresolved with the function name as `via`."""
    prims = _setup_corpus()
    attach_db_access_edges(prims, repo_path=FIXTURE)
    fn = next(p for p in prims if p["name"] == "save_user")
    dba = [e for e in fn["edges_out"] if e["kind"] == "db_access"]
    # save_user's `user` param has no type annotation in the fixture, so
    # session.add(user) resolves as unresolved.
    add_edges = [e for e in dba if "add" in e["via"]]
    assert any(e["confidence"] == "unresolved" for e in add_edges)


def test_orphan_query_target_emits_unresolved(tmp_path):
    """session.query(NotInCorpus) -- emit edge with confidence=unresolved.

    Uses pytest's tmp_path so the test doesn't mutate the committed fixture
    dir and can run concurrently with sibling tests."""
    import shutil
    work = tmp_path / "fixture"
    shutil.copytree(FIXTURE, work)
    (work / "misc.py").write_text(
        "def strange_query(session):\n"
        "    return session.query(NoSuchClass).all()\n"
    )

    py_prims = list(extract_repo(repo_key="fixture", repo_path=work))
    schema_prim = {
        "id": "fixture::schema::users", "primitive": "class", "name": "users",
        "owner": None,
        "source": {"repo": "fixture", "path": "schema/users",
                   "language": "sql", "line": 1, "end_line": 1},
        "signature": {}, "attributes": {}, "edges_out": [],
        "structural_hash": "0", "kind": "schema",
        "extractor": "test", "schema_version": 2,
    }
    all_prims = py_prims + [schema_prim]
    attach_model_schema_references(all_prims)
    attach_db_access_edges(all_prims, repo_path=work)

    fn = next(p for p in all_prims if p["name"] == "strange_query")
    dba = [e for e in fn["edges_out"] if e["kind"] == "db_access"]
    assert any(e["confidence"] == "unresolved" for e in dba)
