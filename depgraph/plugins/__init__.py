"""Depgraph plugin wrapper over the generic registry in `kg.shared.plugins`.

The generic core handles discovery, activation, and local-plugin loading.
This module owns the depgraph-specific cue type (`LanguageCues`), the
merger + copier callbacks the generic core delegates to, and the
public entry points that return a typed `ClassificationConfig`.

Public API (unchanged across the Phase 0 refactor):
    build_config(repo_path, **kwargs) -> (ClassificationConfig, list[str])
    build_config_for_repos(repo_paths, **kwargs) -> (ClassificationConfig, dict)
"""
from __future__ import annotations

from pathlib import Path

from kg.shared.plugins import build_config_generic
from depgraph.lib.classification.config import (
    ClassificationConfig,
    LanguageCues,
)

# Re-exports for back-compat — existing tests and external callers import
# these directly from `depgraph.plugins`. The internals come from
# `kg.shared.plugins` now, but the public surface here is unchanged.
from kg.shared.plugins import (
    Plugin,
    _load_local_plugins,
)
from kg.shared.plugins import _discover_plugins as _generic_discover_plugins
from kg.shared.plugins import _discover_shipped_plugins as _generic_discover_shipped


_DEPGRAPH_PLUGINS_PKG = "depgraph.plugins"


def _discover_shipped_plugins() -> list[Plugin]:
    """Depgraph-curried form of the generic discoverer.

    Existing callers (tests, default_config) call this with no args
    expecting depgraph plugins; the generic core requires a package
    name. Curry it here so the public surface in `depgraph.plugins`
    stays unchanged."""
    return _generic_discover_shipped(_DEPGRAPH_PLUGINS_PKG)


def _discover_plugins(local_plugin_paths: list[Path] | None = None) -> list[Plugin]:
    """Depgraph-curried form of the generic discoverer with local-plugin
    support. Equivalent to `kg.shared.plugins._discover_plugins(
    "depgraph.plugins", local_plugin_paths=...)`."""
    return _generic_discover_plugins(
        _DEPGRAPH_PLUGINS_PKG, local_plugin_paths=local_plugin_paths,
    )


def _merge_language_cues(a: LanguageCues, b: LanguageCues) -> LanguageCues:
    """Union semantics across every LanguageCues field. Identity element
    is the empty cue set; binary op is set union."""
    return LanguageCues(
        route_decorators=a.route_decorators | b.route_decorators,
        orm_base_classes=a.orm_base_classes | b.orm_base_classes,
        test_framework_primitives=a.test_framework_primitives | b.test_framework_primitives,
        hook_call_names=a.hook_call_names | b.hook_call_names,
        orm_schema_link_vias=a.orm_schema_link_vias | b.orm_schema_link_vias,
    )


def _copy_language_cues(cues: LanguageCues) -> LanguageCues:
    """Defensive copy so later merges don't mutate the static cue values
    held inside plugin modules' PLUGIN constants."""
    return LanguageCues(
        route_decorators=set(cues.route_decorators),
        orm_base_classes=set(cues.orm_base_classes),
        test_framework_primitives=set(cues.test_framework_primitives),
        hook_call_names=set(cues.hook_call_names),
        orm_schema_link_vias=set(cues.orm_schema_link_vias),
    )


# Module-level alias for code that previously imported `_merge_cues`.
_merge_cues = _merge_language_cues


def build_config(
    repo_path: Path,
    *,
    enable: list[str] | None = None,
    disable: list[str] | None = None,
    auto: bool = True,
    local_plugin_paths: list[Path] | None = None,
) -> tuple[ClassificationConfig, list[str]]:
    """Build the active ClassificationConfig for a single repo.

    Returns `(config, active_plugin_names)` so the caller can log which
    plugins fired.
    """
    cues_by_lang, active_names = build_config_generic(
        repo_path,
        plugins_pkg=_DEPGRAPH_PLUGINS_PKG,
        cue_merger=_merge_language_cues,
        cue_copier=_copy_language_cues,
        enable=enable, disable=disable, auto=auto,
        local_plugin_paths=local_plugin_paths,
    )
    return ClassificationConfig(languages=cues_by_lang), active_names


def build_config_for_repos(
    repo_paths: dict[str, Path],
    *,
    enable: list[str] | None = None,
    disable: list[str] | None = None,
    auto: bool = True,
    local_plugin_paths: list[Path] | None = None,
) -> tuple[ClassificationConfig, dict[str, list[str]]]:
    """Multi-repo variant — unions cues across every repo's active set.

    Returns `(config, {repo_key: active_plugin_names})`. Local plugin
    paths apply across all repos in the project; the generic core
    re-discovers them per-repo so a project's private detectors fire
    against every repo independently.
    """
    merged: dict[str, LanguageCues] = {}
    by_repo: dict[str, list[str]] = {}
    for key, path in repo_paths.items():
        cfg, names = build_config(
            path, enable=enable, disable=disable, auto=auto,
            local_plugin_paths=local_plugin_paths,
        )
        by_repo[key] = names
        for lang, cues in cfg.languages.items():
            if lang in merged:
                merged[lang] = _merge_language_cues(merged[lang], cues)
            else:
                merged[lang] = cues
    return ClassificationConfig(languages=merged), by_repo
