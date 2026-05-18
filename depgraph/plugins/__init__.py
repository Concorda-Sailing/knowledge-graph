"""Plugin registry — discover, activate, and union cues across plugins.

Public entry point: `build_config(repo_path, *, enable=None, disable=None,
auto=True) -> ClassificationConfig`. Builds the per-repo cue config by:

1. Walking `depgraph.plugins.<name>` subpackages, importing each, calling
   its `make_plugin()` factory.
2. Filtering to the active set: detector fires AND not in `disable`, OR
   forced on via `enable`.
3. Unioning each active plugin's `LanguageCues` per language.

The `general/*` plugins always activate; they carry the language-baseline
cues that aren't framework-specific.
"""
from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

from depgraph.lib.classification.config import (
    ClassificationConfig,
    LanguageCues,
)
from depgraph.plugins.base import Plugin


def _discover_plugins() -> list[Plugin]:
    """Walk depgraph.plugins.* and load every `make_plugin` factory."""
    import depgraph.plugins as pkg

    plugins: list[Plugin] = []
    for module_info in pkgutil.iter_modules(pkg.__path__, prefix=f"{pkg.__name__}."):
        # Plugins are subpackages (each lives in its own directory),
        # not top-level modules — skip base.py / __init__.py.
        if not module_info.ispkg:
            continue
        try:
            sub = importlib.import_module(f"{module_info.name}.plugin")
        except ModuleNotFoundError:
            # Some subpackages (general/) ship multiple plugin modules.
            sub = importlib.import_module(module_info.name)
        for attr in dir(sub):
            obj = getattr(sub, attr)
            if isinstance(obj, Plugin):
                plugins.append(obj)
    return plugins


def _merge_cues(a: LanguageCues, b: LanguageCues) -> LanguageCues:
    return LanguageCues(
        route_decorators=a.route_decorators | b.route_decorators,
        orm_base_classes=a.orm_base_classes | b.orm_base_classes,
        test_framework_primitives=a.test_framework_primitives | b.test_framework_primitives,
        hook_call_names=a.hook_call_names | b.hook_call_names,
        orm_schema_link_vias=a.orm_schema_link_vias | b.orm_schema_link_vias,
    )


def build_config(
    repo_path: Path,
    *,
    enable: list[str] | None = None,
    disable: list[str] | None = None,
    auto: bool = True,
) -> tuple[ClassificationConfig, list[str]]:
    """Build the active ClassificationConfig for a single repo.

    Returns (config, active_plugin_names) so the caller can log which
    plugins fired.
    """
    enable_set = set(enable or [])
    disable_set = set(disable or [])
    plugins = _discover_plugins()
    languages: dict[str, LanguageCues] = {}
    active_names: list[str] = []

    for p in plugins:
        is_general = p.name.startswith("general:")
        if p.name in disable_set:
            continue
        if p.name in enable_set:
            active = True
        elif is_general:
            active = True
        elif auto:
            try:
                active = p.detect(repo_path)
            except Exception:
                active = False
        else:
            active = False
        if not active:
            continue
        active_names.append(p.name)
        for lang, cues in p.cues.items():
            if lang in languages:
                languages[lang] = _merge_cues(languages[lang], cues)
            else:
                # Copy so later unions don't mutate the plugin's static cues.
                languages[lang] = LanguageCues(
                    route_decorators=set(cues.route_decorators),
                    orm_base_classes=set(cues.orm_base_classes),
                    test_framework_primitives=set(cues.test_framework_primitives),
                    hook_call_names=set(cues.hook_call_names),
                    orm_schema_link_vias=set(cues.orm_schema_link_vias),
                )

    active_names.sort()
    return ClassificationConfig(languages=languages), active_names


def build_config_for_repos(
    repo_paths: dict[str, Path],
    *,
    enable: list[str] | None = None,
    disable: list[str] | None = None,
    auto: bool = True,
) -> tuple[ClassificationConfig, dict[str, list[str]]]:
    """Multi-repo variant — unions cues across every repo's active set.

    Returns (config, {repo_key: active_plugin_names}) so the caller can log
    per-repo plugin activation.
    """
    merged: dict[str, LanguageCues] = {}
    by_repo: dict[str, list[str]] = {}
    for key, path in repo_paths.items():
        cfg, names = build_config(path, enable=enable, disable=disable, auto=auto)
        by_repo[key] = names
        for lang, cues in cfg.languages.items():
            if lang in merged:
                merged[lang] = _merge_cues(merged[lang], cues)
            else:
                merged[lang] = cues
    return ClassificationConfig(languages=merged), by_repo
