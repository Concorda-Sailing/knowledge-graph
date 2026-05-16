"""Tests for depgraph.lib.cli.context.Context."""
from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from depgraph.lib.cli.context import Context


def test_from_data_dir_derives_paths(data_dir: Path) -> None:
    ctx = Context.from_data_dir(data_dir)
    assert ctx.DEPGRAPH == data_dir
    assert ctx.NODES == data_dir / "nodes"
    assert ctx.DEPENDENTS_INDEX == data_dir / "nodes" / "_index" / "dependents.json"
    assert ctx.CORPUS_META == data_dir / "nodes" / "_meta.json"
    assert ctx.TELEMETRY_DIR == data_dir / "telemetry"
    assert ctx.INJECTIONS_LOG == data_dir / "telemetry" / "injections.jsonl"
    assert ctx.ACKS_LOG == data_dir / "telemetry" / "acknowledgments.jsonl"


def test_framework_python_resolves(data_dir: Path) -> None:
    ctx = Context.from_data_dir(data_dir)
    assert ctx.framework_python  # non-empty string


def test_context_is_frozen(data_dir: Path) -> None:
    ctx = Context.from_data_dir(data_dir)
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        ctx.DEPGRAPH = Path("/elsewhere")  # type: ignore[misc]
