"""Process-rank cue plumbing — confirms the migration from hardcoded
`kind == "endpoint"` / `kind == "model"` checks to per-project cue
lookups works end-to-end.

These tests exercise the `_load_logigraph_cues(ctx)` helper directly
rather than driving the full `cmd_process_rank` flow, because the
latter needs a fully-built depgraph corpus + index files on disk to
say anything meaningful. The cue plumbing is the change point; the
signal loops just iterate over the cues they get.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from logigraph.lib.cli.context import Context
from logigraph.lib.cli.process import _load_logigraph_cues


def _make_project(tmp_path: Path, *, repo_manifests: dict[str, dict],
                  classification: dict | None = None) -> Context:
    """Build a minimal logigraph project layout: a logigraph data dir, a
    depgraph data dir linked via [depgraph].data_dir, and one or more
    target repos with the requested manifest files."""
    logigraph_dir = tmp_path / "kg-logigraph"
    logigraph_dir.mkdir()
    depgraph_dir = tmp_path / "kg-depgraph"
    depgraph_dir.mkdir()
    # logigraph project.toml — only the depgraph data-dir pointer
    (logigraph_dir / "project.toml").write_text(
        f'[depgraph]\ndata_dir = "{depgraph_dir}"\n'
    )
    # depgraph project.toml — repos + optional classification block.
    # `repo_manifests` maps repo_key -> {"manifest_filename": {...json...}}.
    lines = ["[project]\nname = \"test\"\n\n"]
    if classification:
        lines.append("[classification.plugins]\n")
        for k, v in classification.items():
            lines.append(f"{k} = {json.dumps(v)}\n")
        lines.append("\n")
    for repo_key, manifests in repo_manifests.items():
        repo_path = tmp_path / repo_key
        repo_path.mkdir()
        for filename, content in manifests.items():
            (repo_path / filename).write_text(
                json.dumps(content) if isinstance(content, dict) else content
            )
        lines.append(f"[repos.{repo_key}]\n")
        lines.append(f'path = "{repo_path}"\n')
        lines.append('languages = ["python"]\n\n')
    (depgraph_dir / "project.toml").write_text("".join(lines))
    return Context.from_data_dir(logigraph_dir)


def test_cues_load_web_api_defaults_when_express_in_deps(tmp_path):
    """A repo with express in package.json triggers web-api activation:
    cues.entrypoint_kinds contains "endpoint" and mutation_methods has
    the four mutating verbs."""
    ctx = _make_project(tmp_path, repo_manifests={
        "api": {"package.json": {"dependencies": {"express": "^4.0.0"}}},
    })
    cues = _load_logigraph_cues(ctx)
    assert "endpoint" in cues.entrypoint_kinds
    assert "model" in cues.sink_kinds
    assert {"POST", "PUT", "DELETE", "PATCH"} <= cues.mutation_methods


def test_cues_load_cli_shape_when_bin_dir_present(tmp_path):
    """A repo with a bin/ directory triggers cli activation: cues
    surface `command` as the entrypoint kind and `util` as the sink
    kind, with NO mutation_methods (CLIs take argv, not HTTP verbs)."""
    bin_layout = {"bin": "EXEC"}  # placeholder; we create the dir manually below
    ctx = _make_project(tmp_path, repo_manifests={"tool": {}})
    bin_dir = tmp_path / "tool" / "bin"
    bin_dir.mkdir()
    (bin_dir / "mytool").write_text("#!/usr/bin/env python\n")
    cues = _load_logigraph_cues(ctx)
    assert "command" in cues.entrypoint_kinds
    assert "util" in cues.sink_kinds
    # CLI tools shouldn't filter by HTTP verbs
    assert cues.mutation_methods == set()


def test_cues_empty_when_no_manifests_and_no_overrides(tmp_path):
    """A repo with no manifests and no project.toml classification
    overrides yields empty entrypoint_kinds — process-rank will fall
    back to its built-in defaults and log a configure-your-plugins
    warning."""
    ctx = _make_project(tmp_path, repo_manifests={"empty": {}})
    cues = _load_logigraph_cues(ctx)
    # general:logigraph activates but contributes nothing.
    # No framework plugin auto-detected -> empty cue surface.
    assert cues.entrypoint_kinds == set()


def test_explicit_enable_brings_in_plugin_without_manifest(tmp_path):
    """`[classification.plugins] enable = ["web-api"]` forces web-api
    active even without a manifest signaling it — useful for synthetic
    test corpora that don't ship a package.json."""
    ctx = _make_project(
        tmp_path,
        repo_manifests={"empty": {}},
        classification={"enable": ["web-api"]},
    )
    cues = _load_logigraph_cues(ctx)
    assert "endpoint" in cues.entrypoint_kinds


def test_disable_vetoes_auto_detected_plugin(tmp_path):
    """A manifest that would auto-activate `nextjs` can be vetoed via
    `[classification.plugins] disable = ["nextjs"]`."""
    ctx = _make_project(
        tmp_path,
        repo_manifests={
            "web": {"package.json": {"dependencies": {"next": "^14.0.0"}}}
        },
        classification={"disable": ["nextjs"]},
    )
    cues = _load_logigraph_cues(ctx)
    # nextjs is what contributes ui_entry_path_globs in our shipped set
    # for next-based projects; vetoed -> empty.
    assert cues.ui_entry_path_globs == set()


def test_multi_repo_cues_union(tmp_path):
    """A project with a fastapi backend repo and a nextjs frontend repo
    unions cues from both: web-api contributes mutation_methods,
    nextjs contributes ui_entry_path_globs."""
    ctx = _make_project(tmp_path, repo_manifests={
        "api": {"pyproject.toml": '[project]\ndependencies = ["fastapi"]\n'},
        "web": {"package.json": {"dependencies": {"next": "^14.0.0"}}},
    })
    cues = _load_logigraph_cues(ctx)
    assert "endpoint" in cues.entrypoint_kinds
    assert cues.mutation_methods  # web-api contribution
    assert cues.ui_entry_path_globs  # nextjs contribution
