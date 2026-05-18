"""Tests for graphui.app.search — both the existing semantic path and the
day-zero lexical fallback (#37).

graphui isn't a pytest project of its own; these tests live in depgraph's
test tree because pyproject.toml's `pythonpath` already drags in
`graphui/` via the framework-root insertion. The fixtures mock the loader
so no project.toml setup is needed.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def search_mod(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Import graphui.app.search with a fake project + node corpus wired
    up. Reset the lexical-index cache before each test so cross-test
    pollution doesn't sneak through."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "graphui"))
    from app import loader, search as search_mod

    fake_proj = SimpleNamespace(
        id="testproj",
        depgraph_nodes_dir=tmp_path / "depgraph" / "nodes",
        logigraph_nodes_dir=tmp_path / "logigraph" / "nodes",
    )
    (fake_proj.depgraph_nodes_dir).mkdir(parents=True)
    (fake_proj.logigraph_nodes_dir).mkdir(parents=True)
    monkeypatch.setattr(loader, "current_project", lambda: fake_proj)
    # Reset module-level caches.
    monkeypatch.setattr(search_mod, "_LEXICAL_CACHE", None, raising=False)
    monkeypatch.setattr(search_mod, "_LEXICAL_MTIME", (None, 0.0), raising=False)
    monkeypatch.setattr(search_mod, "_index_cache", None, raising=False)
    monkeypatch.setattr(search_mod, "_index_mtimes", {}, raising=False)
    return search_mod, loader, fake_proj


def _stub_nodes(search_mod, loader_mod, monkeypatch, nodes: list[dict]) -> None:
    monkeypatch.setattr(loader_mod, "load_depgraph_nodes", lambda: nodes)


def test_lexical_finds_node_by_id(search_mod, monkeypatch: pytest.MonkeyPatch):
    sm, ld, _ = search_mod
    _stub_nodes(sm, ld, monkeypatch, [
        {"id": "web::src/components/ui/button.tsx::Button",
         "primitive": "function", "kind": "component", "name": "Button",
         "source": {"repo": "web", "path": "src/components/ui/button.tsx"}},
        {"id": "api::database.py::engine",
         "primitive": "variable", "kind": "variable", "name": "engine",
         "source": {"repo": "api", "path": "database.py"}},
    ])
    hits = sm.lexical_search("button", limit=5)
    assert len(hits) >= 1
    assert hits[0]["node_id"] == "web::src/components/ui/button.tsx::Button"
    assert hits[0]["kind_hint"] == "node"
    assert hits[0]["source_field"] == "lexical"


def test_lexical_finds_node_by_name_only(search_mod, monkeypatch: pytest.MonkeyPatch):
    sm, ld, _ = search_mod
    _stub_nodes(sm, ld, monkeypatch, [
        {"id": "web::src/hooks/use-constants.ts::useConstants",
         "primitive": "function", "kind": "hook", "name": "useConstants",
         "source": {"repo": "web", "path": "src/hooks/use-constants.ts"}},
    ])
    hits = sm.lexical_search("useConstants", limit=5)
    assert hits and hits[0]["node_id"].endswith("::useConstants")


def test_lexical_finds_by_path(search_mod, monkeypatch: pytest.MonkeyPatch):
    sm, ld, _ = search_mod
    _stub_nodes(sm, ld, monkeypatch, [
        {"id": "api::database.py::engine",
         "primitive": "variable", "kind": "variable", "name": "engine",
         "source": {"repo": "api", "path": "database.py"}},
    ])
    hits = sm.lexical_search("database", limit=5)
    assert hits, "search by path should find the node"
    assert hits[0]["node_id"] == "api::database.py::engine"


def test_lexical_skips_packages(search_mod, monkeypatch: pytest.MonkeyPatch):
    """Package primitives have nothing useful to lexically index — the
    directory groupings carry no symbol semantics."""
    sm, ld, _ = search_mod
    _stub_nodes(sm, ld, monkeypatch, [
        {"id": "api::services", "primitive": "package", "name": "services",
         "source": {"repo": "api", "path": "services"}},
        {"id": "api::services/user.py::User", "primitive": "class",
         "kind": "model", "name": "User",
         "source": {"repo": "api", "path": "services/user.py"}},
    ])
    hits = sm.lexical_search("services", limit=5)
    ids = [h["node_id"] for h in hits]
    assert "api::services" not in ids
    # The class with services in its path still surfaces.
    assert "api::services/user.py::User" in ids


def test_lexical_search_returns_empty_on_empty_query(
    search_mod, monkeypatch: pytest.MonkeyPatch,
):
    sm, ld, _ = search_mod
    _stub_nodes(sm, ld, monkeypatch, [
        {"id": "api::x.py::y", "primitive": "function", "name": "y",
         "source": {"repo": "api", "path": "x.py"}},
    ])
    assert sm.lexical_search("", limit=5) == []
    assert sm.lexical_search("   ", limit=5) == []


def test_search_routes_lexical_mode_to_lexical_search(
    search_mod, monkeypatch: pytest.MonkeyPatch,
):
    """mode='lexical' bypasses the embedding index and goes straight to
    the BM25-over-nodes path."""
    sm, ld, _ = search_mod
    _stub_nodes(sm, ld, monkeypatch, [
        {"id": "api::routers/auth.py::login",
         "primitive": "function", "kind": "endpoint", "name": "login",
         "source": {"repo": "api", "path": "routers/auth.py"}},
    ])
    hits = sm.search("auth", scopes=None, mode="lexical", limit=5)
    assert hits
    assert all(h["source_field"] == "lexical" for h in hits)


def test_semantic_falls_back_to_lexical_when_embeddings_missing(
    search_mod, monkeypatch: pytest.MonkeyPatch,
):
    """On a corpus with no embeddings.bin yet, semantic mode would
    return zero hits. The fallback runs lexical so day-zero users get
    something useful (#37)."""
    sm, ld, _ = search_mod
    _stub_nodes(sm, ld, monkeypatch, [
        {"id": "api::routers/auth.py::login",
         "primitive": "function", "kind": "endpoint", "name": "login",
         "source": {"repo": "api", "path": "routers/auth.py"}},
    ])
    # No embeddings.bin / .jsonl was created in the tmp project, so the
    # semantic path will have an empty candidate set and fall through.
    hits = sm.search("login", scopes=None, mode="semantic", limit=5)
    assert hits
    assert hits[0]["source_field"] == "lexical"
