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
    # Tier 1+2 React-ecosystem cue plugins
    assert {
        "mocha", "redux", "tanstack-query", "swr",
        "nextjs-hooks", "react-i18next", "react-intl", "growthbook",
    } <= names


def test_every_framework_plugin_declares_target_versions():
    """The line-in-the-sand check: every plugin that targets a specific
    framework must pin the version it was authored against. Only the
    `general:*` always-on baselines are exempt — they don't target any
    one framework. Without this gate, plugins drift silently and
    reviewers can't tell which ones still match the current major."""
    for p in _discover_plugins():
        if p.name.startswith("general:"):
            continue
        assert p.target_versions, (
            f"plugin {p.name!r} is missing `target_versions=...`; "
            f"every framework plugin must pin the version its cues were "
            f"authored against (e.g. target_versions={{\"react\": \"19.2\"}})"
        )
        for lib, ver in p.target_versions.items():
            assert lib and isinstance(lib, str), (
                f"{p.name}: bad target_versions key {lib!r}"
            )
            assert ver and isinstance(ver, str), (
                f"{p.name}: bad target_versions value {ver!r} for {lib!r}"
            )


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
        "from kg.shared.plugins import Plugin\n"
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
        "from kg.shared.plugins import Plugin\n"
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
        "from kg.shared.plugins import Plugin\n"
        "PLUGIN = Plugin(name='good', detect=lambda p: True,\n"
        "                cues={'python': LanguageCues()})\n"
    )
    _, active = build_config(tmp_path, local_plugin_paths=[plug_dir])
    assert "good" in active
    err = capsys.readouterr().err
    assert "failed to load local plugin" in err
    assert "broken.py" in err


def test_mocha_detects_from_package_json(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({
        "dependencies": {"mocha": "^10.0.0"},
    }))
    cfg, active = build_config(tmp_path, auto=True)
    assert "mocha" in active
    prims = cfg.languages["typescript"].test_framework_primitives
    assert {"describe", "it", "before", "after", "beforeEach"} <= prims


def test_mocha_detects_from_mocharc_marker(tmp_path):
    (tmp_path / ".mocharc.json").write_text("{}\n")
    _, active = build_config(tmp_path, auto=True)
    assert "mocha" in active


def test_redux_detects_and_contributes_hooks(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({
        "dependencies": {"react-redux": "^9.0.0"},
    }))
    cfg, active = build_config(tmp_path, auto=True)
    assert "redux" in active
    hooks = cfg.languages["typescript"].hook_call_names
    assert {"useSelector", "useDispatch"} <= hooks


def test_tanstack_query_detects_v4_and_v3(tmp_path):
    # v4+
    (tmp_path / "package.json").write_text(json.dumps({
        "dependencies": {"@tanstack/react-query": "^5.0.0"},
    }))
    cfg, active = build_config(tmp_path, auto=True)
    assert "tanstack-query" in active
    assert {"useQuery", "useMutation", "useInfiniteQuery"} <= cfg.languages["typescript"].hook_call_names


def test_swr_detects_and_contributes_hooks(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({
        "dependencies": {"swr": "^2.0.0"},
    }))
    cfg, active = build_config(tmp_path, auto=True)
    assert "swr" in active
    assert "useSWR" in cfg.languages["typescript"].hook_call_names


def test_nextjs_hooks_detects_and_contributes(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({
        "dependencies": {"next": "^16.0.0"},
    }))
    cfg, active = build_config(tmp_path, auto=True)
    assert "nextjs-hooks" in active
    hooks = cfg.languages["typescript"].hook_call_names
    assert {"useRouter", "usePathname", "useSearchParams"} <= hooks


def test_react_i18next_detects(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({
        "dependencies": {"react-i18next": "^14.0.0"},
    }))
    cfg, active = build_config(tmp_path, auto=True)
    assert "react-i18next" in active
    assert "useTranslation" in cfg.languages["typescript"].hook_call_names


