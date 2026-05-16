"""Tests for logigraph.lib.cli.context.Context."""
from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from logigraph.lib.cli.context import Context


def test_from_data_dir_derives_paths(data_dir: Path) -> None:
    ctx = Context.from_data_dir(data_dir)
    assert ctx.LOGIGRAPH == data_dir
    assert ctx.NODES == data_dir / "nodes"
    assert ctx.DOSSIERS_DIR == data_dir / "dossiers"
    assert ctx.CALIBRATION_DIR == data_dir / "calibration"
    assert ctx.TELEMETRY_DIR == data_dir / "telemetry"


def test_from_data_dir_resolves_depgraph_via_project_toml(
    data_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When DEPGRAPH_DATA_DIR is not set, resolves via project.toml [depgraph].data_dir."""
    monkeypatch.delenv("DEPGRAPH_DATA_DIR", raising=False)
    ctx = Context.from_data_dir(data_dir)
    assert ctx.depgraph_dir == (data_dir / "fake-depgraph").resolve()


def test_from_data_dir_env_overrides_project_toml(
    data_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DEPGRAPH_DATA_DIR env var takes priority over project.toml."""
    alt_depgraph = tmp_path / "env-depgraph"
    (alt_depgraph / "nodes").mkdir(parents=True)
    monkeypatch.setenv("DEPGRAPH_DATA_DIR", str(alt_depgraph))
    ctx = Context.from_data_dir(data_dir)
    assert ctx.depgraph_dir == alt_depgraph.resolve()


def test_framework_python_resolves(data_dir: Path) -> None:
    ctx = Context.from_data_dir(data_dir)
    assert ctx.framework_python


def test_context_is_frozen(data_dir: Path) -> None:
    ctx = Context.from_data_dir(data_dir)
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        ctx.LOGIGRAPH = Path("/elsewhere")  # type: ignore[misc]
