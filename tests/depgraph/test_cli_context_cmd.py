"""Tests for depgraph.lib.cli.context_cmd."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from depgraph.lib.cli.context import Context
from depgraph.lib.cli.context_cmd import cmd_context


def test_context_unknown_target_returns_1(data_dir: Path, capsys) -> None:
    ctx = Context.from_data_dir(data_dir)
    args = argparse.Namespace(target="nonexistent::id")
    rc = cmd_context(args, ctx)
    assert rc == 1
    captured = capsys.readouterr()
    assert "no nodes match" in captured.err.lower()


def test_context_prints_known_node(data_dir: Path, capsys) -> None:
    # Write a minimal valid node JSON
    nodes_dir = data_dir / "nodes" / "modules"
    nodes_dir.mkdir(parents=True)
    node_path = nodes_dir / "demo.json"
    node_path.write_text(json.dumps({
        "id": "demo::path::Sym",
        "kind": "module",
        "title": "Demo Symbol",
        "structural_hash": "abcdef1234567890",
        "source": {"repo": "demo", "path": "path/to/file.py"},
    }))
    ctx = Context.from_data_dir(data_dir)
    args = argparse.Namespace(target="demo::path::Sym")
    rc = cmd_context(args, ctx)
    assert rc == 0
    captured = capsys.readouterr()
    assert "Demo Symbol" in captured.out
    assert "demo::path::Sym" in captured.out
