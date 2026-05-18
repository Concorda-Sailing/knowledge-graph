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

from depgraph.lib.config import (  # noqa: E402
    primary_repo_path,
    project_classification_options,
    project_repos,
    render_extractor,
    repo_detectors,
)
from depgraph.lib.path_filters import included  # noqa: E402
from depgraph.lib.classification.engine import classify_corpus  # noqa: E402
from depgraph.lib.classification.writer import (  # noqa: E402
    dossier_rel_path_for,
    write_classified,
)
from depgraph.extractors.reconcile import (  # noqa: E402
    _normalize_url_pattern,
    validate_corpus,
)

from ._shared import mark_regen_in_progress
from .context import Context
from .orphans import archive_node_file


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


# Node's own default is ~4 GB, which OOMs on real-world Next.js codebases —
# 276 source files of a moderate web app exhaust the heap loading ts-morph's
# project graph + tsconfig path-alias resolution (#28). 8 GB clears the
# common case without going overboard; users with monorepos can override by
# setting NODE_OPTIONS=--max-old-space-size=... in the environment.
_DEFAULT_TS_HEAP_MB = 8192


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


def _extract_typescript(
    repo_key: str,
    repo_path: Path,
    *,
    tool_root: Path,
    include_paths: list[str] | None = None,
    exclude_paths: list[str] | None = None,
) -> tuple[list[dict], str | None]:
    """Invoke the TS extractor as a subprocess, parse ndjson output.

    Returns (primitives, error_msg). error_msg is None on success; on
    failure it carries the extractor's stderr (truncated) so the regen
    loop can surface a single summary at end-of-run instead of burying
    the warning in the output (#28).
    """
    ts_extractor = tool_root / "extractors" / "typescript" / "extract.ts"
    if not ts_extractor.exists():
        msg = f"TS extractor not found at {ts_extractor}"
        print(f"ERROR: {msg}; skipping", file=sys.stderr)
        return [], msg
    cmd = [
        "npx", "tsx", str(ts_extractor),
        "--repo-key", repo_key,
        "--repo-path", str(repo_path),
        "--format", "ndjson",
    ]
    if include_paths:
        cmd += ["--include-paths", ",".join(include_paths)]
    if exclude_paths:
        cmd += ["--exclude-paths", ",".join(exclude_paths)]
    result = subprocess.run(cmd, env=_ts_node_env(), capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        # Full stderr — when ts-morph OOMs the diagnostic line is past
        # the first 400 chars and the older truncation hid it.
        print(
            f"ERROR: TS extractor exited {result.returncode} for repo {repo_key!r}:\n"
            f"{result.stderr}",
            file=sys.stderr,
        )
        return [], (
            f"exit={result.returncode}; "
            f"first stderr line: {result.stderr.splitlines()[0] if result.stderr.strip() else '(empty)'}"
        )
    prims: list[dict] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            prims.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"WARN: TS extractor bad JSON line: {e}", file=sys.stderr)
    return prims, None


# ---------------------------------------------------------------------------
# SQL pipeline helpers
# ---------------------------------------------------------------------------

def _run_sql_pipeline(
    all_primitives: list[dict],
    *,
    repo_key: str,
    repo_path: Path,
    migrations_dirs: list[Path],
    include_paths: list[str] | None = None,
    exclude_paths: list[str] | None = None,
) -> list[dict]:
    """Run the SQL migration pipeline for one repo and return schema primitives."""
    try:
        from depgraph.lib.sql.migration import extract_migration, is_migration_file
        from depgraph.lib.sql.reconcile import reconcile_schema, schema_to_primitives
        from depgraph.lib.sql.attach import attach_migration_attributes
    except ImportError as e:
        print(f"WARN: SQL pipeline unavailable ({e}); skipping", file=sys.stderr)
        return []

    include = include_paths or ()
    exclude = exclude_paths or ()

    migration_files = []
    for mdir in migrations_dirs:
        if not mdir.is_dir():
            continue
        for f in sorted(mdir.rglob("*")):
            if not (f.is_file() and is_migration_file(f)):
                continue
            try:
                rel = str(f.resolve().relative_to(repo_path.resolve()))
            except ValueError:
                rel = str(f)
            if not included(rel, include_paths=include, exclude_paths=exclude):
                continue
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