def test_react_i18next_via_next_i18next(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({
        "dependencies": {"next-i18next": "^15.0.0"},
    }))
    _, active = build_config(tmp_path, auto=True)
    assert "react-i18next" in active


def test_react_intl_detects(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({
        "dependencies": {"react-intl": "^6.0.0"},
    }))
    cfg, active = build_config(tmp_path, auto=True)
    assert "react-intl" in active
    assert "useIntl" in cfg.languages["typescript"].hook_call_names


def test_growthbook_detects(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({
        "dependencies": {"@growthbook/growthbook-react": "^1.0.0"},
    }))
    cfg, active = build_config(tmp_path, auto=True)
    assert "growthbook" in active
    hooks = cfg.languages["typescript"].hook_call_names
    assert {"useFeature", "useFeatureValue", "useFeatureIsOn"} <= hooks


def test_real_fe_landing_page_stack_unions_correctly(tmp_path):
    """End-to-end: a realistic Next.js project with Next + SWR + redux-form +
    react-i18next + GrowthBook + Sentry/Next + react-bootstrap unions cues
    from every relevant plugin."""
    (tmp_path / "package.json").write_text(json.dumps({
        "dependencies": {
            "next": "^16.2.0",
            "react": "^19.2.0",
            "swr": "^2.0.0",
            "react-i18next": "^14.0.0",
            "next-i18next": "^15.0.0",
            "@growthbook/growthbook-react": "^1.0.0",
            "react-bootstrap": "^2.0.0",   # no plugin — just noise
            "@sentry/nextjs": "^7.0.0",     # no plugin — just noise
        },
    }))
    cfg, active = build_config(tmp_path, auto=True)
    # Every Tier 1+2 plugin matched by this stack
    assert {"react", "nextjs-hooks", "swr", "react-i18next", "growthbook"} <= set(active)
    hooks = cfg.languages["typescript"].hook_call_names
    # Built-in React hooks
    assert "useState" in hooks
    # Next.js navigation
    assert "useRouter" in hooks
    # Data fetching
    assert "useSWR" in hooks
    # i18n
    assert "useTranslation" in hooks
    # Feature flags
    assert "useFeature" in hooks


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


def test_build_config_languages_filter_drops_offlanguage_plugins(tmp_path):
    """A Python-only repo must not activate `general:typescript` etc. (#15)."""
    (tmp_path / "pyproject.toml").write_text('[project]\ndependencies = []\n')

    cfg, active = build_config(tmp_path, languages=["python"])
    assert "general:python" in active
    assert "general:typescript" not in active
    # No TS cues should bleed in.
    assert "typescript" not in cfg.languages


def test_build_config_languages_none_keeps_legacy_behavior(tmp_path):
    """languages=None preserves the pre-fix behavior (every general:* fires)."""
    cfg, active = build_config(tmp_path, languages=None)
    assert "general:python" in active
    assert "general:typescript" in active


def test_build_config_for_repos_filters_per_repo_languages(tmp_path):
    """languages_by_repo scopes each repo's plugin set independently (#15)."""
    api = tmp_path / "api"; api.mkdir()
    (api / "pyproject.toml").write_text('[project]\ndependencies = []\n')
    web = tmp_path / "web"; web.mkdir()
    (web / "package.json").write_text(json.dumps({"dependencies": {}}))

    _, by_repo = build_config_for_repos(
        {"api": api, "web": web},
        languages_by_repo={"api": ["python"], "web": ["typescript"]},
    )
    assert "general:python" in by_repo["api"]
    assert "general:typescript" not in by_repo["api"]
    assert "general:typescript" in by_repo["web"]
    assert "general:python" not in by_repo["web"]


def test_build_config_explicit_enable_overrides_language_filter(tmp_path):
    """An explicit `enable=["general:typescript"]` overrides the language
    filter — the user is forcing the plugin on, that wins (#15)."""
    (tmp_path / "pyproject.toml").write_text('[project]\ndependencies = []\n')
    _, active = build_config(
        tmp_path, languages=["python"], enable=["general:typescript"],
    )
    assert "general:typescript" in active
