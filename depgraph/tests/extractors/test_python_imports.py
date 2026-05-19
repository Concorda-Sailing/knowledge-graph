"""Tests for python extractor's ImportFrom edge resolution, especially
re-exports through package __init__.py barrels.

Regression: `from pkg import Name` where `pkg/__init__.py` re-exports `Name`
from a submodule used to collapse the edge to the package module instead of
the underlying defining symbol, under-counting consumers of barrel-exported
classes (e.g. a model class re-exported via a package's `__init__.py`).
"""
from __future__ import annotations

from pathlib import Path

from depgraph.extractors.python.extract import extract_repo


def _write(root: Path, rel: str, content: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)


def _import_edges(primitives: list[dict], from_path: str) -> list[dict]:
    for p in primitives:
        if p["primitive"] == "module" and p["source"]["path"] == from_path:
            return [e for e in p["edges_out"] if e["kind"] == "imports"]
    raise AssertionError(f"module {from_path!r} not found in primitives")


def _edge_for(edges: list[dict], local_binding: str) -> dict:
    for e in edges:
        if e.get("local_binding") == local_binding:
            return e
    raise AssertionError(
        f"no edge with local_binding={local_binding!r}; have: "
        f"{[e.get('local_binding') for e in edges]}"
    )


def test_package_reexport_resolves_to_defining_symbol(tmp_path: Path) -> None:
    """`from pkg import Name` should edge to pkg/sub.py::Name when
    pkg/__init__.py re-exports it via `from .sub import Name`."""
    _write(tmp_path, "pkg/__init__.py", "from .sub import Boat\n")
    _write(tmp_path, "pkg/sub.py", "class Boat:\n    pass\n")
    _write(tmp_path, "consumer.py", "from pkg import Boat\n")

    primitives = list(extract_repo(repo_key="r", repo_path=tmp_path))

    edges = _import_edges(primitives, "consumer.py")
    edge = _edge_for(edges, "Boat")
    assert edge["target"] == "r::pkg/sub.py::Boat", (
        f"expected r::pkg/sub.py::Boat, got {edge['target']!r}"
    )
    assert edge["confidence"] == "exact"


def test_package_reexport_with_alias_at_package_boundary(tmp_path: Path) -> None:
    """pkg/__init__.py: `from .sub import _Hidden as Boat`; consumer
    `from pkg import Boat` resolves to the hidden symbol's defining site."""
    _write(tmp_path, "pkg/__init__.py", "from .sub import _Hidden as Boat\n")
    _write(tmp_path, "pkg/sub.py", "class _Hidden:\n    pass\n")
    _write(tmp_path, "consumer.py", "from pkg import Boat\n")

    primitives = list(extract_repo(repo_key="r", repo_path=tmp_path))

    edges = _import_edges(primitives, "consumer.py")
    edge = _edge_for(edges, "Boat")
    assert edge["target"] == "r::pkg/sub.py::_Hidden", (
        f"expected r::pkg/sub.py::_Hidden, got {edge['target']!r}"
    )


def test_package_reexport_with_alias_at_consumer(tmp_path: Path) -> None:
    """Consumer uses `from pkg import Boat as B`; edge target should still
    be the underlying defining symbol; local_binding is the aliased name."""
    _write(tmp_path, "pkg/__init__.py", "from .sub import Boat\n")
    _write(tmp_path, "pkg/sub.py", "class Boat:\n    pass\n")
    _write(tmp_path, "consumer.py", "from pkg import Boat as B\n")

    primitives = list(extract_repo(repo_key="r", repo_path=tmp_path))

    edges = _import_edges(primitives, "consumer.py")
    edge = _edge_for(edges, "B")
    assert edge["target"] == "r::pkg/sub.py::Boat"


def test_transitive_package_reexport(tmp_path: Path) -> None:
    """Two levels of package barrels: outer/__init__.py re-exports from
    inner/__init__.py which re-exports from leaf.py. Consumer importing
    from the outer package should resolve all the way to leaf.py::Name."""
    _write(tmp_path, "outer/__init__.py", "from .inner import Boat\n")
    _write(tmp_path, "outer/inner/__init__.py", "from .leaf import Boat\n")
    _write(tmp_path, "outer/inner/leaf.py", "class Boat:\n    pass\n")
    _write(tmp_path, "consumer.py", "from outer import Boat\n")

    primitives = list(extract_repo(repo_key="r", repo_path=tmp_path))

    edges = _import_edges(primitives, "consumer.py")
    edge = _edge_for(edges, "Boat")
    assert edge["target"] == "r::outer/inner/leaf.py::Boat", (
        f"expected leaf, got {edge['target']!r}"
    )


