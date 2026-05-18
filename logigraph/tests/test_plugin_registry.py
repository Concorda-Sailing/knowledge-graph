"""Logigraph plugin registry — discovery, activation, override semantics.

Mirrors `depgraph/tests/test_plugin_registry.py`. The generic registry
machinery is shared via `kg.shared.plugins`; these tests cover the
logigraph-side cue type (`LogigraphCues`) and the framework plugins
shipped under `logigraph.plugins.*`.
"""
from __future__ import annotations

import json

import pytest

from logigraph.plugins import (
    _discover_shipped_plugins,
    build_config,
    build_config_for_repos,
    get_logigraph_cues,
)


def test_discovers_general_baseline_and_framework_plugins():
    names = {p.name for p in _discover_shipped_plugins()}
    assert "general:logigraph" in names
    # Phase-1 framework plugins
    assert {
        "web-api", "nextjs", "nuxt", "cli", "event-driven", "data-pipeline",
    } <= names


def test_general_baseline_always_active_with_no_manifests(tmp_path):
    _, active = build_config(tmp_path, auto=True)
    assert "general:logigraph" in active
    # Empty dir — no framework plugins should activate
    assert "web-api" not in active
    assert "cli" not in active


def test_web_api_detects_from_express_dep(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({
        "dependencies": {"express": "^4.0.0"},
    }))
    cues_by_key, active = build_config(tmp_path, auto=True)
    assert "web-api" in active
    cues = get_logigraph_cues(cues_by_key)
    assert "endpoint" in cues.entrypoint_kinds
    assert "model" in cues.sink_kinds
    assert {"POST", "PUT", "DELETE", "PATCH"} <= cues.mutation_methods


def test_web_api_detects_from_fastapi_dep(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\ndependencies = ["fastapi"]\n'
    )
    _, active = build_config(tmp_path, auto=True)
    assert "web-api" in active


def test_nextjs_contributes_ui_entry_globs(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({
        "dependencies": {"next": "^14.0.0"},
    }))
    cues_by_key, active = build_config(tmp_path, auto=True)
    assert "nextjs" in active
    cues = get_logigraph_cues(cues_by_key)
    assert any("page" in g for g in cues.ui_entry_path_globs)


def test_cli_detects_from_bin_directory(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "mytool").write_text("#!/usr/bin/env python\n")
    cues_by_key, active = build_config(tmp_path, auto=True)
    assert "cli" in active
    cues = get_logigraph_cues(cues_by_key)
    assert "command" in cues.entrypoint_kinds
    # CLIs don't have HTTP verbs — mutation_methods should be empty
    assert cues.mutation_methods == set()


def test_data_pipeline_detects_from_prefect_dep(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\ndependencies = ["prefect>=2.0"]\n'
    )
    cues_by_key, active = build_config(tmp_path, auto=True)
    assert "data-pipeline" in active
    cues = get_logigraph_cues(cues_by_key)
    assert "task" in cues.entrypoint_kinds


def test_event_driven_detects_from_celery_dep(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\ndependencies = ["celery"]\n'
    )
    _, active = build_config(tmp_path, auto=True)
    assert "event-driven" in active


def test_disable_vetoes_auto_detected_plugin(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({
        "dependencies": {"express": "^4.0.0", "next": "^14.0.0"},
    }))
    _, active = build_config(tmp_path, disable=["nextjs"], auto=True)
    assert "nextjs" not in active
    assert "web-api" in active


def test_enable_forces_plugin_without_manifest(tmp_path):
    _, active = build_config(tmp_path, enable=["web-api"], auto=True)
    assert "web-api" in active


def test_auto_false_disables_detection(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({
        "dependencies": {"express": "^4.0.0"},
    }))
    _, active = build_config(tmp_path, auto=False)
    # Only the always-on baseline activates without auto-detect
    assert active == ["general:logigraph"]


def test_local_plugin_loaded_from_directory(tmp_path):
    """Project-private logigraph plugins work the same way depgraph's
    local plugins do — file under `local_plugin_paths`, exports
    `PLUGIN: Plugin = Plugin(...)`. Phase 1 doesn't add any
    logigraph-specific machinery here; this confirms the generic
    `kg.shared.plugins` local-loader works for LogigraphCues too."""
    plug_dir = tmp_path / "plugins"
    plug_dir.mkdir()
    (plug_dir / "acme_internal.py").write_text(
        "from kg.shared.plugins import Plugin\n"
        "from logigraph.plugins.base import LogigraphCues\n"
        "PLUGIN = Plugin(\n"
        "    name='acme-internal',\n"
        "    detect=lambda p: True,\n"
        "    cues={'logigraph': LogigraphCues(entrypoint_kinds={'acme_handler'})},\n"
        ")\n"
    )
    repo = tmp_path / "repo"
    repo.mkdir()
    cues_by_key, active = build_config(repo, local_plugin_paths=[plug_dir])
    assert "acme-internal" in active
    cues = get_logigraph_cues(cues_by_key)
    assert "acme_handler" in cues.entrypoint_kinds


def test_kind_weights_merge_takes_max_per_kind(tmp_path):
    """Two plugins disagreeing on the weight for a kind: the higher
    weight wins. Matches the additive-cues model the other fields use."""
    plug_dir = tmp_path / "plugins"
    plug_dir.mkdir()
    (plug_dir / "low.py").write_text(
        "from kg.shared.plugins import Plugin\n"
        "from logigraph.plugins.base import LogigraphCues\n"
        "PLUGIN = Plugin(\n"
        "    name='low',\n"
        "    detect=lambda p: True,\n"
        "    cues={'logigraph': LogigraphCues(kind_weights={'service': 0.3})},\n"
        ")\n"
    )
    (plug_dir / "high.py").write_text(
        "from kg.shared.plugins import Plugin\n"
        "from logigraph.plugins.base import LogigraphCues\n"
        "PLUGIN = Plugin(\n"
        "    name='high',\n"
        "    detect=lambda p: True,\n"
        "    cues={'logigraph': LogigraphCues(kind_weights={'service': 0.9})},\n"
        ")\n"
    )
    cues_by_key, _ = build_config(tmp_path, local_plugin_paths=[plug_dir])
    cues = get_logigraph_cues(cues_by_key)
    assert cues.kind_weights["service"] == 0.9


def test_build_config_for_repos_unions_across_repos(tmp_path):
    api = tmp_path / "api"; api.mkdir()
    (api / "pyproject.toml").write_text('[project]\ndependencies = ["fastapi"]\n')
    web = tmp_path / "web"; web.mkdir()
    (web / "package.json").write_text(json.dumps({"dependencies": {"next": "^14"}}))

    cues_by_key, by_repo = build_config_for_repos({"api": api, "web": web})
    assert "web-api" in by_repo["api"]
    assert "nextjs" in by_repo["web"]
    cues = get_logigraph_cues(cues_by_key)
    # api repo contributed entrypoint_kinds + mutation_methods (web-api);
    # web repo contributed ui_entry_path_globs (nextjs). Union should
    # contain both.
    assert "endpoint" in cues.entrypoint_kinds
    assert cues.ui_entry_path_globs