# Primitive types we never auto-stub — modules, packages, and variables
# generate a lot of "this file/constant has no narrative" noise on big
# corpora. Symbols worth a stub (function / class / endpoint / hook /
# component / service / model / schema / test / util) fall through.
_STUB_SKIP_PRIMITIVES: frozenset[str] = frozenset({"module", "package", "variable"})


_STUB_TEMPLATE = """---
node_id: {id}
node_kind: {kind}
feature: null
last_reviewed: {date}
last_reviewed_against_hash: {hash}
status: unreviewed
---

# {title}

## Purpose

_TODO: describe what this {kind} is for and why it exists, in plain English.
The stub was auto-generated by `depgraph regen` — replace this and bump
`status: current` once the dossier reflects reality._

## Invariants

_TODO: bulleted list of things that must remain true._

## Gotchas

_TODO: what has bitten us, surprising ordering, hard-learned lessons._

## Cross-cutting concerns

_TODO: auth, rate limits, websocket events, audit, side effects on other features._

## External consumers

_None known. (See node JSON `external_consumers` for the structured form.)_

## Open questions

_None recorded yet._
"""


def _stub_missing_dossiers(
    *, primitives: list[dict], decisions: dict, data_dir: Path
) -> int:
    """For each non-skipped primitive, ensure a dossier file exists at its
    canonical path and the primitive carries a `dossier` field that points
    at that path.

    Idempotent: existing dossier files are not touched. Sets `dossier` on
    every stubbable primitive so a subsequent `write_classified` persists
    the field into the on-disk node JSON. Returns the count of newly
    written stubs.
    """
    import datetime as _dt

    today = _dt.date.today().isoformat()
    created = 0
    for p in primitives:
        if p.get("primitive") in _STUB_SKIP_PRIMITIVES:
            continue
        decision = decisions.get(p["id"])
        decision_kind = decision.kind if decision is not None else None
        rel = dossier_rel_path_for(p, decision_kind)
        p["dossier"] = rel
        full = data_dir / rel
        if full.exists():
            continue
        full.parent.mkdir(parents=True, exist_ok=True)
        title = p.get("title") or p.get("name") or p["id"].split("::")[-1]
        kind = decision_kind or p.get("kind") or p.get("primitive") or "?"
        full.write_text(_STUB_TEMPLATE.format(
            id=p["id"],
            kind=kind,
            date=today,
            hash=p.get("structural_hash", "unknown"),
            title=title,
        ))
        created += 1
    return created


def _iter_live_node_files(nodes_dir: Path):
    """Yield every node JSON under nodes/, skipping `_archive/`, `_index/`,
    `_meta.json`, `_manifests/`, etc."""
    for path in nodes_dir.rglob("*.json"):
        if path.name.startswith("_"):
            continue
        if any(p.startswith("_") for p in path.relative_to(nodes_dir).parts):
            continue
        yield path


def _effective_kind(p: dict, decisions: dict) -> str | None:
    """Resolve a primitive's effective kind for cross-cutting passes: the
    classifier's verdict wins, otherwise the kind the extractor set
    directly, otherwise None. Mirrors `write_classified`'s precedence."""
    decision = decisions.get(p.get("id"))
    if decision is not None and getattr(decision, "kind", None) is not None:
        return decision.kind
    return p.get("kind")


