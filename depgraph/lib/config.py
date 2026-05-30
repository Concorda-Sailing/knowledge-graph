"""Shared project-config parser for the depgraph framework.

All scripts in `bin/`, `hooks/`, and `extractors/` read project.toml
through this module so the schema is enforced in one place.

Schema (per-repo tables, mandatory):

    [project]
    name = "..."
    primary_repo = "<key>"   # optional; falls back to first [repos.*] key

    [repos.<key>]
    path = "~/<dir>"                                     # required
    extractor = ["python3", "{data_dir}/extractors/x.py"] # optional list
    files_arg = "--only"                                  # optional str

Substitutions available in `extractor` tokens:
    {data_dir}      — the framework data dir (e.g. ~/<project>/depgraph)
    {path}          — the repo's resolved path
    {framework_dir} — the depgraph framework root (parent of lib/)
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional


def resolve_data_dir(env_var: str) -> Path:
    """Resolve a graph data dir. Priority:
       1. `env_var` (e.g. DEPGRAPH_DATA_DIR) — explicit override.
       2. Walk up from cwd looking for `project.toml` next to `nodes/`.
       3. Raise SystemExit with a helpful message.

    Hooks always set the env var explicitly; CLI users either export it
    or cd into a project dir.
    """
    explicit = os.environ.get(env_var)
    if explicit:
        return Path(explicit).expanduser().resolve()
    cwd = Path.cwd().resolve()
    for d in [cwd, *cwd.parents]:
        if (d / "project.toml").exists() and (d / "nodes").is_dir():
            return d
    # Final fallback: the machine-local registry's default project — the same
    # resolution `kg` uses. Lets the bare `depgraph` / `logigraph` binaries
    # work from any cwd (matching the documented aliases) instead of erroring
    # when the env var is unset and cwd isn't inside a project dir.
    subsystem = env_var.split("_", 1)[0].lower()  # DEPGRAPH_DATA_DIR -> "depgraph"
    registry_dir = _registry_default_data_dir(subsystem)
    if registry_dir is not None:
        return registry_dir
    raise SystemExit(
        f"{env_var} is not set, no project root found in cwd or ancestors, and "
        f"no default project is registered. Either export "
        f"{env_var}=/path/to/project/data, cd into a directory containing "
        f"project.toml + nodes/, or set a default with `kg project use <name>`."
    )


def _load_tomllib():
    try:
        import tomllib  # py311+
        return tomllib
    except ImportError:
        try:
            import tomli  # type: ignore
            return tomli
        except ImportError:
            return None


def _registry_default_data_dir(subsystem: str) -> Optional[Path]:
    """Resolve ``<default-project-path>/<subsystem>`` from the machine-local
    kg registry (``~/.claude/kg-graphs.toml``), or None if unavailable.

    Reads the registry file directly rather than importing the kg orchestrator
    package — depgraph stays self-contained, and the registry location/shape is
    a stable, documented contract. Returns the subsystem data dir only when it
    actually carries a ``project.toml`` (a scaffolded project)."""
    tomllib = _load_tomllib()
    if tomllib is None:
        return None
    registry = Path.home() / ".claude" / "kg-graphs.toml"
    try:
        data = tomllib.loads(registry.read_text())
    except (OSError, ValueError):
        return None
    default = data.get("default")
    if not default:
        return None
    for graph in data.get("graph", []) or []:
        if graph.get("name") == default and graph.get("path"):
            d = Path(graph["path"]).expanduser() / subsystem
            if (d / "project.toml").exists():
                return d.resolve()
    return None


@lru_cache(maxsize=None)
def _load_project_config_cached(data_dir_str: str) -> dict:
    data_dir = Path(data_dir_str)
    candidates = [data_dir / "project.toml", data_dir.parent / "project.toml"]
    tomllib = _load_tomllib()
    if tomllib is None:
        return {}
    for cfg in candidates:
        if not cfg.exists():
            continue
        try:
            return tomllib.loads(cfg.read_text())
        except Exception:
            return {}
    return {}


def load_project_config(data_dir: Path) -> dict:
    """Read project.toml from `data_dir/project.toml` (or one level up).
    Returns {} if missing or unparseable.

    Result is memoized per `data_dir` for the process lifetime — project.toml
    doesn't change mid-process for our workloads (CLI invocations, hook fires,
    long-running graphui). Callers must treat the returned dict as immutable.
    """
    return _load_project_config_cached(str(data_dir))


def project_repos(data_dir: Path) -> dict[str, dict]:
    """Parse [repos.<key>] tables into a normalized dict.

    Returns: {repo_key: {"path": Path, "basename": str,
                         "extractor": list[str] | None,
                         "files_arg": str | None,
                         "detectors": list[str],
                         "languages": list[str] | None,
                         "migrations_dirs": list[str]}}

    The repo_key is the [repos.<key>] table name (e.g. "api").
    The basename is the final path segment (e.g. "<project>-api"), used
    for home-relative path matching when classifying file paths.

    v2 keys:
      languages       — ["python", "typescript", "sql"]; inferred from file
                        extensions if absent.
      migrations_dirs — list of subdirectory names (relative to repo path)
                        that contain migration files.
      include_paths   — list of fnmatch globs against rel-path; if set, only
                        files matching at least one pattern are extracted.
      exclude_paths   — list of fnmatch globs against rel-path; files
                        matching any pattern are skipped. Applied after
                        include_paths.
      test_paths      — list of fnmatch globs identifying TEST files for the
                        Option-C coverage walker (#52). These files are NOT
                        in the production graph (they remain excluded), but
                        the coverage pass scans them to map test-file →
                        production-node. Default when absent:
                        ["**/test_*.py", "**/*_test.py", "**/tests/**",
                         "**/__tests__/**"].

    Raises ValueError if [repos.*] is present but malformed.
    Returns {} if no [repos.*] tables are configured.
    """
    cfg = load_project_config(data_dir)
    repos_raw = cfg.get("repos") or {}
    out: dict[str, dict] = {}
    for key, val in repos_raw.items():
        if not isinstance(val, dict):
            raise ValueError(
                f"project.toml [repos.{key}] must be a table with `path`, "
                f"got a bare value. Per-repo tables are required."
            )
        path = val.get("path")
        if not path:
            raise ValueError(f"project.toml [repos.{key}] missing `path`")
        resolved = Path(path).expanduser().resolve()
        out[key] = {
            "path": resolved,
            "basename": resolved.name,
            "extractor": val.get("extractor"),
            "files_arg": val.get("files_arg"),
            "detectors": val.get("detectors", []),
            # v2 pipeline keys — passed through as-is from TOML
            "languages": val.get("languages"),
            "migrations_dirs": val.get("migrations_dirs", []),
            "include_paths": val.get("include_paths") or [],
            "exclude_paths": val.get("exclude_paths") or [],
            # `None` (not []) signals "user didn't configure test_paths";
            # the test-coverage walker substitutes its default glob set.
            # A user who wants the coverage pass to scan nothing should
            # set `test_paths = []` explicitly.
            "test_paths": val.get("test_paths"),
        }
    return out


def project_classification_options(data_dir: Path) -> dict:
    """Parse the optional [classification] section of project.toml.

    Returns the activation knobs the plugin registry honors:
        {
            "auto": bool,
            "enable": list[str],
            "disable": list[str],
            "local_plugin_paths": list[Path],
        }

    Defaults: auto=True, enable=[], disable=[]. `local_plugin_paths`
    always includes `<data-dir>/plugins/` if it exists (convention path
    for project-private detectors) plus anything listed under
    `[classification.plugins].local_paths`. Relative paths in
    project.toml resolve against the data dir.

        [classification.plugins]
        auto = false                      # turn off auto-detect
        enable = ["my-internal"]          # force-on (incl. local plugins)
        disable = ["jest"]                # veto
        local_paths = ["./private-plugins"]
    """
    cfg = load_project_config(data_dir)
    raw = cfg.get("classification") or {}
    plugins = raw.get("plugins") or {}

    local_paths: list[Path] = []
    conv = data_dir / "plugins"
    if conv.is_dir():
        local_paths.append(conv)
    for entry in plugins.get("local_paths") or []:
        p = Path(entry).expanduser()
        if not p.is_absolute():
            p = (data_dir / p).resolve()
        local_paths.append(p)

    return {
        "auto": bool(plugins.get("auto", True)),
        "enable": list(plugins.get("enable") or []),
        "disable": list(plugins.get("disable") or []),
        "local_plugin_paths": local_paths,
    }


def project_primary_repo(data_dir: Path) -> Optional[str]:
    """Return the repo_key whose git HEAD stamps the corpus-meta git_commit
    field. Falls back to the first [repos.*] key. Returns None if no repos
    are configured."""
    cfg = load_project_config(data_dir)
    proj = cfg.get("project") or {}
    primary = proj.get("primary_repo")
    repos = project_repos(data_dir)
    if primary and primary in repos:
        return primary
    if repos:
        return next(iter(repos))
    return None


def project_primary_repo_explicit(data_dir: Path) -> Optional[str]:
    """The value of `[project].primary_repo` from project.toml, or None if the
    user hasn't set it (regardless of whether a fallback is available).

    Callers that need to distinguish "user set this" from "first entry by
    iteration order" should use this; everything else should call
    project_primary_repo() and get the resolved value."""
    cfg = load_project_config(data_dir)
    proj = cfg.get("project") or {}
    primary = proj.get("primary_repo")
    if not primary:
        return None
    repos = project_repos(data_dir)
    return primary if primary in repos else None


def primary_repo_path(data_dir: Path) -> Optional[Path]:
    """Convenience: resolve the primary repo's path. Used by git-head stampers."""
    key = project_primary_repo(data_dir)
    if key is None:
        return None
    return project_repos(data_dir)[key]["path"]


def render_extractor(repo_info: dict, data_dir: Path) -> Optional[list[str]]:
    """Apply {data_dir}/{path}/{framework_dir}/{kg_dir} substitutions to the extractor token list.
    Returns None if the repo has no extractor configured.

    Available substitutions:
        {data_dir}      — the project data dir (e.g. ~/project/depgraph)
        {path}          — the repo's resolved filesystem path
        {framework_dir} — the depgraph framework root (parent of lib/)
        {kg_dir}        — the knowledge-graph repo root (parent of depgraph/)
    """
    extractor = repo_info.get("extractor")
    if not extractor:
        return None
    _lib_dir = Path(__file__).resolve().parent
    subs = {
        "data_dir": str(data_dir),
        "path": str(repo_info["path"]),
        "framework_dir": str(_lib_dir.parent),
        "kg_dir": str(_lib_dir.parent.parent),
    }
    return [token.format(**subs) for token in extractor]


def repo_detectors(repo_cfg: dict) -> list[str]:
    """Return the detectors list for a [repos.*] table; default empty.

    Raises ValueError if `detectors` is present but is not a list.
    """
    val = repo_cfg.get("detectors", [])
    if not isinstance(val, list):
        raise ValueError(f"detectors must be a list, got {type(val).__name__}")
    return list(val)


def repo_basenames(data_dir: Path) -> set[str]:
    """Convenience: the set of repo basenames, for path-matching like
    `seg == basename` in place of project-name string-prefix matching."""
    return {r["basename"] for r in project_repos(data_dir).values()}


def repo_for_basename(data_dir: Path, basename: str) -> Optional[dict]:
    """Look up a repo_info by its repo key (e.g. 'api') or basename
    (e.g. '<project>-api'). Key match wins; basename is the fallback.

    Callers in dossier.py / post_edit_regen.py pass `source.repo` from
    node JSON, which holds the [repos.<key>] key, not the path basename.
    The name is preserved for backward compat with existing imports."""
    repos = project_repos(data_dir)
    info = repos.get(basename)
    if info is not None:
        return info
    for info in repos.values():
        if info["basename"] == basename:
            return info
    return None


def path_to_repo_relative(abs_path: Path, data_dir: Path) -> Optional[tuple[str, str]]:
    """Given an absolute filesystem path, find which configured [repos.*]
    checkout it lives under and return (basename, rel_path_str).

    Returns None if the path isn't under any configured repo's `path`.
    Works for both flat checkouts (~/<basename>/) and nested ones
    (~/projects/<group>/<basename>/) because it consults the actual
    resolved `path` from project.toml rather than assuming layout.
    """
    try:
        ap = Path(abs_path).expanduser().resolve()
    except (OSError, RuntimeError):
        return None
    for info in project_repos(data_dir).values():
        try:
            rel = ap.relative_to(info["path"])
        except ValueError:
            continue
        return info["basename"], str(rel)
    return None


def path_to_repo_key_relative(abs_path: Path, data_dir: Path) -> Optional[tuple[str, str]]:
    """Given an absolute filesystem path, find which configured [repos.<key>]
    checkout it lives under and return (repo_key, rel_path_str).

    Same lookup as `path_to_repo_relative` but returns the repo KEY (the
    [repos.<key>] table name used as the prefix in canonical node ids
    like `<key>::<rel-path>::<symbol>`). v2 corpora are keyed by the
    repo key; v1 path-matching callers may still want basename via the
    sibling function.

    Returns None if the path isn't under any configured repo's `path`.
    """
    try:
        ap = Path(abs_path).expanduser().resolve()
    except (OSError, RuntimeError):
        return None
    for key, info in project_repos(data_dir).items():
        try:
            rel = ap.relative_to(info["path"])
        except ValueError:
            continue
        return key, str(rel)
    return None


def basename_path_map(data_dir: Path) -> dict[str, Path]:
    """{basename: resolved Path} for every [repos.*] table. Convenience for
    callers that have a `source.repo` basename and need the on-disk path
    without iterating every node."""
    return {info["basename"]: info["path"] for info in project_repos(data_dir).values()}
