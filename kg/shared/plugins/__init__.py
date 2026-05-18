"""Generic plugin registry — discovery, activation, local-plugin loading.

This package owns the cross-subsystem plugin protocol and the registry
machinery. Both depgraph and logigraph build their own typed plugin
layers on top of it: each subsystem defines its own Cues dataclass and
provides a merger + copier callback, and the generic core handles
discovery, activation, and cue contribution accumulation.

Why here: `kg.shared` is the established home for cross-graph helpers
used by both depgraph and logigraph (see `kg/shared/__init__.py` —
git, telemetry). Lifting plugin infrastructure here avoids having one
sibling subsystem (logigraph) reach into another sibling's namespace
(depgraph) for shared machinery.

The `Plugin` dataclass treats `cues` as opaque `dict[str, Any]`. The
generic core never inspects or merges those values; it just collects
them per language key and hands them to the subsystem's merger. Type
ownership stays inside each subsystem.

Usage:

    # depgraph wraps the generic core like this:
    from kg.shared.plugins import build_config_generic
    cues_by_lang, active = build_config_generic(
        repo_path,
        plugins_pkg="depgraph.plugins",
        cue_merger=_merge_language_cues,
        cue_copier=_copy_language_cues,
    )

    # logigraph wraps it the same way with its own Cues type.
"""
from __future__ import annotations

import importlib
import importlib.util
import pkgutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

# Re-export detection helpers so plugin authors can write one import:
#   from kg.shared.plugins import Plugin, has_npm_dep, has_pypi_dep
from kg.shared.plugins.detectors import (  # noqa: E402 (re-export)
    has_marker_file,
    has_npm_dep,
    has_pypi_dep,
)


# ---------------------------------------------------------------------------
# Plugin protocol
# ---------------------------------------------------------------------------

@dataclass
class Plugin:
    """A framework or convention pack a subsystem's classifier can activate.

    Generic over the cue type: `cues` is `dict[str, Any]` here so this
    module knows nothing about LanguageCues / LogigraphCues / etc. Each
    subsystem's wrapper layer knows the actual type of the cue values
    and provides merger + copier callbacks to `build_config_generic`.
    """

    name: str
    """Stable identifier (e.g. 'react', 'fastapi', 'web-api'). Used in
    project.toml enable/disable lists and in the plugin-active log line.
    Must be unique within a subsystem's plugin set."""

    detect: Callable[[Path], bool]
    """Predicate returning True when this plugin should activate for the
    given repo path. Usually reads dependency manifests or marker files.
    Should be cheap (single-digit milliseconds) and side-effect-free."""

    cues: dict[str, Any] = field(default_factory=dict)
    """Per-language (or per-kind, for logigraph) cue contributions. The
    generic core never inspects the values; it just collects them per
    key and hands them to the subsystem's merger when keys collide."""

    target_versions: dict[str, str] = field(default_factory=dict)
    """Framework name -> the specific version string the plugin's cues
    were authored and verified against. A "line in the sand": each entry
    pins ONE version (e.g. `"19.2"`, not a range like `"18.x to 19.x"`),
    so a later maintainer can compare it against the current release
    and decide whether re-verification is needed. Purely informational
    — the activation pipeline and merger ignore this field.

    Examples:
        target_versions={"react": "19.2"}
        target_versions={"@tanstack/react-query": "5.62"}
        target_versions={"express": "4.21", "fastify": "5.1"}

    Multi-framework plugins (e.g. logigraph's `web-api` which fires on
    any of express / fastify / fastapi / django / …) list every
    framework whose conventions informed the cues, each pinned to its
    own verified version. Always-on baseline plugins (`general:*`) may
    leave this empty.

    When a contributor bumps cues to track a new major, they update
    this field too — that's the audit trail. When no one has touched
    the cues, the field continues to point at the older version,
    making "this plugin hasn't been re-verified since" visible.

    Useful for:
      - Maintenance audits ("which plugins haven't been touched since
        the framework cut a new major?").
      - Future tooling: `kg plugins list --stale` style commands.
      - PR review — reviewers can spot when a contributor's claimed
        target version doesn't match the cue set they shipped."""


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def _discover_shipped_plugins(plugins_pkg: str) -> list[Plugin]:
    """Walk a plugins package and load every `Plugin` instance it exposes.

    `plugins_pkg` is the dotted package name (e.g. `"depgraph.plugins"` or
    `"logigraph.plugins"`). Each immediate subpackage is imported; either
    its `plugin` submodule (single-plugin case) or its `__init__` (when a
    subpackage groups multiple plugins, e.g. `general/` re-exports) is
    scanned for top-level `Plugin` constants.
    """
    pkg = importlib.import_module(plugins_pkg)
    plugins: list[Plugin] = []
    for module_info in pkgutil.iter_modules(pkg.__path__, prefix=f"{pkg.__name__}."):
        # Plugins are subpackages (each lives in its own directory),
        # not top-level modules — skip helper modules like base.py.
        if not module_info.ispkg:
            continue
        try:
            sub = importlib.import_module(f"{module_info.name}.plugin")
        except ModuleNotFoundError:
            # Subpackages that re-export multiple plugins via __init__.py
            # (e.g. general/ in depgraph) — fall back to the package.
            sub = importlib.import_module(module_info.name)
        for attr in dir(sub):
            obj = getattr(sub, attr)
            if isinstance(obj, Plugin):
                plugins.append(obj)
    return plugins


