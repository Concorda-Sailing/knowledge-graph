"""Plugin registry — discovery + per-repo activation."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from depgraph.plugins import (
    _discover_plugins,
    build_config,
    build_config_for_repos,
)


def test_discovers_general_baselines_and_framework_plugins():
    names = {p.name for p in _discover_plugins()}
    # Always-on baselines
    assert "general:python" in names
    assert "general:typescript" in names
    # Framework plugins shipped at v0
    assert {"react", "vitest", "fastapi", "sqlalchemy", "pytest", "express", "prisma"} <= names


def test_general_plugins_always_active_with_no_manifests(tmp_path):
    cfg, active = build_config(tmp_path, auto=True)
    assert "general:python" in active
    assert "general:typescript" in active
    # No frameworks should detect on an empty dir
    assert "react" not in active
    assert "fastapi" not in active


def test_react_detects_from_package_json(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({
        "name": "demo",
        "dependencies": {"react": "^18.0.0"},
    }))
    cfg, active = build_config(tmp_path, auto=True)
    assert "react" in active
    ts_cues = cfg.languages["typescript"]
    assert "useState" in ts_cues.hook_call_names
    assert "useEffect" in ts_cues.hook_call_names


def test_fastapi_detects_from_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\ndependencies = ["fastapi>=0.100", "uvicorn"]\n'
    )
    cfg, active = build_config(tmp_path, auto=True)
    assert "fastapi" in active
    py_cues = cfg.languages["python"]
    assert "router.get" in py_cues.route_decorators
    assert "app.post" in py_cues.route_decorators


def test_vitest_detects_from_marker_file(tmp_path):
    (tmp_path / "vitest.config.ts").write_text("export default {}\n")
    cfg, active = build_config(tmp_path, auto=True)
    assert "vitest" in active
    ts_cues = cfg.languages["typescript"]
    assert {"it", "test", "describe", "expect"} <= ts_cues.test_framework_primitives


def test_disable_vetoes_auto_detected_plugin(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({
        "dependencies": {"react": "^18.0.0", "vitest": "^1.0.0"},
    }))
    _, active = build_config(tmp_path, disable=["react"], auto=True)
    assert "react" not in active
    assert "vitest" in active


def test_enable_forces_plugin_even_without_manifest(tmp_path):
    _, active = build_config(tmp_path, enable=["fastapi"], auto=True)
    assert "fastapi" in active


def test_auto_false_disables_detection(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({
        "dependencies": {"react": "^18.0.0"},
    }))
    _, active = build_config(tmp_path, auto=False)
    # Only general:* baselines should be on
    assert active == ["general:python", "general:typescript"]


def test_local_plugin_loaded_from_directory(tmp_path):
    """A project-private plugin file under `local_plugin_paths` loads and
    contributes cues just like a shipped plugin."""
    plug_dir = tmp_path / "plugins"
    plug_dir.mkdir()
    (plug_dir / "internal_orm.py").write_text(
        "from depgraph.lib.classification.config import LanguageCues\n"
        "from depgraph.plugins.base import Plugin\n"
        "PLUGIN = Plugin(\n"
        "    name='acme-internal',\n"
        "    detect=lambda p: True,\n"
        "    cues={'python': LanguageCues(orm_base_classes={'AcmeModel'})},\n"
        ")\n"
    )
    repo = tmp_path / "repo"
    repo.mkdir()
    cfg, active = build_config(repo, local_plugin_paths=[plug_dir])
    assert "acme-internal" in active
    assert "AcmeModel" in cfg.languages["python"].orm_base_classes


def test_local_plugin_overrides_shipped_on_name_collision(tmp_path):
    """A local plugin named the same as a shipped one replaces it."""
    plug_dir = tmp_path / "plugins"
    plug_dir.mkdir()
    (plug_dir / "react_override.py").write_text(
        "from depgraph.lib.classification.config import LanguageCues\n"
        "from depgraph.plugins.base import Plugin\n"
        "PLUGIN = Plugin(\n"
        "    name='react',\n"
        "    detect=lambda p: True,\n"
        "    cues={'typescript': LanguageCues(hook_call_names={'useAcmeOnly'})},\n"
        ")\n"
    )
    cfg, active = build_config(tmp_path, local_plugin_paths=[plug_dir])
    assert "react" in active
    hooks = cfg.languages["typescript"].hook_call_names
    # Override semantics — shipped React's useState is gone, replaced by local
    assert "useAcmeOnly" in hooks
    assert "useState" not in hooks


def test_local_plugin_bad_file_does_not_abort(tmp_path, capsys):
    """A broken local plugin reports on stderr but doesn't break the build."""
    plug_dir = tmp_path / "plugins"
    plug_dir.mkdir()
    (plug_dir / "broken.py").write_text("this is not valid python )(\n")
    (plug_dir / "good.py").write_text(
        "from depgraph.lib.classification.config import LanguageCues\n"
        "from depgraph.plugins.base import Plugin\n"
        "PLUGIN = Plugin(name='good', detect=lambda p: True,\n"
        "                cues={'python': LanguageCues()})\n"
    )
    _, active = build_config(tmp_path, local_plugin_paths=[plug_dir])
    assert "good" in active
    err = capsys.readouterr().err
    assert "failed to load local plugin" in err
    assert "broken.py" in err


def test_build_config_for_repos_unions_across_repos(tmp_path):
    api = tmp_path / "api"; api.mkdir()
    (api / "pyproject.toml").write_text('[project]\ndependencies = ["fastapi"]\n')
    web = tmp_path / "web"; web.mkdir()
    (web / "package.json").write_text(json.dumps({"dependencies": {"react": "^18"}}))

    cfg, by_repo = build_config_for_repos({"api": api, "web": web})
    assert "fastapi" in by_repo["api"]
    assert "react" in by_repo["web"]
    # Union: api contributes python.route_decorators, web contributes ts.hook_call_names
    assert cfg.languages["python"].route_decorators
    assert cfg.languages["typescript"].hook_call_names
