"""Plugin registry — discover, activate, and union cues across plugins.

Public entry point: `build_config(repo_path, *, enable=None, disable=None,
auto=True, local_plugin_paths=None) -> ClassificationConfig`. Builds the
per-repo cue config by:

1. Walking `depgraph.plugins.<name>` subpackages, importing each, collecting
   every top-level `Plugin` instance.
2. Walking any project-local plugin paths the caller passed (used to load
   private/internal-only detectors a project doesn't want to upstream).
   Local plugins override shipped plugins with the same `.name`.
3. Filtering to the active set: detector fires AND not in `disable`, OR
   forced on via `enable`.
4. Unioning each active plugin's `LanguageCues` per language.

The `general/*` plugins always activate; they carry the language-baseline
cues that aren't framework-specific. Private plugins under
`<data-dir>/plugins/` get the same first-class treatment as shipped ones
without ever being published.
"""
from __future__ import annotations

import importlib
import importlib.util
import pkgutil
from pathlib import Path

from depgraph.lib.classification.config import (
    ClassificationConfig,
    LanguageCues,
)
from depgraph.plugins.base import Plugin


def _discover_shipped_plugins() -> list[Plugin]:
    """Walk depgraph.plugins.* and load every shipped plugin."""
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
            # Some subpackages (general/) ship multiple plugin modules
            # via __init__.py re-exports.
            sub = importlib.import_module(module_info.name)
        for attr in dir(sub):
            obj = getattr(sub, attr)
            if isinstance(obj, Plugin):
                plugins.append(obj)
    return plugins


def _load_local_plugins(paths: list[Path]) -> list[Plugin]:
    """Load Plugin instances from arbitrary directories outside the package.

    Each path can be a single `plugin.py` file or a directory whose
    immediate `.py` children each contribute zero or more `Plugin`
    instances. Bad paths and import errors are reported on stderr but
    don't abort the build — a typo in a private plugin shouldn't break
    `kg depgraph regen`.

    Use this to ship detectors for internal/proprietary frameworks that
    can't be upstreamed. The project's `[classification.plugins]
    local_paths` setting in project.toml is the typical caller.
    """
    import sys

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
            module_name = f"depgraph._local_plugins.{py.stem}_{abs(hash(str(py)))}"
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


def _discover_plugins(local_plugin_paths: list[Path] | None = None) -> list[Plugin]:
    """Shipped plugins plus any local ones; locals override shipped on
    name collision (so a project can ship a custom `react` plugin that
    replaces the framework's React cues without forking the codebase)."""
    shipped = _discover_shipped_plugins()
    if not local_plugin_paths:
        return shipped
    local = _load_local_plugins(local_plugin_paths)
    local_names = {p.name for p in local}
    merged = [p for p in shipped if p.name not in local_names]
    merged.extend(local)
    return merged


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
    local_plugin_paths: list[Path] | None = None,
) -> tuple[ClassificationConfig, list[str]]:
    """Build the active ClassificationConfig for a single repo.

    Returns (config, active_plugin_names) so the caller can log which
    plugins fired. Pass `local_plugin_paths` to load private detectors
    from directories outside the framework — see `_load_local_plugins`.
    """
    enable_set = set(enable or [])
    disable_set = set(disable or [])
    plugins = _discover_plugins(local_plugin_paths=local_plugin_paths)
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
    local_plugin_paths: list[Path] | None = None,
) -> tuple[ClassificationConfig, dict[str, list[str]]]:
    """Multi-repo variant — unions cues across every repo's active set.

    Returns (config, {repo_key: active_plugin_names}) so the caller can log
    per-repo plugin activation. Local plugin paths apply across all repos
    in the project; they're loaded once and reused per-repo so the
    project's private detectors fire wherever they detect a match.
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
                merged[lang] = _merge_cues(merged[lang], cues)
            else:
                merged[lang] = cues
    return ClassificationConfig(languages=merged), by_repo
