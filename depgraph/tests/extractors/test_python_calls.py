"""Tests for python extractor's call-edge resolution (calls / instantiates).

Regression coverage for issue #68: method-call branch of `_resolve_call_edge`
did not consult the per-file imports table when the receiver was a bare
module name like `requests.get(...)`. The edge collapsed to
`external::unresolved::requests.get` instead of the canonical
`external::pypi::requests::get`.

Issue #51 already covered typed-receiver resolution (`db: Session = ...`);
this file pins the imports-fallback branch for module-named receivers.
"""
from __future__ import annotations

from pathlib import Path

from depgraph.extractors.python.extract import extract_repo


def _write(root: Path, rel: str, content: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)


def _call_edges_from_function(primitives: list[dict], *, path: str,
                                name: str) -> list[dict]:
    """Return calls/instantiates edges emitted by a function primitive."""
    for p in primitives:
        if (p["primitive"] == "function"
                and p["source"]["path"] == path
                and p["name"] == name):
            return [e for e in p["edges_out"]
                    if e["kind"] in {"calls", "instantiates"}]
    raise AssertionError(
        f"function {name!r} in {path!r} not found in primitives"
    )


def test_module_named_receiver_resolves_via_imports(tmp_path: Path) -> None:
    """`import requests; requests.get(...)` inside a function should emit
    a calls edge with target `external::pypi::requests::get` and
    `confidence == 'exact'`, not `external::unresolved::requests.get`."""
    _write(tmp_path, "consumer.py",
           "import requests\n"
           "\n"
           "def fetch():\n"
           "    return requests.get('/x')\n")

    primitives = list(extract_repo(repo_key="r", repo_path=tmp_path))

    edges = _call_edges_from_function(primitives, path="consumer.py",
                                       name="fetch")
    targets = [e["target"] for e in edges]
    assert "external::pypi::requests::get" in targets, (
        f"expected external::pypi::requests::get, got {targets!r}"
    )
    edge = next(e for e in edges
                if e["target"] == "external::pypi::requests::get")
    assert edge["confidence"] == "exact"
    assert edge["kind"] == "calls"
    assert edge["via"] == "method_call"


def test_aliased_module_receiver_resolves_via_imports(tmp_path: Path) -> None:
    """`import numpy as np; np.array(...)` resolves to the underlying
    package via the local-binding name (np), not the alias text."""
    _write(tmp_path, "consumer.py",
           "import numpy as np\n"
           "\n"
           "def make():\n"
           "    return np.array([1, 2, 3])\n")

    primitives = list(extract_repo(repo_key="r", repo_path=tmp_path))

    edges = _call_edges_from_function(primitives, path="consumer.py",
                                       name="make")
    targets = [e["target"] for e in edges]
    assert "external::pypi::numpy::array" in targets, (
        f"expected external::pypi::numpy::array, got {targets!r}"
    )
    edge = next(e for e in edges
                if e["target"] == "external::pypi::numpy::array")
    assert edge["confidence"] == "exact"


def test_unknown_receiver_still_unresolved(tmp_path: Path) -> None:
    """Pre-existing fallback preserved: a receiver name that is neither a
    typed variable nor an imported binding still emits the
    `external::unresolved::<recv>.<method>` sentinel."""
    _write(tmp_path, "consumer.py",
           "def fetch(x):\n"
           "    return x.get('/x')\n")

    primitives = list(extract_repo(repo_key="r", repo_path=tmp_path))

    edges = _call_edges_from_function(primitives, path="consumer.py",
                                       name="fetch")
    targets = [e["target"] for e in edges]
    assert "external::unresolved::x.get" in targets, (
        f"expected unresolved sentinel, got {targets!r}"
    )
