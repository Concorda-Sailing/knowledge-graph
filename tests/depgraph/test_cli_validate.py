"""Tests for depgraph.lib.cli.validate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from depgraph.lib.cli.context import Context
from depgraph.lib.cli.validate import cmd_validate


def test_validate_empty_nodes_exits_0(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """No node files → no validation errors → exit 0."""
    ctx = Context.from_data_dir(data_dir)
    args = argparse.Namespace(strict=False)
    rc = cmd_validate(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "valid" in out


def test_validate_valid_node_exits_0(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A well-formed node JSON passes schema validation → exit 0."""
    ctx = Context.from_data_dir(data_dir)
    node = {
        "schema_version": 1,
        "id": "test-api::models/foo.py::Foo",
        "kind": "model",
        "source": {"repo": "test-api", "path": "models/foo.py"},
        "extractor": "python",
        "structural_hash": "deadbeef01234567",
    }
    node_file = ctx.NODES / "test_api__models_foo_py__Foo.json"
    node_file.write_text(json.dumps(node))

    args = argparse.Namespace(strict=False)
    rc = cmd_validate(args, ctx)

    assert rc == 0
    out = capsys.readouterr().out
    assert "valid" in out


def test_validate_invalid_node_exits_nonzero(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A node missing required fields fails schema validation → exit non-zero."""
    ctx = Context.from_data_dir(data_dir)
    # Missing required fields: schema_version, kind, source, extractor, structural_hash
    bad_node = {"id": "test-api::models/foo.py::Foo"}
    node_file = ctx.NODES / "bad_node.json"
    node_file.write_text(json.dumps(bad_node))

    args = argparse.Namespace(strict=False)
    rc = cmd_validate(args, ctx)

    assert rc != 0
    err = capsys.readouterr().err
    assert "INVALID" in err
