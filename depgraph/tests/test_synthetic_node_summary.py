"""Unit tests for `_synthetic_node_summary` — the day-zero search surface.

Each node gets a brief textual summary embedded alongside any dossier
body, so semantic search has something to grip on a fresh corpus that
hasn't been hand-dossiered yet (#37).
"""
from __future__ import annotations

from depgraph.extractors.reconcile import _synthetic_node_summary


def _node(**overrides) -> dict:
    base: dict = {
        "id": "api::models/foo.py::Foo",
        "primitive": "class",
        "kind": "model",
        "name": "Foo",
        "owner": None,
        "source": {
            "repo": "api", "path": "models/foo.py",
            "language": "python", "line": 1, "end_line": 10,
        },
        "signature": {},
        "attributes": {},
        "edges_out": [],
    }
    base.update(overrides)
    return base


def test_summary_includes_id_kind_and_path():
    out = _synthetic_node_summary(_node())
    assert "api::models/foo.py::Foo" in out
    assert "kind: model" in out
    assert "path: api/models/foo.py" in out


def test_summary_skips_packages():
    """Package primitives are directory groupings — their member modules
    already cover the textual surface; indexing the package itself only
    adds noise."""
    pkg = _node(primitive="package", id="api::models", name="models",
                kind=None, source={"repo": "api", "path": "models",
                                     "language": "python", "line": 0, "end_line": 0})
    assert _synthetic_node_summary(pkg) is None


def test_summary_includes_function_signature():
    fn = _node(
        primitive="function", kind="service",
        id="api::services/user.py::create",
        name="create",
        signature={
            "parameters": [
                {"name": "email", "type_annotation": "str"},
                {"name": "password", "type_annotation": "str"},
            ],
            "return_type": "User",
            "is_async": True,
        },
    )
    out = _synthetic_node_summary(fn)
    assert "params: email, password" in out
    assert "returns User" in out


def test_summary_includes_docstring_when_present():
    fn = _node(signature={"docstring": "Create a new user from credentials."})
    out = _synthetic_node_summary(fn)
    assert "doc: Create a new user from credentials." in out


def test_summary_truncates_long_docstrings():
    fn = _node(signature={"docstring": "x" * 1000})
    out = _synthetic_node_summary(fn)
    # 400 chars from the docstring, plus a "doc: " prefix.
    assert "doc: " + "x" * 400 in out
    assert "x" * 401 not in out.split("doc: ", 1)[1]


def test_summary_returns_none_when_id_missing():
    assert _synthetic_node_summary({"primitive": "class"}) is None


def test_summary_omits_name_line_when_redundant_with_id():
    """`name: Foo` adds no signal when the id already ends in `::Foo`."""
    out = _synthetic_node_summary(_node())
    assert "name: Foo" not in out


def test_summary_includes_name_when_it_differs_from_id_tail():
    """Methods have id like `Foo.bar` but name `Foo.bar` (still equal) —
    but a module primitive might have name=basename and id=<key>::path,
    where the basename isn't the id tail."""
    mod = _node(
        primitive="module", kind="module",
        id="api::services/user.py",
        name="user",  # basename, differs from "services/user.py" tail
    )
    out = _synthetic_node_summary(mod)
    assert "name: user" in out
