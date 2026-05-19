"""Tests for depgraph.lib.cli.health."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from depgraph.lib.cli.context import Context
from depgraph.lib.cli.health import cmd_health


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_node(ctx: Context, node_id: str, *, primitive: str = "class",
               kind: str = "model",
               structural_hash: str = "aabbccdd11223344",
               dossier: str | None = None) -> Path:
    """Write a minimal valid v2 node JSON under nodes/."""
    node_file = ctx.NODES / f"{node_id.replace('::', '_')}.json"
    node_file.parent.mkdir(parents=True, exist_ok=True)
    name = node_id.split("::")[-1]
    data: dict = {
        "schema_version": 2,
        "id": node_id,
        "primitive": primitive,
        "kind": kind,
        "name": name,
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
        "structural_hash": structural_hash,
    }
    if dossier is not None:
        data["dossier"] = dossier
    node_file.write_text(json.dumps(data))
    return node_file


def _make_dependents_index(ctx: Context, fan_out_by_id: dict[str, int]) -> None:
    """Write a v2 by_target index where each id has N synthetic inbound edges."""
    payload = {
        nid: [{"source_id": f"dep-{i}", "kind": "imports"} for i in range(n)]
        for nid, n in fan_out_by_id.items()
    }
    idx_dir = ctx.NODES / "_index"
    idx_dir.mkdir(parents=True, exist_ok=True)
    (idx_dir / "by_target.json").write_text(json.dumps(payload))


def _make_dossier(ctx: Context, rel_path: str, *,
                  last_reviewed_against_hash: str,
                  status: str = "current") -> Path:
    """Write a minimal dossier YAML front-matter file at ctx.DEPGRAPH/rel_path."""
    full = ctx.DEPGRAPH / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(
        f"---\n"
        f"status: {status}\n"
        f"last_reviewed_against_hash: {last_reviewed_against_hash}\n"
        f"---\n"
        f"## The rule\nsome content\n"
    )
    return full


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_health_empty_graph_exits_0(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Empty nodes/ → no problems → exit 0."""
    ctx = Context.from_data_dir(data_dir)
    args = argparse.Namespace()
    rc = cmd_health(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Depgraph health" in out
    assert "clean" in out


def test_health_single_node_no_dossier_exits_0(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A node with no dossier and few dependents is not a tier-A concern → exit 0."""
    ctx = Context.from_data_dir(data_dir)
    _make_node(ctx, "test-api::models/foo.py::Foo")
    args = argparse.Namespace()
    rc = cmd_health(args, ctx)
    assert rc == 0


def test_health_stale_dossier_exits_nonzero(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A node whose dossier was reviewed against a different hash → stale → exit 1."""
    ctx = Context.from_data_dir(data_dir)
    dossier_rel = "dossiers/foo.md"
    _make_node(
        ctx,
        "test-api::models/foo.py::Foo",
        structural_hash="currenthash0000001",
        dossier=dossier_rel,
    )
    _make_dossier(ctx, dossier_rel, last_reviewed_against_hash="oldhash99999999")
    args = argparse.Namespace()
    rc = cmd_health(args, ctx)
    assert rc == 1
    out = capsys.readouterr().out
    assert "stale" in out


def test_health_current_dossier_exits_0(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A node whose dossier hash matches structural_hash → current → exit 0."""
    ctx = Context.from_data_dir(data_dir)
    dossier_rel = "dossiers/bar.md"
    _make_node(
        ctx,
        "test-api::models/bar.py::Bar",
        structural_hash="matchinghash12345",
        dossier=dossier_rel,
    )
    _make_dossier(ctx, dossier_rel, last_reviewed_against_hash="matchinghash12345")
    args = argparse.Namespace()
    rc = cmd_health(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "clean" in out


def test_health_skips_underscore_files(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Files starting with _ (e.g. _meta.json, _index/) are skipped."""
    ctx = Context.from_data_dir(data_dir)
    # Write a broken JSON file under an underscore name — should be ignored.
    (ctx.NODES / "_broken.json").write_text("NOT VALID JSON")
    args = argparse.Namespace()
    rc = cmd_health(args, ctx)
    assert rc == 0


@pytest.mark.parametrize("primitive", ["module", "package", "variable"])
def test_health_tier_a_excludes_unstubbable_primitives(
    primitive: str, data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """High-fan-out nodes whose primitive the stubber refuses (module /
    package / variable) must not count toward Tier-A coverage — otherwise
    the warning can never clear even on a fully-curated corpus (#46)."""
    ctx = Context.from_data_dir(data_dir)
    nid = f"test-api::pkg/foo.py::heavy_{primitive}"
    _make_node(ctx, nid, primitive=primitive, kind=primitive)
    _make_dependents_index(ctx, {nid: 12})  # well above the Tier-A threshold of 10
    rc = cmd_health(argparse.Namespace(), ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Tier-A" not in out


def test_health_tier_a_counts_eligible_primitive(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A high-fan-out function with no dossier *is* a Tier-A coverage gap —
    the new exclusion must not also drop eligible primitives."""
    ctx = Context.from_data_dir(data_dir)
    nid = "test-api::pkg/foo.py::heavy_fn"
    _make_node(ctx, nid, primitive="function", kind="util")
    _make_dependents_index(ctx, {nid: 12})
    rc = cmd_health(argparse.Namespace(), ctx)
    assert rc == 1
    out = capsys.readouterr().out
    assert "Tier-A dossier coverage at 0% (0/1)" in out


def test_health_tier_a_denominator_mirrors_stubber(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Mixed corpus: one eligible function + one ineligible module, both
    high-fan-out, no dossiers. Denominator should be 1, not 2."""
    ctx = Context.from_data_dir(data_dir)
    fn_id = "test-api::pkg/foo.py::heavy_fn"
    mod_id = "test-api::pkg/bar.py::__init__"
    _make_node(ctx, fn_id, primitive="function", kind="util")
    _make_node(ctx, mod_id, primitive="module", kind="module")
    _make_dependents_index(ctx, {fn_id: 12, mod_id: 20})
    rc = cmd_health(argparse.Namespace(), ctx)
    assert rc == 1
    out = capsys.readouterr().out
    assert "Tier-A dossier coverage at 0% (0/1)" in out
