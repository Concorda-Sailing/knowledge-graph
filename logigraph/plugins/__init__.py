"""Logigraph plugin wrapper over the generic registry in `kg.shared.plugins`.

The generic core handles discovery, activation, and local-plugin loading.
This module owns the logigraph-specific cue type (`LogigraphCues`), the
merger + copier callbacks the generic core delegates to, and the public
entry points returning a per-language LogigraphCues map.

Sibling to `depgraph.plugins`: same shape, different cue type.

Public API:
    build_config(repo_path, **kwargs) -> (dict[str, LogigraphCues], list[str])
    build_config_for_repos(repo_paths, **kwargs) -> (dict[str, LogigraphCues], dict)
"""
from __future__ import annotations

from pathlib import Path

from kg.shared.plugins import build_config_generic
from kg.shared.plugins import Plugin  # noqa: F401 (re-export for plugin authors)
from kg.shared.plugins import _discover_plugins as _generic_discover_plugins
from kg.shared.plugins import _discover_shipped_plugins as _generic_discover_shipped
from kg.shared.plugins import _load_local_plugins  # noqa: F401 (re-export)

from logigraph.plugins.base import LogigraphCues


_LOGIGRAPH_PLUGINS_PKG = "logigraph.plugins"


def _merge_logigraph_cues(a: LogigraphCues, b: LogigraphCues) -> LogigraphCues:
    """Union semantics across every set field. `kind_weights` (the one
    dict field) merges by max-value-per-key — if two plugins disagree on
    the weight for a kind, the higher one wins; this matches the
    "additive cues" model the rest of the fields follow."""
    merged_weights = dict(a.kind_weights)
    for k, v in b.kind_weights.items():
        merged_weights[k] = max(merged_weights.get(k, 0.0), v)
    return LogigraphCues(
        entrypoint_kinds=a.entrypoint_kinds | b.entrypoint_kinds,
        sink_kinds=a.sink_kinds | b.sink_kinds,
        mutation_methods=a.mutation_methods | b.mutation_methods,
        ui_entry_path_globs=a.ui_entry_path_globs | b.ui_entry_path_globs,
        api_client_path_globs=a.api_client_path_globs | b.api_client_path_globs,
        test_path_globs=a.test_path_globs | b.test_path_globs,
        headless_skip_kinds=a.headless_skip_kinds | b.headless_skip_kinds,
        kind_weights=merged_weights,
    )


def _copy_logigraph_cues(cues: LogigraphCues) -> LogigraphCues:
    """Defensive copy so later merges don't mutate the static cue values
    held inside plugin modules' PLUGIN constants."""
    return LogigraphCues(
        entrypoint_kinds=set(cues.entrypoint_kinds),
        sink_kinds=set(cues.sink_kinds),
        mutation_methods=set(cues.mutation_methods),
        ui_entry_path_globs=set(cues.ui_entry_path_globs),
        api_client_path_globs=set(cues.api_client_path_globs),
        test_path_globs=set(cues.test_path_globs),
        headless_skip_kinds=set(cues.headless_skip_kinds),
        kind_weights=dict(cues.kind_weights),
    )


def _discover_shipped_plugins():
    """Curried form: returns the logigraph package's shipped plugins."""
    return _generic_discover_shipped(_LOGIGRAPH_PLUGINS_PKG)


def _discover_plugins(local_plugin_paths: list[Path] | None = None):
    """Curried form: walks the logigraph plugins namespace plus any
    project-local plugin paths."""
    return _generic_discover_plugins(
        _LOGIGRAPH_PLUGINS_PKG, local_plugin_paths=local_plugin_paths,
    )


def build_config(
    repo_path: Path,
    *,
    enable: list[str] | None = None,
    disable: list[str] | None = None,
    auto: bool = True,
    local_plugin_paths: list[Path] | None = None,
) -> tuple[dict[str, LogigraphCues], list[str]]:
    """Build the active LogigraphCues set for a single repo.

    Returns `(cues_by_subsystem_key, active_plugin_names)`. The
    subsystem key is currently always `"logigraph"` (one cue type, one
    key) — the dict shape parallels depgraph's per-language map so
    future per-language cues (e.g. if logigraph signals diverge per
    language) are a non-breaking extension.
    """
    cues_by_key, active_names = build_config_generic(
        repo_path,
        plugins_pkg=_LOGIGRAPH_PLUGINS_PKG,
        cue_merger=_merge_logigraph_cues,
        cue_copier=_copy_logigraph_cues,
        enable=enable, disable=disable, auto=auto,
        local_plugin_paths=local_plugin_paths,
    )
    return cues_by_key, active_names


def build_config_for_repos(
    repo_paths: dict[str, Path],
    *,
    enable: list[str] | None = None,
    disable: list[str] | None = None,
    auto: bool = True,
    local_plugin_paths: list[Path] | None = None,
) -> tuple[dict[str, LogigraphCues], dict[str, list[str]]]:
    """Multi-repo variant — unions cues across every repo's active set.

    Returns `(cues_by_subsystem_key, {repo_key: active_plugin_names})`.
    """
    merged: dict[str, LogigraphCues] = {}
    by_repo: dict[str, list[str]] = {}
    for key, path in repo_paths.items():
        cues_by_key, names = build_config(
            path, enable=enable, disable=disable, auto=auto,
            local_plugin_paths=local_plugin_paths,
        )
        by_repo[key] = names
        for subsys_key, cues in cues_by_key.items():
            if subsys_key in merged:
                merged[subsys_key] = _merge_logigraph_cues(merged[subsys_key], cues)
            else:
                merged[subsys_key] = cues
    return merged, by_repo


def get_logigraph_cues(
    cues_by_key: dict[str, LogigraphCues],
) -> LogigraphCues:
    """Convenience: extract the `"logigraph"` cue entry or return an empty
    LogigraphCues if no plugin contributed. Callers in `process.py` use
    this to get a single cue object to drive their checks."""
    return cues_by_key.get("logigraph", LogigraphCues())
