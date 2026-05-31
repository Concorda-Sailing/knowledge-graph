"""Tests for kg.registry — the ~/.claude/kg-graphs.toml manager."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Make the framework root importable so `import kg.registry` works.
TOOL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TOOL_ROOT))

from kg import registry  # noqa: E402


@pytest.fixture
def tmp_registry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point KG_REGISTRY_PATH at a tmp file for the duration of the test."""
    p = tmp_path / "kg-graphs.toml"
    monkeypatch.setenv("KG_REGISTRY_PATH", str(p))
    return p


def test_load_returns_empty_when_missing(tmp_registry: Path) -> None:
    assert not tmp_registry.exists()
    assert registry.load() == []


def test_add_then_load_roundtrips(tmp_registry: Path, tmp_path: Path) -> None:
    graph_dir = tmp_path / "my-knowledge-graph"
    graph_dir.mkdir()
    registry.add(name="my-graph", path=graph_dir)

    entries = registry.load()
    assert len(entries) == 1
    assert entries[0].name == "my-graph"
    assert entries[0].path == graph_dir.resolve()


def test_add_writes_managed_header(tmp_registry: Path, tmp_path: Path) -> None:
    graph_dir = tmp_path / "g"
    graph_dir.mkdir()
    registry.add(name="g", path=graph_dir)

    text = tmp_registry.read_text()
    assert "managed by" in text.lower()
    assert "kg add" in text


def test_add_rejects_duplicate_name(tmp_registry: Path, tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    registry.add(name="dup", path=tmp_path / "a")
    with pytest.raises(ValueError, match="already registered"):
        registry.add(name="dup", path=tmp_path / "b")


def test_add_rejects_missing_path(tmp_registry: Path, tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        registry.add(name="ghost", path=tmp_path / "nope")


def test_remove_existing_returns_true(tmp_registry: Path, tmp_path: Path) -> None:
    (tmp_path / "g").mkdir()
    registry.add(name="g", path=tmp_path / "g")
    assert registry.remove("g") is True
    assert registry.load() == []


def test_remove_missing_returns_false(tmp_registry: Path) -> None:
    assert registry.remove("not-there") is False


def test_find_by_name(tmp_registry: Path, tmp_path: Path) -> None:
    (tmp_path / "alpha").mkdir()
    (tmp_path / "beta").mkdir()
    registry.add(name="alpha", path=tmp_path / "alpha")
    registry.add(name="beta", path=tmp_path / "beta")

    found = registry.find("beta")
    assert found is not None
    assert found.name == "beta"
    assert registry.find("missing") is None


def test_tilde_in_stored_path_expands_on_load(
    tmp_registry: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A path written as ~/foo round-trips through load() as an absolute path."""
    monkeypatch.setenv("HOME", str(tmp_path))
    fake_home_graph = tmp_path / "graph-x"
    fake_home_graph.mkdir()
    # Write a registry file by hand with a tilde-prefixed path.
    tmp_registry.write_text(
        '[[graph]]\nname = "x"\npath = "~/graph-x"\n'
    )
    entries = registry.load()
    assert entries[0].path == fake_home_graph.resolve()


def test_default_registry_path_prefers_grok_when_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """registry.path() resolution when KG_REGISTRY_PATH is unset:

    a Grok registry wins when present; an existing Claude registry is not
    orphaned merely because ~/.grok exists; otherwise Claude is the default.
    Isolated via a fake $HOME so it doesn't depend on the dev machine's dirs.
    """
    monkeypatch.delenv("KG_REGISTRY_PATH", raising=False)
    monkeypatch.delenv("GROK_SESSION_ID", raising=False)
    monkeypatch.delenv("GROK_HOOK_EVENT", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    grok_reg = tmp_path / ".grok" / "kg-graphs.toml"
    claude_reg = tmp_path / ".claude" / "kg-graphs.toml"

    # No ~/.grok dir and nothing populated → Claude default.
    assert registry.path() == claude_reg

    # ~/.grok exists but only the Claude registry is populated → keep Claude.
    (tmp_path / ".grok").mkdir()
    claude_reg.parent.mkdir(parents=True, exist_ok=True)
    claude_reg.write_text("")
    assert registry.path() == claude_reg

    # A Grok registry exists → it wins.
    grok_reg.parent.mkdir(parents=True, exist_ok=True)
    grok_reg.write_text("")
    assert registry.path() == grok_reg


def test_load_default_returns_none_when_unset(tmp_registry: Path) -> None:
    assert registry.load_default() is None


def test_load_default_returns_none_when_file_missing(tmp_registry: Path) -> None:
    assert not tmp_registry.exists()
    assert registry.load_default() is None


def test_save_default_then_load(tmp_registry: Path, tmp_path: Path) -> None:
    graph_dir = tmp_path / "acme-knowledge-graph"
    graph_dir.mkdir()
    registry.add(name="acme", path=graph_dir)

    registry.save_default("acme")
    assert registry.load_default() == "acme"


def test_save_default_rejects_unregistered_name(tmp_registry: Path) -> None:
    with pytest.raises(ValueError, match="not registered"):
        registry.save_default("nope")


def test_clear_default(tmp_registry: Path, tmp_path: Path) -> None:
    graph_dir = tmp_path / "g"
    graph_dir.mkdir()
    registry.add(name="g", path=graph_dir)
    registry.save_default("g")
    assert registry.load_default() == "g"

    registry.clear_default()
    assert registry.load_default() is None


def test_default_persists_through_add(tmp_registry: Path, tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    registry.add(name="a", path=tmp_path / "a")
    registry.save_default("a")

    registry.add(name="b", path=tmp_path / "b")
    assert registry.load_default() == "a"


def test_default_cleared_when_target_removed(tmp_registry: Path, tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    registry.add(name="a", path=tmp_path / "a")
    registry.save_default("a")

    registry.remove("a")
    assert registry.load_default() is None