def _join_route_calls_v2(primitives: list[dict], decisions: dict) -> int:
    """For every route_call primitive (`kind: "route_call"`), find endpoint
    primitives whose `(method, normalized_path)` matches the call site's
    `(method, normalized_url_pattern)` and add a `calls` edge to the call
    site's `edges_out`. Reverse-index build picks the edges up naturally.

    Uses `decisions` (from `classify_corpus`) because endpoint kind is
    assigned by the classifier and isn't yet on the primitive itself when
    this pass runs.

    Returns the count of edges added so the regen log can surface the
    cross-repo connectivity that was previously inert.
    """
    endpoints_by_key: dict[tuple[str, str], list[dict]] = {}
    route_calls: list[dict] = []
    for p in primitives:
        kind = _effective_kind(p, decisions)
        sig = p.get("signature") or {}
        if kind == "endpoint":
            method = (sig.get("method") or "").upper()
            path = _normalize_url_pattern(sig.get("path"))
            if not method or not path:
                continue
            endpoints_by_key.setdefault((method, path), []).append(p)
        elif kind == "route_call":
            route_calls.append(p)

    added = 0
    for rc in route_calls:
        sig = rc.get("signature") or {}
        method = (sig.get("method") or "").upper()
        url = _normalize_url_pattern(sig.get("url_pattern"))
        if not method or not url:
            continue
        targets = endpoints_by_key.get((method, url), [])
        if not targets:
            continue
        rc_source = rc.get("source") or {}
        edges = rc.setdefault("edges_out", [])
        existing_targets = {e.get("target") for e in edges if e.get("via") == "route_call"}
        for ep in targets:
            if ep["id"] in existing_targets:
                continue
            edges.append({
                "kind": "calls",
                "target": ep["id"],
                "via": "route_call",
                "where": rc_source.get("path"),
                "confidence": "fuzzy",
            })
            added += 1
    return added


def _manifest_key(repo: str, language: str) -> str:
    """Filename-safe manifest key for a (repo, language) pair."""
    safe_repo = repo.replace("/", "_")
    return f"{safe_repo}__{language}"


def _write_extraction_manifests(
    data_dir: Path, manifests: dict[tuple[str, str], set[str]]
) -> None:
    """Persist one JSON file per successful extractor run under
    `nodes/_manifests/<repo>__<language>.json`. Files written here are read
    back by `_archive_domain_orphans` to tell "extractor ran and didn't
    emit X" from "extractor didn't run this round."

    Removes any prior manifest for the same (repo, language) before
    rewriting so a subsequent regen that emits fewer ids doesn't see
    leftover ids and skip archival.
    """
    manifest_dir = data_dir / "nodes" / "_manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    for (repo, lang), ids in manifests.items():
        path = manifest_dir / f"{_manifest_key(repo, lang)}.json"
        payload = {
            "schema_version": 1,
            "repo": repo,
            "language": lang,
            "node_ids": sorted(ids),
        }
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        tmp.replace(path)


def _load_extraction_manifests(
    data_dir: Path, only_keys: set[tuple[str, str]]
) -> dict[tuple[str, str], set[str]]:
    """Read manifests for the (repo, language) pairs in `only_keys`. Limiting
    the read to the pairs THIS regen produced is what gives the partial-regen
    safety guarantee: stale manifests on disk from a prior different config
    don't drive archival on this round."""
    out: dict[tuple[str, str], set[str]] = {}
    manifest_dir = data_dir / "nodes" / "_manifests"
    if not manifest_dir.exists():
        return out
    for (repo, lang) in only_keys:
        path = manifest_dir / f"{_manifest_key(repo, lang)}.json"
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        ids = data.get("node_ids") or []
        out[(repo, lang)] = set(ids)
    return out


