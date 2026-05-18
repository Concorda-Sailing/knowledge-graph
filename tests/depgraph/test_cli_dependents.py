"""Tests for depgraph.lib.cli.dependents."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from depgraph.lib.cli.context import Context
from depgraph.lib.cli.dependents import cmd_dependents


def _write_index(ctx: Context, by_target: dict) -> None:
    ctx.DEPENDENTS_INDEX.parent.mkdir(parents=True, exist_ok=True)
    ctx.DEPENDENTS_INDEX.write_text(json.dumps(by_target))


def test_dependents_depth1_returns_direct_dependents(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Depth-1 walk: prints the target and its direct dependents only."""
    ctx = Context.from_data_dir(data_dir)
    _write_index(ctx, {
        "repo::models/foo.py::Foo": [
            {"source": "repo::models/bar.py::Bar", "kind": "class"},
        ],
        "repo::models/bar.py::Bar": [
            {"source": "repo::models/baz.py::Baz", "kind": "class"},
        ],
    })
    args = argparse.Namespace(id="repo::models/foo.py::Foo", depth=1)
    rc = cmd_dependents(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "repo::models/foo.py::Foo" in out
    assert "repo::models/bar.py::Bar" in out
    # Depth-1: baz is a transitive dependent, must NOT appear.
    assert "repo::models/baz.py::Baz" not in out


def test_dependents_depth2_includes_transitive(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Depth-2 walk: prints direct + transitive dependents."""
    ctx = Context.from_data_dir(data_dir)
    _write_index(ctx, {
        "repo::models/foo.py::Foo": [
            {"source": "repo::models/bar.py::Bar", "kind": "class"},
        ],
        "repo::models/bar.py::Bar": [
            {"source": "repo::models/baz.py::Baz", "kind": "class"},
        ],
    })
    args = argparse.Namespace(id="repo::models/foo.py::Foo", depth=2)
    rc = cmd_dependents(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "repo::models/foo.py::Foo" in out
    assert "repo::models/bar.py::Bar" in out
    assert "repo::models/baz.py::Baz" in out


def test_dependents_unknown_target_silently_prints_just_id(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """An id with no entry in the index walks zero edges and prints just the id.

    Matches legacy bin/depgraph behavior — Phase 2 preserves it byte-for-byte.
    Whether this is the right UX is a separate question for later refinement.
    """
    ctx = Context.from_data_dir(data_dir)
    _write_index(ctx, {
        "repo::models/foo.py::Foo": [
            {"source": "repo::models/bar.py::Bar", "kind": "class"},
        ],
    })
    args = argparse.Namespace(id="repo::models/nonexistent.py::Ghost", depth=2)
    rc = cmd_dependents(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "repo::models/nonexistent.py::Ghost" in out
