"""Tests for the test_kind classifier (Task 5.7)."""
from depgraph.lib.classification.engine import classify_corpus


def _fn(id_, name, path, decorators=None, edges_out=None):
    return {
        "id": id_, "primitive": "function", "name": name, "owner": None,
        "source": {"path": path, "line": 1, "end_line": 5,
                   "language": "python", "repo": "r"},
        "signature": {"decorators": decorators or []}, "attributes": {},
        "edges_out": edges_out or [],
        "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2,
    }


def test_function_with_tests_edge_is_test():
    """Primary signal: a `tests` edge outgoing classifies the function as test."""
    p = _fn("r::tests/test_foo.py::test_create", "test_create",
             "tests/test_foo.py",
             edges_out=[{"target": "r::services/foo.py::create",
                         "kind": "tests", "via": "assertion",
                         "where": "tests/test_foo.py:3", "confidence": "exact"}])
    decisions = classify_corpus([p])
    assert decisions[p["id"]].kind == "test"


def test_pytest_fixture_decorator_is_test():
    """pytest.fixture decorator classifies the function as test regardless of name."""
    p = _fn("r::conftest.py::db_session", "db_session", "conftest.py",
             decorators=["pytest.fixture"])
    decisions = classify_corpus([p])
    assert decisions[p["id"]].kind == "test"


def test_test_named_file_and_test_prefix_name_is_test():
    """Function in a test_*.py file whose name starts with 'test' is classified."""
    p = _fn("r::tests/test_auth.py::test_login_success", "test_login_success",
             "tests/test_auth.py")
    decisions = classify_corpus([p])
    assert decisions[p["id"]].kind == "test"


def test_helper_in_test_file_without_test_name_is_not_test():
    """Helper function in a test file but name doesn't start with 'test' — not test."""
    p = _fn("r::tests/test_auth.py::make_user", "make_user", "tests/test_auth.py")
    decisions = classify_corpus([p])
    assert decisions[p["id"]].kind != "test"


def test_dot_test_ts_file_with_test_name_is_test():
    """TypeScript *.test.ts file with a name starting 'test' classifies as test."""
    p = _fn("r::src/auth.test.ts::testLoginRedirect", "testLoginRedirect",
             "src/auth.test.ts")
    decisions = classify_corpus([p])
    assert decisions[p["id"]].kind == "test"