def _load_local_plugins(paths: list[Path]) -> list[Plugin]:
    """Load `Plugin` instances from arbitrary directories outside any
    installed package.

    Each entry can be a single `.py` file or a directory whose immediate
    `.py` children each contribute zero or more `Plugin` instances. Bad
    paths and import errors print to stderr but do NOT abort — a typo in
    one project-private plugin shouldn't break the whole regen.

    Used to load detectors for internal/proprietary frameworks that
    aren't (and shouldn't be) upstreamed.
    """
    plugins: list[Plugin] = []
    for raw in paths:
        path = Path(raw).expanduser().resolve()
        if not path.exists():
            continue
        py_files = [path] if path.is_file() and path.suffix == ".py" else (
            sorted(path.glob("*.py")) if path.is_dir() else []
        )
        for py in py_files:
            if py.name.startswith("_"):
                continue
            # Unique synthetic module name avoids collisions when two
            # local plugin dirs happen to ship same-named files.
            module_name = f"_kg_local_plugins.{py.stem}_{abs(hash(str(py)))}"
            try:
                spec = importlib.util.spec_from_file_location(module_name, py)
                if spec is None or spec.loader is None:
                    continue
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            except Exception as e:
                print(f"WARN: failed to load local plugin {py}: {e}", file=sys.stderr)
                continue
            for attr in dir(module):
                obj = getattr(module, attr)
                if isinstance(obj, Plugin):
                    plugins.append(obj)
    return plugins


def _discover_plugins(
    plugins_pkg: str,
    local_plugin_paths: list[Path] | None = None,
) -> list[Plugin]:
    """Shipped plugins from `plugins_pkg` plus any local ones. Local
    plugins override shipped ones on name collision (so a project can
    ship a custom `react` plugin that replaces the framework's React
    cues without forking the codebase)."""
    shipped = _discover_shipped_plugins(plugins_pkg)
    if not local_plugin_paths:
        return shipped
    local = _load_local_plugins(local_plugin_paths)
    local_names = {p.name for p in local}
    merged = [p for p in shipped if p.name not in local_names]
    merged.extend(local)
    return merged


# ---------------------------------------------------------------------------
# Generic config builder
# ---------------------------------------------------------------------------

def build_config_generic(
    repo_path: Path,
    *,
    plugins_pkg: str,
    cue_merger: Callable[[Any, Any], Any],
    cue_copier: Callable[[Any], Any],
    enable: list[str] | None = None,
    disable: list[str] | None = None,
    auto: bool = True,
    local_plugin_paths: list[Path] | None = None,
    allowed_cue_keys: set[str] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Build the active cue contributions for a single repo, generic
    over the cue type.

    Activation rules:
      - Plugins whose `name` starts with `"general:"` always activate.
      - `enable` forces activation regardless of detector.
      - `disable` vetoes (wins over `enable=False`, loses to explicit `enable`).
      - When `auto=True`, every other plugin runs its detector; when
        `auto=False`, only `general:*` and `enable` listings activate.
      - When `allowed_cue_keys` is set, a plugin only activates if at
        least one of its cue keys is in the set (after other rules pass).
        Depgraph uses this to keep `general:typescript` from firing on a
        Python-only repo, etc. Explicit `enable=[name]` still wins —
        forcing a plugin is a user override of the auto-detect machinery.

    Returns `(cues_by_key, active_plugin_names)`. The caller's wrapper
    constructs whatever typed config object it wants from `cues_by_key`.

    Parameters:
      cue_merger:  Called with `(existing, new)` when two plugins
                   contribute under the same key. Must return the union
                   (or whatever combining semantics the subsystem wants).
      cue_copier:  Called once per key to defensively copy the first
                   plugin's contribution so later merges don't mutate
                   the static cue values inside plugin modules.
    """
    enable_set = set(enable or [])
    disable_set = set(disable or [])
    plugins = _discover_plugins(plugins_pkg, local_plugin_paths=local_plugin_paths)
    cues_by_key: dict[str, Any] = {}
    active_names: list[str] = []

    for p in plugins:
        is_general = p.name.startswith("general:")
        if p.name in disable_set and p.name not in enable_set:
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
        if (
            allowed_cue_keys is not None
            and p.name not in enable_set
            and not (set(p.cues.keys()) & allowed_cue_keys)
        ):
            continue
        active_names.append(p.name)
        for key, cues in p.cues.items():
            if allowed_cue_keys is not None and key not in allowed_cue_keys and p.name not in enable_set:
                # Drop the contribution but keep the plugin in active_names
                # only if some other cue key passes — handled by the outer
                # `if not (set(...) & ...)` guard above.
                continue
            if key in cues_by_key:
                cues_by_key[key] = cue_merger(cues_by_key[key], cues)
            else:
                cues_by_key[key] = cue_copier(cues)

    active_names.sort()
    return cues_by_key, active_names
