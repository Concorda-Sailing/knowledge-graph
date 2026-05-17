"""depgraph regen — run extractors per [repos.*] then reconcile.

Two invocation modes:

Mode A — multi-repo via project.toml (production path):
    kg depgraph regen --data-dir <out> [--project-toml <path>]
    Loads project.toml, iterates [repos.*], runs per-language extractors,
    runs SQL pipeline if any repo has sql in languages, runs cross-ref +
    db_access + classification, writes to <out>/nodes/, builds indexes.
    Falls back to the v1 subprocess-based pipeline if no per-repo language
    spec is found (backward compat for configs that still use 'extractor =').

Mode B — single-repo direct invocation (CI / ad-hoc):
    kg depgraph regen --data-dir <out> --repo-key <key> --repo-path <path>
                      [--languages typescript,python,sql]
                      [--migrations-dir <path>]
    Synthesizes a one-repo config from CLI args and runs the v2 pipeline.
    If --languages is omitted, infers from file extensions present in repo-path.

Both modes produce byte-identical output for the same source state. Mode B is
Mode A with a single synthesized repo config — the pipeline code is shared.

Python venv: the regen pipeline runs in the current interpreter. When invoked
via `kg depgraph regen`, that interpreter is whichever python kg's bin/ shim
used — typically depgraph/venv/bin/python (which has sqlglot installed). The
pipeline imports depgraph.extractors.python.extract directly; no subprocess.
TypeScript extraction still uses subprocess (npx tsx) since there's no Python
binding for the TS extractor.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1]
if str(_LIB.parent) not in sys.path:
    sys.path.insert(0, str(_LIB.parent))

from depgraph.lib.config import project_repos, render_extractor, repo_detectors  # noqa: E402
from depgraph.lib.classification.engine import classify_corpus  # noqa: E402
from depgraph.lib.classification.writer import write_classified  # noqa: E402
from depgraph.extractors.reconcile import validate_corpus  # noqa: E402

from ._shared import mark_regen_in_progress
from .context import Context


# ---------------------------------------------------------------------------
# Language inference
# ---------------------------------------------------------------------------

def _infer_languages(repo_path: Path) -> list[str]:
    """Infer language set from file extensions present under repo_path."""
    langs: set[str] = set()
    for f in repo_path.rglob("*"):
        if not f.is_file():
            continue
        s = f.suffix.lower()
        if s == ".py":
            langs.add("python")
        elif s in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
            langs.add("typescript")
        elif s == ".sql":
            langs.add("sql")
    return sorted(langs)


# ---------------------------------------------------------------------------
# Per-language extraction
# ---------------------------------------------------------------------------

def _extract_python(
    repo_key: str,
    repo_path: Path,
    *,
    include_paths: list[str] | None = None,
    exclude_paths: list[str] | None = None,
) -> list[dict]:
    from depgraph.extractors.python.extract import extract_repo
    return list(extract_repo(
        repo_key=repo_key,
        repo_path=repo_path,
        include_paths=include_paths or (),
        exclude_paths=exclude_paths or (),
    ))


_DEFAULT_TS_HEAP_MB = 4096


def _ts_node_env(base_env: dict[str, str] | None = None) -> dict[str, str]:
    """Build the env for the tsx subprocess, ensuring Node has a heap large
    enough for ts-morph to load hundreds of files. ts-morph's default 2GB
    heap OOMs on real-world web apps; we raise the floor but defer to any
    --max-old-space-size the caller has already set in NODE_OPTIONS.
    """
    env = dict(base_env if base_env is not None else os.environ)
    existing = env.get("NODE_OPTIONS", "")
    if "--max-old-space-size" not in existing:
        addition = f"--max-old-space-size={_DEFAULT_TS_HEAP_MB}"
        env["NODE_OPTIONS"] = f"{existing} {addition}".strip() if existing else addition
    return env


def _extract_typescript(repo_key: str, repo_path: Path, *, tool_root: Path) -> list[dict]:
    """Invoke the TS extractor as a subprocess, parse ndjson output."""
    ts_extractor = tool_root / "extractors" / "typescript" / "extract.ts"
    if not ts_extractor.exists():
        print(f"WARN: TS extractor not found at {ts_extractor}; skipping", file=sys.stderr)
        return []
    cmd = [
        "npx", "tsx", str(ts_extractor),
        "--repo-key", repo_key,
        "--repo-path", str(repo_path),
        "--format", "ndjson",
    ]
    result = subprocess.run(cmd, env=_ts_node_env(), capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"WARN: TS extractor exited {result.returncode}: {result.stderr[:400]}",
              file=sys.stderr)
        return []
    prims: list[dict] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            prims.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"WARN: TS extractor bad JSON line: {e}", file=sys.stderr)
    return prims


# ---------------------------------------------------------------------------
# SQL pipeline helpers
# ---------------------------------------------------------------------------

def _run_sql_pipeline(
    all_primitives: list[dict],
    *,
    repo_key: str,
    repo_path: Path,
    migrations_dirs: list[Path],
) -> list[dict]:
    """Run the SQL migration pipeline for one repo and return schema primitives."""
    try:
        from depgraph.lib.sql.migration import extract_migration, is_migration_file
        from depgraph.lib.sql.reconcile import reconcile_schema, schema_to_primitives
        from depgraph.lib.sql.attach import attach_migration_attributes
    except ImportError as e:
        print(f"WARN: SQL pipeline unavailable ({e}); skipping", file=sys.stderr)
        return []

    migration_files = []
    for mdir in migrations_dirs:
        if not mdir.is_dir():
            continue
        for f in sorted(mdir.rglob("*")):
            if f.is_file() and is_migration_file(f):
                try:
                    migration_files.append(extract_migration(f))
                except Exception as exc:
                    print(f"WARN: failed to extract migration {f}: {exc}", file=sys.stderr)

    if not migration_files:
        return []

    schema = reconcile_schema(migration_files, repo_key=repo_key)
    schema_prims = schema_to_primitives(schema)
    attach_migration_attributes(primitives=all_primitives + schema_prims,
                               migrations=migration_files)
    return schema_prims


# ---------------------------------------------------------------------------
# Cross-pass helpers
# ---------------------------------------------------------------------------

def _run_cross_passes(all_primitives: list[dict], repo_paths: dict[str, Path]) -> None:
    """Run cross-reference and db_access passes over the unified primitive list."""
    try:
        from depgraph.lib.sql.cross_ref import attach_model_schema_references
        attach_model_schema_references(all_primitives)
    except ImportError:
        pass

    for repo_key, repo_path in repo_paths.items():
        try:
            from depgraph.lib.system_stub.db_access import attach_db_access_edges
            attach_db_access_edges(all_primitives, repo_path=repo_path)
        except ImportError:
            pass
        except Exception as exc:
            print(f"WARN: db_access pass failed for {repo_key}: {exc}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Index building
# ---------------------------------------------------------------------------

def _build_by_target(primitives: list[dict]) -> dict[str, list[dict]]:
    """Build target_id → [incoming edge records] from edges_out across all primitives."""
    by_target: dict[str, list[dict]] = {}
    for p in primitives:
        for e in p.get("edges_out", []) or []:
            tgt = e.get("target")
            if not tgt:
                continue
            by_target.setdefault(tgt, []).append({
                "source": p["id"],
                "kind": e.get("kind"),
                "via": e.get("via"),
                "where": e.get("where"),
                "confidence": e.get("confidence", "exact"),
            })
    for k in by_target:
        by_target[k].sort(key=lambda e: (
            e.get("source", ""), e.get("kind", ""), e.get("via") or "", e.get("where") or ""
        ))
    return by_target


def _build_by_source(primitives: list[dict]) -> dict[str, list[dict]]:
    """Build source_id → [outgoing edge records] from edges_out."""
    by_source: dict[str, list[dict]] = {}
    for p in primitives:
        edges = p.get("edges_out", []) or []
        if edges:
            by_source[p["id"]] = list(edges)
    return by_source


def _write_index(index_dir: Path, name: str, payload: dict) -> None:
    """Atomically write a JSON index file under index_dir."""
    index_dir.mkdir(parents=True, exist_ok=True)
    target = index_dir / name
    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    tmp.replace(target)


# ---------------------------------------------------------------------------
# Core v2 pipeline
# ---------------------------------------------------------------------------

def _run_v2_pipeline(
    *,
    data_dir: Path,
    repos: list[dict],  # each: {key, path, languages, migrations_dirs}
    tool_root: Path,
) -> int:
    """
    Run the full v2 extraction + classification + reconcile pipeline.

    repos is a list of per-repo config dicts:
        key:            str  — repo identifier
        path:           Path — checkout root
        languages:      list[str] — ["python", "typescript", "sql"]
        migrations_dirs: list[Path] — dirs to scan for migration files
        include_paths:  list[str] — fnmatch globs (Python only, today)
        exclude_paths:  list[str] — fnmatch globs (Python only, today)
    """
    all_primitives: list[dict] = []
    repo_paths: dict[str, Path] = {}

    # --- Extraction pass (per repo × language) ---
    for repo_cfg in repos:
        key = repo_cfg["key"]
        path = Path(repo_cfg["path"])
        languages = repo_cfg.get("languages") or _infer_languages(path)
        repo_paths[key] = path

        print(f"--- extract {key} (languages: {', '.join(languages) or 'none detected'})")

        if "python" in languages:
            prims = _extract_python(
                key, path,
                include_paths=repo_cfg.get("include_paths"),
                exclude_paths=repo_cfg.get("exclude_paths"),
            )
            print(f"    python: {len(prims)} primitives")
            all_primitives.extend(prims)

        if "typescript" in languages:
            prims = _extract_typescript(key, path, tool_root=tool_root)
            print(f"    typescript: {len(prims)} primitives")
            all_primitives.extend(prims)

        if "sql" in languages:
            migrations_dirs = [Path(d) for d in repo_cfg.get("migrations_dirs", [])]
            schema_prims = _run_sql_pipeline(
                all_primitives,
                repo_key=key,
                repo_path=path,
                migrations_dirs=migrations_dirs,
            )
            print(f"    sql: {len(schema_prims)} schema primitives")
            all_primitives.extend(schema_prims)

    print(f"--- total primitives extracted: {len(all_primitives)}")

    # --- Cross passes (cross-ref + db_access) ---
    print("--- cross passes")
    _run_cross_passes(all_primitives, repo_paths)

    # --- Classification ---
    print("--- classify")
    decisions = classify_corpus(all_primitives)

    # --- Write to disk ---
    print("--- write")
    write_classified(all_primitives, decisions, data_dir=data_dir)

    # --- v2 validation report ---
    report = validate_corpus(all_primitives)
    n_orphans = len(report["orphan_edges"])
    n_prim_errors = len(report["primitive_errors"])
    n_collisions = len(report["slug_collisions"])
    if n_prim_errors:
        print(f"WARN: {n_prim_errors} primitive validation errors", file=sys.stderr)
    if n_collisions:
        print(f"WARN: {n_collisions} slug collisions", file=sys.stderr)
    if n_orphans:
        print(f"WARN: {n_orphans} orphan edges (targets not in corpus or external::)",
              file=sys.stderr)

    # --- Build and write indexes ---
    print("--- indexes")
    index_dir = data_dir / "nodes" / "_index"
    by_target = _build_by_target(all_primitives)
    by_source = _build_by_source(all_primitives)
    _write_index(index_dir, "by_target.json", by_target)
    _write_index(index_dir, "by_source.json", by_source)
    edge_count = sum(len(v) for v in by_target.values())
    print(f"    by_target: {len(by_target)} targets, {edge_count} edges")
    print(f"    by_source: {len(by_source)} sources")

    # --- Write _meta.json ---
    meta = {
        "schema_version": 2,
        "regen_status": "complete",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "primitive_count": len(all_primitives),
        "edge_count": edge_count,
        "orphan_edge_count": n_orphans,
        "slug_collision_count": n_collisions,
        "primitive_error_count": n_prim_errors,
        "validation_report": report,
    }
    meta_path = data_dir / "nodes" / "_meta.json"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    print(f"--- done: {len(all_primitives)} primitives, {edge_count} edges")
    return 0


# ---------------------------------------------------------------------------
# Mode A — multi-repo via project.toml (with v1 fallback)
# ---------------------------------------------------------------------------

def _mode_a(args: argparse.Namespace, ctx: Context) -> int:
    """Run regen for all repos defined in project.toml.

    If project.toml repos use the v1 'extractor =' syntax, falls back to the
    v1 subprocess-based pipeline so existing configs keep working.  The v2
    native pipeline is used when a repo has a 'languages' list instead of a
    bare 'extractor' command.
    """
    repos_cfg = project_repos(ctx.DEPGRAPH)
    if not repos_cfg:
        print("No [repos.*] tables found in project.toml — nothing to regen.", file=sys.stderr)
        return 1

    # Detect whether any repo is configured with the new 'languages' key.
    # If none are, fall back to v1 subprocess mode for full backward compat.
    has_v2_config = any(
        "languages" in info for info in repos_cfg.values()
        if isinstance(info, dict)
    )

    if not has_v2_config:
        return _mode_a_v1_fallback(args, ctx, repos_cfg)

    repos = []
    for key, info in repos_cfg.items():
        repos.append({
            "key": key,
            "path": info["path"],
            "languages": info.get("languages") or _infer_languages(info["path"]),
            "migrations_dirs": [
                info["path"] / d for d in (info.get("migrations_dirs") or [])
            ],
            "include_paths": info.get("include_paths") or [],
            "exclude_paths": info.get("exclude_paths") or [],
        })

    tool_root = ctx.tool_root
    return _run_v2_pipeline(data_dir=ctx.DEPGRAPH, repos=repos, tool_root=tool_root)


def _mode_a_v1_fallback(
    args: argparse.Namespace,
    ctx: Context,
    repos_cfg: dict,
) -> int:
    """v1 subprocess-based regen — kept for backward compat with extractor= configs."""
    env = {**os.environ, "DEPGRAPH_DATA_DIR": str(ctx.DEPGRAPH)}
    failed: list[str] = []
    for key, info in repos_cfg.items():
        cmd = render_extractor(info, ctx.DEPGRAPH)
        if cmd is None:
            print(f"--- {key} (no extractor configured; skipping)")
            continue
        cmd += [
            "--repo-key", key,
            "--repo-path", str(info["path"]),
            "--data-dir", str(ctx.DEPGRAPH),
        ]
        detectors = repo_detectors(info)
        if detectors:
            cmd += ["--detectors", ",".join(detectors)]
        cmd += ["--detector-path", str(ctx.DEPGRAPH / "extractors" / "detectors")]
        print(f"--- {key}")
        rc = subprocess.call(cmd, env=env)
        if rc != 0:
            failed.append(key)
    print("--- reconcile")
    rc = subprocess.call(
        [ctx.framework_python, str(ctx.tool_root / "extractors" / "reconcile.py")],
        env=env,
    )
    if rc != 0:
        failed.append("reconcile")
    if failed:
        print(f"\nFAILED stages: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [s.strip() for s in value.split(",") if s.strip()]


# ---------------------------------------------------------------------------
# Mode B — single-repo direct invocation
# ---------------------------------------------------------------------------

def _mode_b(args: argparse.Namespace, ctx: Context) -> int:
    """Run regen for a single repo specified entirely via CLI flags."""
    repo_path = Path(args.repo_path).expanduser().resolve()
    if not repo_path.is_dir():
        print(f"Error: --repo-path {repo_path} is not a directory", file=sys.stderr)
        return 1

    if args.languages:
        languages = [l.strip() for l in args.languages.split(",") if l.strip()]
    else:
        languages = _infer_languages(repo_path)

    migrations_dirs: list[Path] = []
    if getattr(args, "migrations_dir", None):
        migrations_dirs = [Path(args.migrations_dir).expanduser().resolve()]

    include_paths = _split_csv(getattr(args, "include_paths", None))
    exclude_paths = _split_csv(getattr(args, "exclude_paths", None))

    # data_dir comes from ctx (resolved by kg.cli.depgraph from --data-dir)
    data_dir = ctx.DEPGRAPH

    repos = [{
        "key": args.repo_key,
        "path": repo_path,
        "languages": languages,
        "migrations_dirs": migrations_dirs,
        "include_paths": include_paths,
        "exclude_paths": exclude_paths,
    }]

    tool_root = ctx.tool_root
    return _run_v2_pipeline(data_dir=data_dir, repos=repos, tool_root=tool_root)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def cmd_regen(args: argparse.Namespace, ctx: Context) -> int:
    """Dispatch to Mode A or Mode B based on whether --repo-key is present."""
    mark_regen_in_progress(ctx)
    if getattr(args, "repo_key", None):
        return _mode_b(args, ctx)
    return _mode_a(args, ctx)


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "regen",
        help="Run extractors and rebuild the node corpus + indexes.",
    )
    # Mode A flags
    p.add_argument("--all", action="store_true",
                   help="(v1 compat) Ignored in v2 mode.")
    p.add_argument("--since",
                   help="(v1 compat) Ignored in v2 mode.")
    # Mode B flags
    p.add_argument("--repo-key",
                   help="[Mode B] Repo identifier (e.g. 'api').")
    p.add_argument("--repo-path",
                   help="[Mode B] Path to repo checkout.")
    p.add_argument("--languages",
                   help="[Mode B] Comma-separated language list: python,typescript,sql. "
                        "Inferred from file extensions if omitted.")
    p.add_argument("--migrations-dir",
                   help="[Mode B] Path to migrations directory (SQL pipeline).")
    p.add_argument("--include-paths", dest="include_paths",
                   help="[Mode B] Comma-separated fnmatch globs against "
                        "rel-path; if set, only matching files are extracted "
                        "(Python only).")
    p.add_argument("--exclude-paths", dest="exclude_paths",
                   help="[Mode B] Comma-separated fnmatch globs against "
                        "rel-path; matching files are skipped (Python only).")
    p.set_defaults(func=cmd_regen)