def test_unresolvable_name_falls_back_to_package(tmp_path: Path) -> None:
    """Name not in package re-export map keeps existing fallback: edge
    targets the package __init__.py module itself."""
    _write(tmp_path, "pkg/__init__.py", "from .sub import Boat\n")
    _write(tmp_path, "pkg/sub.py", "class Boat:\n    pass\n")
    _write(tmp_path, "consumer.py", "from pkg import does_not_exist\n")

    primitives = list(extract_repo(repo_key="r", repo_path=tmp_path))

    edges = _import_edges(primitives, "consumer.py")
    edge = _edge_for(edges, "does_not_exist")
    assert edge["target"] == "r::pkg/__init__.py"


def test_direct_submodule_import_unchanged(tmp_path: Path) -> None:
    """Pre-existing behavior: `from pkg.sub import Boat` already resolves
    to the defining file directly; must remain so."""
    _write(tmp_path, "pkg/__init__.py", "")
    _write(tmp_path, "pkg/sub.py", "class Boat:\n    pass\n")
    _write(tmp_path, "consumer.py", "from pkg.sub import Boat\n")

    primitives = list(extract_repo(repo_key="r", repo_path=tmp_path))

    edges = _import_edges(primitives, "consumer.py")
    edge = _edge_for(edges, "Boat")
    assert edge["target"] == "r::pkg/sub.py::Boat"


def test_bare_package_import_unchanged(tmp_path: Path) -> None:
    """`import pkg` should still edge to the package module, not into
    any of its re-exports (no symbol was requested)."""
    _write(tmp_path, "pkg/__init__.py", "from .sub import Boat\n")
    _write(tmp_path, "pkg/sub.py", "class Boat:\n    pass\n")
    _write(tmp_path, "consumer.py", "import pkg\n")

    primitives = list(extract_repo(repo_key="r", repo_path=tmp_path))

    edges = _import_edges(primitives, "consumer.py")
    edge = _edge_for(edges, "pkg")
    assert edge["target"] == "r::pkg/__init__.py"
    assert edge["via"] == "import"


def test_wildcard_reexport_resolves_to_defining_symbol(tmp_path: Path) -> None:
    """`pkg/__init__.py: from .sub import *` followed by consumer
    `from pkg import Boat` should resolve to `pkg/sub.py::Boat`. Without
    wildcard-expansion in the re-export map this is silent under-counting
    (the consumer edge stays on the package module). Wildcards re-export
    every public top-level symbol of the target."""
    _write(tmp_path, "pkg/__init__.py", "from .sub import *\n")
    _write(tmp_path, "pkg/sub.py", "class Boat:\n    pass\n")
    _write(tmp_path, "consumer.py", "from pkg import Boat\n")

    primitives = list(extract_repo(repo_key="r", repo_path=tmp_path))

    edges = _import_edges(primitives, "consumer.py")
    edge = _edge_for(edges, "Boat")
    assert edge["target"] == "r::pkg/sub.py::Boat", (
        f"expected r::pkg/sub.py::Boat, got {edge['target']!r}"
    )


def test_chained_wildcard_reexport_resolves_through_packages(tmp_path: Path) -> None:
    """outer/__init__.py: from .inner import *; inner/__init__.py: from .leaf import *.
    Consumer `from outer import Boat` should still resolve to leaf.py::Boat —
    the fixpoint loop must propagate the inner re-exports back up to outer
    even when the wildcard target's __init__.py has no direct symbols."""
    _write(tmp_path, "outer/__init__.py", "from .inner import *\n")
    _write(tmp_path, "outer/inner/__init__.py", "from .leaf import *\n")
    _write(tmp_path, "outer/inner/leaf.py", "class Boat:\n    pass\n")
    _write(tmp_path, "consumer.py", "from outer import Boat\n")

    primitives = list(extract_repo(repo_key="r", repo_path=tmp_path))

    edges = _import_edges(primitives, "consumer.py")
    edge = _edge_for(edges, "Boat")
    assert edge["target"] == "r::outer/inner/leaf.py::Boat", (
        f"expected leaf, got {edge['target']!r}"
    )