def _archive_domain_orphans(
    data_dir: Path, manifests: dict[tuple[str, str], set[str]]
) -> tuple[int, set[str]]:
    """Walk on-disk nodes and archive any whose (repo, language) had an
    extractor run THIS regen but whose id isn't in that run's manifest —
    i.e. the symbol was removed from a source file that still exists.

    Nodes whose (repo, language) isn't in `manifests` are preserved. This
    is what makes partial regens safe: missing manifest ⇒ "extractor didn't
    run this round, don't claim its nodes are stale."

    Returns (count, ids) — symmetric with `_archive_file_orphans`.
    """
    nodes_dir = data_dir / "nodes"
    if not nodes_dir.exists():
        return 0, set()
    archive_dir = nodes_dir / "_archive"
    archived_ids: set[str] = set()
    count = 0
    for node_file in _iter_live_node_files(nodes_dir):
        try:
            data = json.loads(node_file.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        src = data.get("source") or {}
        repo, language = src.get("repo"), src.get("language")
        nid = data.get("id")
        if not repo or not language or not nid:
            continue
        manifest = manifests.get((repo, language))
        if manifest is None:
            continue
        if nid in manifest:
            continue
        archive_node_file(
            node_file, archive_dir, reason="domain_orphan_symbol_removed"
        )
        _archive_dossier_alongside(data, data_dir)
        archived_ids.add(nid)
        count += 1
    return count, archived_ids


def _archive_dossier_alongside(data: dict, data_dir: Path) -> None:
    """If an archived node has a dossier file, move it to `dossiers/_archive/`
    alongside the node. Same collision-safe rename rules as `archive_node_file`.
    No-op if the dossier field isn't set or the file doesn't exist.
    """
    rel = data.get("dossier")
    if not rel:
        return
    full = data_dir / rel
    if not full.exists():
        return
    archive_dir = data_dir / "dossiers" / "_archive"
    archive_node_file(full, archive_dir, reason="source_path_missing")


def _archive_file_orphans(
    data_dir: Path, repo_paths: dict[str, Path]
) -> tuple[int, set[str]]:
    """Walk on-disk nodes and archive any whose `source.path` no longer
    exists on disk (file deleted from the tracked repo since last regen).

    `repo_paths` is the authoritative basename → checkout-path map for THIS
    regen run (built from project.toml in Mode A, from CLI args in Mode B).
    Nodes whose repo basename isn't in `repo_paths` are preserved — they
    may belong to a repo this run didn't touch (partial regen). This keeps
    archival from accidentally clearing a quiescent repo's nodes.

    Returns (count_archived, set_of_archived_ids). The id set lets callers
    drop matching entries from in-memory primitive lists so indexes only
    reflect the live set.
    """
    nodes_dir = data_dir / "nodes"
    if not nodes_dir.exists():
        return 0, set()
    archive_dir = nodes_dir / "_archive"
    archived_ids: set[str] = set()
    count = 0
    for node_file in _iter_live_node_files(nodes_dir):
        try:
            data = json.loads(node_file.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        src = data.get("source") or {}
        repo, rel = src.get("repo"), src.get("path")
        if not repo or not rel:
            continue
        repo_path = repo_paths.get(repo)
        if repo_path is None:
            continue
        if (repo_path / rel).exists():
            continue
        archive_node_file(node_file, archive_dir, reason="source_path_missing")
        _archive_dossier_alongside(data, data_dir)
        nid = data.get("id")
        if nid:
            archived_ids.add(nid)
        count += 1
    return count, archived_ids


# ---------------------------------------------------------------------------
# Core v2 pipeline
# ---------------------------------------------------------------------------

def _run_v2_pipeline(
    *,
    data_dir: Path,
    repos: list[dict],  # each: {key, path, languages, migrations_dirs}
    tool_root: Path,
    classification_options: dict | None = None,
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
    extractor_errors: list[tuple[str, str, str]] = []  # (repo_key, language, msg)
    # (repo_key, language) → set of node ids emitted by a *successful* run
    # of that extractor. Written to nodes/_manifests/<repo>__<lang>.json so
    # the domain-orphan pass can tell "this extractor ran and chose not to
    # emit X" from "this extractor didn't run this round" (partial regen).
    extraction_manifests: dict[tuple[str, str], set[str]] = {}

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
            # Python extractor either returns prims or raises — no soft-fail
            # path — so emission == success.
            extraction_manifests[(key, "python")] = {
                p["id"] for p in prims if p.get("id")
            }

        if "typescript" in languages:
            prims, ts_err = _extract_typescript(
                key, path, tool_root=tool_root,
                include_paths=repo_cfg.get("include_paths"),
                exclude_paths=repo_cfg.get("exclude_paths"),
            )
            marker = "  [EXTRACTOR FAILED]" if ts_err else ""
            print(f"    typescript: {len(prims)} primitives{marker}")
            if ts_err:
                extractor_errors.append((key, "typescript", ts_err))
            all_primitives.extend(prims)
            # Do NOT write a manifest on a TS failure — a partial extraction
            # would otherwise look complete and the domain-orphan pass would
            # archive everything the failed run didn't emit.
            if not ts_err:
                extraction_manifests[(key, "typescript")] = {
                    p["id"] for p in prims if p.get("id")
                }

        if "sql" in languages:
            migrations_dirs = [Path(d) for d in repo_cfg.get("migrations_dirs", [])]
            schema_prims = _run_sql_pipeline(
                all_primitives,
                repo_key=key,
                repo_path=path,
                migrations_dirs=migrations_dirs,
                include_paths=repo_cfg.get("include_paths"),
                exclude_paths=repo_cfg.get("exclude_paths"),
            )
            print(f"    sql: {len(schema_prims)} schema primitives")
            all_primitives.extend(schema_prims)
            extraction_manifests[(key, "sql")] = {
                p["id"] for p in schema_prims if p.get("id")
            }

    print(f"--- total primitives extracted: {len(all_primitives)}")

    # --- Cross passes (cross-ref + db_access) ---
    print("--- cross passes")
    _run_cross_passes(all_primitives, repo_paths)

    # --- Classification ---
    print("--- classify")
    from depgraph.plugins import build_config_for_repos
    classification_options = classification_options or {}
    # Build the per-repo languages map from the repos we just extracted from,
    # falling back to the inferred set when a repo didn't declare languages
    # explicitly. This is what filters out `general:typescript` from a
    # Python-only repo etc. (#15).
    languages_by_repo: dict[str, list[str]] = {}
    for repo_cfg in repos:
        key = repo_cfg["key"]
        langs = repo_cfg.get("languages") or _infer_languages(Path(repo_cfg["path"]))
        if langs:
            languages_by_repo[key] = list(langs)
    cfg, plugins_by_repo = build_config_for_repos(
        repo_paths,
        enable=classification_options.get("enable"),
        disable=classification_options.get("disable"),
        auto=classification_options.get("auto", True),
        local_plugin_paths=classification_options.get("local_plugin_paths"),
        languages_by_repo=languages_by_repo,
    )
    for repo_key, names in plugins_by_repo.items():
        print(f"    {repo_key} plugins: {', '.join(names) if names else '(none)'}")
    decisions = classify_corpus(all_primitives, config=cfg)

    # --- Cross-repo route_call → endpoint join ---
    # Endpoint kind is assigned by `classify_corpus` (FastAPI / Flask /
    # Express plugins), so the join has to run AFTER classification.
    # It mutates each route_call's `edges_out` in place, so the standard
    # write/index path picks up the new edges with no further plumbing.
    rc_edges = _join_route_calls_v2(all_primitives, decisions)
    print(f"--- route_call join: {rc_edges} edge(s)")

    # --- Stub missing dossiers ---
    # Run before write_classified so the dossier field is persisted into
    # each node JSON (dossier-finalize/bump/draft all read this field).
    # Idempotent: existing dossier files are left alone, so subsequent
    # regens only stub newly-introduced nodes.
    print("--- stub missing dossiers")
    stubbed = _stub_missing_dossiers(
        primitives=all_primitives, decisions=decisions, data_dir=data_dir,
    )
    print(f"    stubbed: {stubbed}")

    # --- Write to disk ---
    print("--- write")
    write_classified(all_primitives, decisions, data_dir=data_dir)

    # --- Archive file-orphan nodes ---
    # A node whose source file is gone from its repo is dead corpus state.
    # `write_classified` only writes the newly-extracted set, it doesn't
    # delete leftover nodes from prior regens. Walk on-disk now and sweep
    # them to `_archive/` so indexes and the `node_count` reflect the
    # live set rather than monotonically growing across regens.
    print("--- archive file-orphans")
    archived_count, archived_ids = _archive_file_orphans(data_dir, repo_paths)
    if archived_ids:
        all_primitives = [p for p in all_primitives if p.get("id") not in archived_ids]
    print(f"    archived: {archived_count}")

    # --- Write extraction manifests + archive domain-orphan nodes ---
    # File-orphan archival above only catches "source file deleted." But
    # symbols removed from a source file that still exists are equally
    # stale — and far more common in active development. Compare the
    # newly-emitted id set per (repo, language) against on-disk leftovers
    # and archive any that no longer appear.
    _write_extraction_manifests(data_dir, extraction_manifests)
    print("--- archive domain-orphans")
    loaded_manifests = _load_extraction_manifests(
        data_dir, set(extraction_manifests.keys())
    )
    domain_count, domain_ids = _archive_domain_orphans(data_dir, loaded_manifests)
    if domain_ids:
        all_primitives = [p for p in all_primitives if p.get("id") not in domain_ids]
    print(f"    archived: {domain_count}")

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
        # graphui templates read `node_count`; keep both keys so old and
        # new readers work without coordinating a rename.
        "node_count": len(all_primitives),
        "edge_count": edge_count,
        "orphan_edge_count": n_orphans,
        "slug_collision_count": n_collisions,
        "primitive_error_count": n_prim_errors,
        "git_commit": _primary_git_commit(data_dir),
        "validation_report": report,
        "extractor_errors": [
            {"repo": r, "language": lang, "error": msg}
            for (r, lang, msg) in extractor_errors
        ],
    }
    meta_path = data_dir / "nodes" / "_meta.json"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    print(f"--- done: {len(all_primitives)} primitives, {edge_count} edges")
    if extractor_errors:
        print(f"--- ERRORS: {len(extractor_errors)} extractor failure(s):",
              file=sys.stderr)
        for repo_key, lang, msg in extractor_errors:
            print(f"    {repo_key} ({lang}): {msg}", file=sys.stderr)
        if any(lang == "typescript" for _, lang, _ in extractor_errors):
            print(
                "    TS hint: if the message above contains "
                "'JavaScript heap out of memory', try\n"
                "      NODE_OPTIONS='--max-old-space-size=16384' "
                "kg depgraph regen\n"
                "    to give ts-morph more headroom (default is 8 GB).",
                file=sys.stderr,
            )
        return 1
    return 0


def _primary_git_commit(data_dir: Path) -> str | None:
    """HEAD short SHA of the [project] primary_repo's checkout, if it's a
    git working tree. Returns None when there's no primary_repo configured,
    the checkout isn't a git repo, or git isn't on PATH. The corpus is
    still valid without this — it just goes into _meta for provenance."""
    try:
        path = primary_repo_path(data_dir)
    except Exception:
        return None
    if path is None or not path.exists():
        return None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=path, capture_output=True, text=True, timeout=5,
        )
    except (FileNotFoundError, OSError):
        return None
    if result.returncode != 0:
        return None
    sha = result.stdout.strip()
    return sha or None


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
    classification_options = project_classification_options(ctx.DEPGRAPH)
    return _run_v2_pipeline(
        data_dir=ctx.DEPGRAPH, repos=repos, tool_root=tool_root,
        classification_options=classification_options,
    )


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
    classification_options = project_classification_options(ctx.DEPGRAPH)
    return _run_v2_pipeline(
        data_dir=data_dir, repos=repos, tool_root=tool_root,
        classification_options=classification_options,
    )


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
                   help="[Mode B] Comma-separated globs against rel-path; "
                        "if set, only matching files are extracted. Applied "
                        "by every language extractor (Python, TypeScript, SQL).")
    p.add_argument("--exclude-paths", dest="exclude_paths",
                   help="[Mode B] Comma-separated globs against rel-path; "
                        "matching files are skipped. Applied by every "
                        "language extractor (Python, TypeScript, SQL).")
    p.set_defaults(func=cmd_regen)
