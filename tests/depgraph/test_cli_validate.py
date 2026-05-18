"""Tests for depgraph.lib.cli.validate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from depgraph.lib.cli.context import Context
from depgraph.lib.cli.validate import cmd_validate


def _args(**overrides) -> argparse.Namespace:
    defaults = {"strict": False, "verbose": False, "all": False}
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def _v2_node(**overrides) -> dict:
    """A minimal well-formed v2 node primitives extractors emit."""
    node = {
        "schema_version": 2,
        "id": "test-api::models/foo.py::Foo",
        "primitive": "class",
        "kind": "model",
        "name": "Foo",
        "owner": None,
        "source": {
            "repo": "test-api",
            "path": "models/foo.py",
            "language": "python",
            "line": 1,
            "end_line": 5,
        },
        "signature": {},
        "attributes": {},
        "edges_out": [],
        "extractor": "depgraph/extractors/python/extract.py@test",
        "structural_hash": "deadbeef01234567deadbeef01234567",
    }
    node.update(overrides)
    return node


def test_validate_empty_nodes_exits_0(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """No node files → no validation problems → exit 0 + summary line."""
    ctx = Context.from_data_dir(data_dir)
    rc = cmd_validate(_args(), ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "validate: 0 nodes" in out
    assert "0 problems" in out


def test_validate_valid_v2_node_exits_0(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A well-formed v2 node passes both schema and coherence checks → exit 0."""
    ctx = Context.from_data_dir(data_dir)
    node_file = ctx.NODES / "test_api__models_foo_py__Foo.json"
    node_file.parent.mkdir(parents=True, exist_ok=True)
    node_file.write_text(json.dumps(_v2_node()))

    rc = cmd_validate(_args(), ctx)

    assert rc == 0
    out = capsys.readouterr().out
    assert "validate: 1 nodes" in out
    assert "0 problems" in out


def test_validate_invalid_node_exits_nonzero(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A node missing required fields fails validation → exit non-zero + counts."""
    ctx = Context.from_data_dir(data_dir)
    bad_node = {"id": "test-api::models/foo.py::Foo"}
    node_file = ctx.NODES / "bad_node.json"
    node_file.parent.mkdir(parents=True, exist_ok=True)
    node_file.write_text(json.dumps(bad_node))

    rc = cmd_validate(_args(), ctx)

    assert rc != 0
    captured = capsys.readouterr()
    assert "validate: 1 nodes" in captured.out
    assert "problems" in captured.out
    # Per-class detail goes to stderr.
    assert "shape" in captured.err.lower() or "primitive" in captured.err.lower()


def test_validate_caps_output_by_default(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """With more than 20 bad nodes, default output caps the per-class list."""
    ctx = Context.from_data_dir(data_dir)
    ctx.NODES.mkdir(parents=True, exist_ok=True)
    for i in range(30):
        (ctx.NODES / f"bad_{i}.json").write_text(json.dumps({"id": f"x{i}"}))

    rc = cmd_validate(_args(), ctx)

    assert rc != 0
    err = capsys.readouterr().err
    # Cap message rendered when failures exceed the default 20.
    assert "more (pass --all" in err


def test_validate_all_disables_cap(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """--all removes the per-class output cap."""
    ctx = Context.from_data_dir(data_dir)
    ctx.NODES.mkdir(parents=True, exist_ok=True)
    for i in range(25):
        (ctx.NODES / f"bad_{i}.json").write_text(json.dumps({"id": f"x{i}"}))

    rc = cmd_validate(_args(all=True), ctx)

    assert rc != 0
    err = capsys.readouterr().err
    assert "more (pass --all" not in err