def test_wildcard_reexport_skips_underscored_symbols(tmp_path: Path) -> None:
    """Python's default `from X import *` (when __all__ is undefined)
    skips underscored names; the re-export map must match that semantics.
    Underscored symbols should NOT resolve through a wildcard barrel."""
    _write(tmp_path, "pkg/__init__.py", "from .sub import *\n")
    _write(tmp_path, "pkg/sub.py",
           "class Boat:\n    pass\n\nclass _Internal:\n    pass\n")
    _write(tmp_path, "consumer.py",
           "from pkg import Boat\nfrom pkg import _Internal\n")

    primitives = list(extract_repo(repo_key="r", repo_path=tmp_path))

    edges = _import_edges(primitives, "consumer.py")
    # Boat re-exports via wildcard.
    boat_edge = _edge_for(edges, "Boat")
    assert boat_edge["target"] == "r::pkg/sub.py::Boat"
    # _Internal does not — falls back to the package module.
    internal_edge = _edge_for(edges, "_Internal")
    assert internal_edge["target"] == "r::pkg/__init__.py"


def test_wildcard_reexport_named_takes_precedence(tmp_path: Path) -> None:
    """When a package has both `from .sub import Boat` (named) and a
    wildcard from a different module, the named edge wins. Wildcards use
    `setdefault` so they don't overwrite explicit re-exports."""
    _write(tmp_path, "pkg/__init__.py",
           "from .named import Boat\nfrom .wild import *\n")
    _write(tmp_path, "pkg/named.py", "class Boat:\n    pass\n")
    _write(tmp_path, "pkg/wild.py", "class Boat:\n    pass\n")
    _write(tmp_path, "consumer.py", "from pkg import Boat\n")

    primitives = list(extract_repo(repo_key="r", repo_path=tmp_path))

    edges = _import_edges(primitives, "consumer.py")
    edge = _edge_for(edges, "Boat")
    assert edge["target"] == "r::pkg/named.py::Boat", (
        f"named re-export should win over wildcard, got {edge['target']!r}"
    )


def test_fixpoint_cap_warns_on_excessive_nesting(tmp_path: Path, capsys) -> None:
    """When package barrel nesting exceeds the fixpoint cap, the resolver
    emits a stderr warning rather than silently leaving edges partly
    resolved. Pinning the eye on the user-visible behavior so future
    refactors can't accidentally remove the message."""
    # Build 15 layers of barrel nesting; default cap is 10, so this
    # forces the loop to exit without converging. Each layer is a
    # `__init__.py` that does `from .lN+1 import *`.
    n_layers = 15
    parts = ["root"]
    _write(tmp_path, "root/__init__.py", f"from .l1 import *\n")
    for i in range(1, n_layers):
        parts.append(f"l{i}")
        rel = "/".join(parts)
        _write(tmp_path, f"{rel}/__init__.py", f"from .l{i+1} import *\n")
    parts.append(f"l{n_layers}")
    leaf_rel = "/".join(parts) + ".py"
    _write(tmp_path, leaf_rel, "class Boat:\n    pass\n")
    _write(tmp_path, "consumer.py", "from root import Boat\n")

    list(extract_repo(repo_key="r", repo_path=tmp_path))

    captured = capsys.readouterr()
    assert "package re-export resolution did not converge" in captured.err, (
        f"expected fixpoint-cap warning on >10-level nesting, got stderr: "
        f"{captured.err!r}"
    )


def test_extends_via_barrel_reexport_resolves_to_leaf(tmp_path: Path) -> None:
    """Pins the 03eb61f + 7cc056e interaction: when a class extends a base
    imported through a package barrel (`from models import BaseModel`
    where `models/__init__.py: from .base import BaseModel`), inheritance
    should chase through the re-export rewrite and target the leaf
    `models/base.py::BaseModel`, not the package module or unknown."""
    _write(tmp_path, "models/__init__.py", "from .base import BaseModel\n")
    _write(tmp_path, "models/base.py", "class BaseModel:\n    pass\n")
    _write(tmp_path, "consumer.py",
           "from models import BaseModel\n"
           "class Item(BaseModel):\n    pass\n")

    primitives = list(extract_repo(repo_key="r", repo_path=tmp_path))

    item = next(p for p in primitives if p["name"] == "Item")
    extends = [e for e in item["edges_out"] if e["kind"] == "extends"]
    assert any(e["target"] == "r::models/base.py::BaseModel"
               and e["confidence"] == "exact"
               for e in extends), extends
