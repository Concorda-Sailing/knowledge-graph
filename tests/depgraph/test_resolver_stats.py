"""Per-resolver hit-rate counters (R7, issue #77).

Each resolver branch increments a counter keyed by (resolver_name, outcome).
Counters are persisted into nodes/_meta.json::resolver_stats and surfaced
by `kg depgraph stats`. This file pins:

  1. The Python extractor populates module-level counters and exposes them
     through `consume_resolver_stats()` (read-then-reset).
  2. Synthetic source exercising each Python resolver branch produces the
     expected (resolver_name, outcome) keys.
  3. `kg depgraph stats` renders a "Resolver stats" section when
     `_meta.json::resolver_stats` is non-empty.

The TS-side counters travel as an ndjson sentinel; the regen pipeline
merges both sides into `_meta.json`. That end-to-end wiring is exercised
by the regen-determinism + reconcile tests indirectly — this file pins
the Python-side branches and the stats-rendering surface.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from depgraph.extractors.python.extract import (
    consume_resolver_stats,
    extract_repo,
)
from depgraph.lib.cli.context import Context
from depgraph.lib.cli.stats import cmd_stats


def _write(root: Path, rel: str, content: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)


@pytest.fixture(autouse=True)
def _reset_stats():
    """Each test starts with a clean stats counter — module-level state
    survives across test cases otherwise."""
    consume_resolver_stats()
    yield
    consume_resolver_stats()


# ---------------------------------------------------------------------------
# Python extractor exposes resolver-stat counters
# ---------------------------------------------------------------------------

def test_consume_returns_empty_dict_when_nothing_extracted() -> None:
    """No extraction → empty counter dict, returns the same shape regardless."""
    stats = consume_resolver_stats()
    assert isinstance(stats, dict)
    assert stats == {}


def test_consume_resets_after_read(tmp_path: Path) -> None:
    """Read-then-reset semantics: a second call sees the empty counter."""
    _write(tmp_path, "a.py",
           "def helper(): pass\n"
           "def caller():\n"
           "    helper()\n")
    list(extract_repo(repo_key="r", repo_path=tmp_path))
    first = consume_resolver_stats()
    assert first  # something was counted
    second = consume_resolver_stats()
    assert second == {}


# ---------------------------------------------------------------------------
# Each Python resolver branch ticks its counter
# ---------------------------------------------------------------------------

def test_bare_name_call_hit(tmp_path: Path) -> None:
    """`helper()` where helper is defined in the same file → bare_name hit."""
    _write(tmp_path, "a.py",
           "def helper(): pass\n"
           "def caller():\n"
           "    helper()\n")
    list(extract_repo(repo_key="r", repo_path=tmp_path))
    stats = consume_resolver_stats()
    assert stats.get(("python.call.bare_name", "hit"), 0) >= 1


def test_bare_name_call_fallthrough(tmp_path: Path) -> None:
    """`unknown()` with no local/imported binding → fallthrough."""
    _write(tmp_path, "a.py",
           "def caller():\n"
           "    unknown()\n")
    list(extract_repo(repo_key="r", repo_path=tmp_path))
    stats = consume_resolver_stats()
    assert stats.get(("python.call.bare_name", "fallthrough"), 0) >= 1


def test_method_via_imports_hit(tmp_path: Path) -> None:
    """`import requests; requests.get(...)` → method_via_imports hit. (#68)"""
    _write(tmp_path, "a.py",
           "import requests\n"
           "def caller():\n"
           "    requests.get('/x')\n")
    list(extract_repo(repo_key="r", repo_path=tmp_path))
    stats = consume_resolver_stats()
    assert stats.get(("python.call.method_via_imports", "hit"), 0) >= 1


def test_method_via_var_types_hit(tmp_path: Path) -> None:
    """`x = Service(); x.go()` (in-corpus class) → method_via_var_types hit."""
    _write(tmp_path, "a.py",
           "class Service:\n"
           "    def go(self): pass\n"
           "def caller():\n"
           "    s = Service()\n"
           "    s.go()\n")
    list(extract_repo(repo_key="r", repo_path=tmp_path))
    stats = consume_resolver_stats()
    assert stats.get(("python.call.method_via_var_types", "hit"), 0) >= 1


def test_method_unresolved_fallthrough(tmp_path: Path) -> None:
    """`unknown_var.go()` with no typing + no import → method_unresolved."""
    _write(tmp_path, "a.py",
           "def caller(x):\n"
           "    x.go()\n")
    list(extract_repo(repo_key="r", repo_path=tmp_path))
    stats = consume_resolver_stats()
    assert stats.get(("python.call.method_unresolved", "fallthrough"), 0) >= 1


def test_extends_local_hit(tmp_path: Path) -> None:
    """`class B(A)` where A is in the same module → extends local hit."""
    _write(tmp_path, "a.py",
           "class A: pass\n"
           "class B(A): pass\n")
    list(extract_repo(repo_key="r", repo_path=tmp_path))
    stats = consume_resolver_stats()
    assert stats.get(("python.extends.local", "hit"), 0) >= 1


def test_extends_imports_table_hit(tmp_path: Path) -> None:
    """`from .base import A; class B(A)` → extends.imports_table hit."""
    _write(tmp_path, "base.py", "class A: pass\n")
    _write(tmp_path, "child.py",
           "from base import A\n"
           "class B(A): pass\n")
    list(extract_repo(repo_key="r", repo_path=tmp_path))
    stats = consume_resolver_stats()
    assert stats.get(("python.extends.imports_table", "hit"), 0) >= 1


def test_extends_fallthrough(tmp_path: Path) -> None:
    """`class B(UnknownBase): pass` with no import → extends fallthrough."""
    _write(tmp_path, "a.py",
           "class B(UnknownBase): pass\n")
    list(extract_repo(repo_key="r", repo_path=tmp_path))
    stats = consume_resolver_stats()
    assert stats.get(("python.extends.unknown", "fallthrough"), 0) >= 1


def test_imports_from_module_hit(tmp_path: Path) -> None:
    """`from x import y` where x is in-corpus → imports.from_module hit."""
    _write(tmp_path, "x.py", "def y(): pass\n")
    _write(tmp_path, "main.py", "from x import y\n")
    list(extract_repo(repo_key="r", repo_path=tmp_path))
    stats = consume_resolver_stats()
    assert stats.get(("python.imports.from_module", "hit"), 0) >= 1


def test_imports_from_module_fallthrough(tmp_path: Path) -> None:
    """`from somepkg import thing` where somepkg is external → fallthrough."""
    _write(tmp_path, "main.py", "from somepkg import thing\n")
    list(extract_repo(repo_key="r", repo_path=tmp_path))
    stats = consume_resolver_stats()
    assert stats.get(("python.imports.from_module", "fallthrough"), 0) >= 1


def test_imports_wildcard(tmp_path: Path) -> None:
    """`from x import *` ticks the wildcard counter regardless of resolution."""
    _write(tmp_path, "x.py", "def y(): pass\n")
    _write(tmp_path, "main.py", "from x import *\n")
    list(extract_repo(repo_key="r", repo_path=tmp_path))
    stats = consume_resolver_stats()
    total = (
        stats.get(("python.imports.wildcard", "hit"), 0)
        + stats.get(("python.imports.wildcard", "fuzzy"), 0)
        + stats.get(("python.imports.wildcard", "fallthrough"), 0)
    )
    assert total >= 1


def test_imports_module_statement(tmp_path: Path) -> None:
    """Plain `import x` ticks the module-import counter."""
    _write(tmp_path, "x.py", "")
    _write(tmp_path, "main.py", "import x\n")
    list(extract_repo(repo_key="r", repo_path=tmp_path))
    stats = consume_resolver_stats()
    total = (
        stats.get(("python.imports.module", "hit"), 0)
        + stats.get(("python.imports.module", "fallthrough"), 0)
    )
    assert total >= 1


# ---------------------------------------------------------------------------
# stats.py surfaces the table when _meta.json carries resolver_stats
# ---------------------------------------------------------------------------

def test_cmd_stats_renders_resolver_table(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`kg depgraph stats` includes a 'Resolver stats' section when
    `_meta.json::resolver_stats` is non-empty."""
    ctx = Context.from_data_dir(data_dir)
    meta_path = ctx.NODES / "_meta.json"
    meta_path.write_text(json.dumps({
        "schema_version": 2,
        "regen_status": "complete",
        "resolver_stats": {
            "python.call.bare_name": {"hit": 5, "fallthrough": 2},
            "python.extends.local": {"hit": 1},
        },
    }))
    args = argparse.Namespace(telemetry=False, edges=False, unresolved_top=15)
    rc = cmd_stats(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Resolver stats" in out
    assert "python.call.bare_name" in out


def test_cmd_stats_omits_resolver_table_when_empty(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """No resolver_stats in _meta.json → no 'Resolver stats' section
    (keeps the report quiet when the data isn't there)."""
    ctx = Context.from_data_dir(data_dir)
    meta_path = ctx.NODES / "_meta.json"
    meta_path.write_text(json.dumps({
        "schema_version": 2,
        "regen_status": "complete",
    }))
    args = argparse.Namespace(telemetry=False, edges=False, unresolved_top=15)
    rc = cmd_stats(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Resolver stats" not in out
