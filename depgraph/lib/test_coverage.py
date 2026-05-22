"""Lightweight test-coverage index — Option C of issue #52.

Tests are excluded from the production corpus by design (so test files
don't inflate every function's reverse-dependent count). The side
effect is that the graph can't answer "is this function tested?" —
which is exactly the leverage signal we want for test prioritization.

This module closes that gap WITHOUT polluting the production graph.
After extraction emits production primitives, this pass:

  1. Walks test files (paths matching `test_paths` patterns) that the
     production extractor skipped.
  2. For each test file, parses its imports + bare name references and
     resolves each to a production primitive id using the same dotted-
     module / per-file-symbol indexes the production import resolver
     builds.
  3. Aggregates per production primitive: which test files import or
     reference it.
  4. Writes `<data_dir>/test_coverage.json` (production_id →
     [test_file_paths]) and stamps `tested_by_count: N` on each
     production primitive so dossiers and graphui can read coverage
     without re-loading the JSON index. (`data_dir` here is the
     depgraph data dir, which `kg.cli.resolve` already places under
     `<project>/depgraph/`.)

The inverse direction ("what does THIS test cover") is out of scope for
Option C by design — it would require keeping test files as primitives,
which is what Option B / A would do. Option C is the cheapest answer to
the more important question ("is this tested at all?").
"""
from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

from depgraph.lib.path_filters import included, matches_any


# Default test-file globs used when a repo doesn't declare `test_paths`
# in project.toml. Mirrors common conventions across Python (pytest,
# unittest) and JS/TS (Jest, Vitest). Kept generous on purpose — false
# positives (a non-test file under `tests/`) only cost a parse and
# never pollute the production graph.
DEFAULT_TEST_PATTERNS: tuple[str, ...] = (
    "**/test_*.py",
    "**/*_test.py",
    "**/tests/**",
    "**/__tests__/**",
)


SCHEMA_VERSION = "1"


# Directories the production extractor hardcodes to skip; mirror them
# here so we don't try to walk virtualenvs or pycache trees as tests.
_HARDCODED_SKIP_DIRS = {"__pycache__", ".venv", "venv", "node_modules"}


# Builtin / framework names that show up as bare ast.Name references
# inside every test file. Resolving these against the per-file local
# symbol map would produce false coverage edges (every test that calls
# `len(...)` would "cover" any production helper also named `len`).
# Filtering at this layer keeps the resolver dumb.
_BUILTIN_REFERENCE_NAMES: frozenset[str] = frozenset({
    "len", "print", "range", "list", "dict", "set", "tuple", "str",
    "bytes", "int", "float", "bool", "True", "False", "None",
    "isinstance", "issubclass", "type", "object", "Exception",
    "ValueError", "TypeError", "KeyError", "IndexError", "AttributeError",
    "RuntimeError", "NotImplementedError", "StopIteration", "OSError",
    "FileNotFoundError", "PermissionError",
    "open", "iter", "next", "enumerate", "zip", "map", "filter",
    "sorted", "reversed", "sum", "min", "max", "any", "all", "abs",
    "round", "repr", "hash", "id", "vars", "dir", "getattr", "setattr",
    "hasattr", "delattr", "callable", "classmethod", "staticmethod",
    "property", "super", "self", "cls",
    # pytest framework primitives — already filtered upstream when
    # `_attach_tests_edges` runs, mirrored here so the walker doesn't
    # try to resolve them against the production symbol map.
    "pytest", "fixture", "mark", "parametrize", "raises", "fail",
    "skip", "skipif", "xfail", "approx",
})


# ----------------------------------------------------------------------
# Walker
# ----------------------------------------------------------------------


# Common source-layout prefixes the test-coverage walker strips when
# trying to resolve a test-file import against the production module
# index. A repo with `src/click/__init__.py` exposes the package as
# just `click` to importers (because the build system installs `src/`
# as a roots dir); test files therefore say `import click`, not
# `import src.click`. The production extractor stores the path-derived
# dotted name (`src.click`), so without this aliasing the test would
# resolve to `external::` and cover nothing.
#
# Tried in order. The first prefix whose stripped form points at a
# different module than the unstripped form wins; "first prefix" is
# stable because we iterate this tuple explicitly. None-of-the-above
# falls back to the literal dotted lookup.
_SOURCE_ROOT_ALIASES: tuple[str, ...] = ("src.", "lib.")


@dataclass
class _ProductionIndex:
    """Indexes over the production primitives used to resolve test-file
    references back to production node ids.

    Built once per regen and consulted by the per-file walker; lives
    here rather than as anonymous dicts so the dataclass attribute
    names document what each index keys on."""
    # dotted-module-name → primitive id of the module
    module_by_dotted: dict[str, str]
    # rel-path (forward-slash, .py) → {top-level symbol name → primitive id}
    symbols_by_path: dict[str, dict[str, str]]
    # primitive id of the module → rel-path
    path_by_module_id: dict[str, str]
    # primitive id of a module → {imported-as-name → target id}
    # Captures the production extractor's resolved `imports` edges
    # (including post-`_resolve_package_reexports` rewrites pointing
    # at defining symbols), which lets the walker resolve barrel
    # `click.option` → the actual `option` definition without having
    # to re-walk the package's __init__ source.
    bindings_by_module_id: dict[str, dict[str, str]]
    # set of every production primitive id (membership test)
    all_ids: set[str]

    def lookup_module(self, dotted: str) -> str | None:
        """Resolve a dotted-module name to a primitive id, with
        source-root aliasing.

        First tries the literal name; on miss, tries each
        `_SOURCE_ROOT_ALIASES` prefix prepended. The prepended form is
        what the production extractor sees for `src/`-layout repos
        (`src/click/__init__.py` → dotted `src.click`), while the test
        files import the installed name (`click`). Without this
        aliasing every `src/`-layout repo would report zero test
        coverage.
        """
        direct = self.module_by_dotted.get(dotted)
        if direct is not None:
            return direct
        for prefix in _SOURCE_ROOT_ALIASES:
            aliased = self.module_by_dotted.get(prefix + dotted)
            if aliased is not None:
                return aliased
        return None

    def lookup_symbol_in_module(self, module_id: str, name: str) -> str | None:
        """Find a top-level symbol `name` reachable through `module_id`.

        Checks two sources, in order:
          1. The module's own per-file symbol map (functions/classes/
             variables defined directly in the file).
          2. The module's resolved `imports` edges — captures barrel
             re-exports like `click/__init__.py`'s
             `from .core import Argument as Argument`, which the
             production extractor's `_resolve_package_reexports` has
             already rewritten to point at the defining symbol.

        Returns None when the name isn't a top-level symbol of the
        module AND isn't a re-export the package exposes.
        """
        path = self.path_by_module_id.get(module_id)
        if path is not None:
            direct = self.symbols_by_path.get(path, {}).get(name)
            if direct is not None:
                return direct
        bindings = self.bindings_by_module_id.get(module_id) or {}
        return bindings.get(name)


def _build_production_index(primitives: list[dict]) -> _ProductionIndex:
    """Build the {dotted-module, per-path-symbols, re-export-bindings,
    id-set} indexes from the production primitive list.

    Symmetric with the indexes `_attach_imports_edges` builds locally,
    just exposed as a reusable shape. The `bindings_by_module_id` map
    captures the resolved `imports` edges so the walker can answer
    `click.option` correctly even when `option` lives in
    `decorators.py` rather than `__init__.py` — the production
    extractor's `_resolve_package_reexports` pass has already rewritten
    the package edge to point at the defining symbol. See issue #52
    design notes."""
    module_by_dotted: dict[str, str] = {}
    symbols_by_path: dict[str, dict[str, str]] = {}
    path_by_module_id: dict[str, str] = {}
    bindings_by_module_id: dict[str, dict[str, str]] = {}
    all_ids: set[str] = set()
    for p in primitives:
        pid = p.get("id")
        if pid:
            all_ids.add(pid)
        if p.get("primitive") == "module":
            path = p["source"]["path"]
            path_by_module_id[pid] = path
            dotted = path
            if dotted.endswith(".py"):
                dotted = dotted[:-3]
            dotted = dotted.replace("/", ".")
            if dotted.endswith(".__init__"):
                dotted = dotted[: -len(".__init__")]
            module_by_dotted[dotted] = pid
            for e in p.get("edges_out", []) or []:
                if e.get("kind") != "imports":
                    continue
                lb = e.get("local_binding")
                tgt = e.get("target")
                if not lb or not tgt:
                    continue
                # Skip placeholders for unresolved external symbols —
                # they'd let a `click.something_we_dont_define` claim
                # coverage on a synthetic `external::pypi::...` id.
                if tgt.startswith("external::"):
                    continue
                bindings_by_module_id.setdefault(pid, {})[lb] = tgt
        if p.get("owner") is None and p.get("primitive") in {"class", "function", "variable"}:
            symbols_by_path.setdefault(p["source"]["path"], {})[p["name"]] = pid
    return _ProductionIndex(
        module_by_dotted=module_by_dotted,
        symbols_by_path=symbols_by_path,
        path_by_module_id=path_by_module_id,
        bindings_by_module_id=bindings_by_module_id,
        all_ids=all_ids,
    )


def _iter_test_files(
    repo_path: Path,
    *,
    test_patterns: Sequence[str],
    exclude_paths: Sequence[str] = (),
) -> Iterable[tuple[str, Path]]:
    """Yield (rel-path, absolute path) for every .py file under repo_path
    that matches any `test_patterns` glob.

    Mirrors `_iter_py_files` in extract.py for skip-dirs handling, but
    inverts the include-rule: we WANT the files the production extractor
    excludes. `exclude_paths` here only filters out paths the user wants
    out of BOTH the production graph and the test-coverage index (e.g.
    vendored test trees that shouldn't count as covering anything).
    """
    for p in repo_path.rglob("*.py"):
        if any(part in _HARDCODED_SKIP_DIRS for part in p.parts):
            continue
        rel = str(p.relative_to(repo_path)).replace("\\", "/")
        if not matches_any(rel, test_patterns):
            continue
        if exclude_paths and matches_any(rel, exclude_paths):
            continue
        yield rel, p


def _resolve_relative_import(
    test_rel_path: str,
    *,
    level: int,
    module_name: str,
    index: _ProductionIndex,
) -> str | None:
    """Resolve a `from .X.Y import Z` to the target module's primitive id.

    Returns None if the relative anchor lands outside the corpus (e.g.
    the test file is at repo root and tries `from .. import X`).
    """
    parts = test_rel_path.split("/")
    base_parts = parts[:-level] if level <= len(parts) - 1 else []
    if module_name:
        base_parts = base_parts + module_name.split(".")
    if not base_parts:
        return None
    candidate_path = "/".join(base_parts) + ".py"
    candidate_init = "/".join(base_parts) + "/__init__.py"
    # Look up by path → module id via the index. We don't have a
    # path→id index, so reconstruct the dotted form and use that.
    for path in (candidate_path, candidate_init):
        dotted = path
        if dotted.endswith(".py"):
            dotted = dotted[:-3]
        dotted = dotted.replace("/", ".")
        if dotted.endswith(".__init__"):
            dotted = dotted[: -len(".__init__")]
        mid = index.lookup_module(dotted)
        if mid:
            return mid
    return None


def _collect_references(
    tree: ast.Module,
    test_rel_path: str,
    *,
    index: _ProductionIndex,
) -> set[str]:
    """Walk a test file's AST and return the set of production primitive
    ids it touches.

    Two passes:
      1. ast.Import / ast.ImportFrom → resolved to a module id or the
         specific top-level symbol id when the import names a symbol the
         production indexes know about. Builds a per-file `bindings` map
         {local_name → production_id} so the next pass can attribute
         bare name references.
      2. ast.Name / ast.Attribute references whose root binds to
         something the imports map. An `ast.Attribute` chain like
         `mod.SubClass` is resolved by walking from the root binding:
         if the root is a production module id and `SubClass` is a top-
         level symbol of that module, we add the symbol id (in addition
         to the module id from the import pass).

    The walker is deliberately conservative: when in doubt, fall back to
    the module-level id from the import pass. False negatives (missing
    a deeply-nested reference) cost coverage signal; false positives
    (claiming a test covers a symbol it never touches) corrupt the
    answer to "is this tested?". We prefer the former.
    """
    bindings: dict[str, str] = {}
    references: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            level = node.level or 0
            module_name = node.module or ""
            target_mod_id: str | None
            if level > 0:
                target_mod_id = _resolve_relative_import(
                    test_rel_path,
                    level=level,
                    module_name=module_name,
                    index=index,
                )
            else:
                target_mod_id = (
                    index.lookup_module(module_name) if module_name else None
                )
            if not target_mod_id:
                continue
            for alias in node.names:
                if alias.name == "*":
                    # Wildcard imports — claim the module-level dependency
                    # only. Naming individual symbols would require
                    # evaluating `__all__`, which would mean a level of
                    # static analysis we explicitly avoid in Option C.
                    references.add(target_mod_id)
                    continue
                local_binding = alias.asname or alias.name
                sym_id = index.lookup_symbol_in_module(
                    target_mod_id, alias.name
                )
                if sym_id:
                    bindings[local_binding] = sym_id
                    references.add(sym_id)
                else:
                    bindings[local_binding] = target_mod_id
                    references.add(target_mod_id)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                target_id = index.lookup_module(alias.name)
                if not target_id:
                    continue
                local_binding = alias.asname or alias.name.split(".")[0]
                bindings[local_binding] = target_id
                references.add(target_id)

    # Second pass: any ast.Attribute chain whose root binds to a
    # production module id and whose `.attr` matches a top-level symbol
    # in that module — record the symbol id too. Bare `ast.Name`
    # references are already covered by the import pass (the import
    # itself counts as the reference).
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue
        root = node
        while isinstance(root, ast.Attribute):
            root = root.value
        if not isinstance(root, ast.Name):
            continue
        root_name = root.id
        if root_name in _BUILTIN_REFERENCE_NAMES:
            continue
        root_id = bindings.get(root_name)
        if not root_id:
            continue
        # Only walk one level deep — `mod.Sym.method` resolves to
        # `mod.Sym` if `Sym` is a top-level symbol of mod, not to the
        # method (we don't track methods as top-level symbols).
        # `lookup_symbol_in_module` returns None when root_id isn't a
        # module (i.e. the root binding already resolved to a symbol);
        # that's the right behavior — `Symbol.attr` doesn't tell us
        # anything new about coverage targets.
        sym_id = index.lookup_symbol_in_module(root_id, node.attr)
        if sym_id:
            references.add(sym_id)

    return references


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


def build_test_coverage_index(
    primitives: list[dict],
    *,
    repos: list[dict],
) -> dict:
    """Build the test-coverage index payload.

    `repos` is the per-repo config list `_run_v2_pipeline` already
    threads (key, path, languages, exclude_paths, test_paths). Returns
    the JSON-serializable payload; callers persist it under
    `<data_dir>/depgraph/test_coverage.json` and stamp the per-node
    `tested_by_count` field separately.

    The walker is Python-only today. TypeScript / JavaScript test files
    are silently skipped — TS production primitives won't get a
    `tested_by_count` until an equivalent walker lands for that
    extractor. The schema doesn't change when TS support arrives; only
    the set of populated entries grows.
    """
    index = _build_production_index(primitives)
    coverage: dict[str, set[str]] = {}
    test_files_scanned = 0

    for repo_cfg in repos:
        languages = repo_cfg.get("languages") or []
        if "python" not in languages:
            # Only Python test walking is implemented; see module
            # docstring. TS-test support would call a sibling helper
            # here without changing the on-disk shape.
            continue
        repo_path = Path(repo_cfg["path"])
        if not repo_path.is_dir():
            continue
        # `test_paths = []` in project.toml is meaningful — it means
        # "scan no files for coverage". Only `None` (the default when
        # the key is absent) should fall back to the default globs.
        configured = repo_cfg.get("test_paths")
        test_patterns = (
            list(DEFAULT_TEST_PATTERNS) if configured is None else list(configured)
        )
        if not test_patterns:
            continue
        # If the production extractor ran with include_paths, the test
        # walker must NOT honor it — by definition the user wants the
        # production graph narrowed, and the tests they want indexed
        # may live outside. We do honor a separate exclude_paths style
        # filter at the test_paths layer via the standard matches_any
        # rule embedded above.
        for rel_path, abs_path in _iter_test_files(
            repo_path, test_patterns=test_patterns,
        ):
            try:
                tree = ast.parse(abs_path.read_text())
            except (OSError, SyntaxError):
                # A syntactically-broken test file is still a "test
                # file we tried to scan" — count it, but emit no edges.
                test_files_scanned += 1
                continue
            test_files_scanned += 1
            refs = _collect_references(tree, rel_path, index=index)
            for pid in refs:
                # Repo-scope the test rel-path so test files from
                # different repos with the same rel-path stay
                # distinguishable in the index.
                rel_with_repo = f"{repo_cfg['key']}::{rel_path}"
                coverage.setdefault(pid, set()).add(rel_with_repo)

    production_to_tests = {
        pid: sorted(files) for pid, files in coverage.items()
    }
    tested_nodes = len(production_to_tests)
    total_production_nodes = len(index.all_ids)
    ratio = (tested_nodes / total_production_nodes) if total_production_nodes else 0.0

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "production_to_tests": production_to_tests,
        "stats": {
            "test_files_scanned": test_files_scanned,
            "tested_nodes": tested_nodes,
            "total_production_nodes": total_production_nodes,
            "tested_node_ratio": round(ratio, 4),
        },
    }


def stamp_tested_by_count(primitives: list[dict], payload: dict) -> int:
    """Stamp `tested_by_count: int` on every production primitive that
    appears as a key in the coverage payload.

    Mutates in place and returns the count of primitives stamped.
    Primitives without coverage do NOT get a `tested_by_count: 0`
    stamp — the absence of the field is itself the signal, which keeps
    on-disk node JSON unchanged for the (current) common case of
    "nothing tested" and stays compatible with corpora generated
    before this pass landed.
    """
    counts = {
        pid: len(files)
        for pid, files in (payload.get("production_to_tests") or {}).items()
    }
    stamped = 0
    for p in primitives:
        pid = p.get("id")
        if pid is None:
            continue
        n = counts.get(pid)
        if n is None:
            continue
        p["tested_by_count"] = n
        stamped += 1
    return stamped


def write_test_coverage(data_dir: Path, payload: dict) -> Path:
    """Atomically write the coverage payload to
    `<data_dir>/test_coverage.json`.

    `data_dir` here is the depgraph data dir (which is already the
    `<project>/depgraph/` directory — see `kg.cli.resolve`). Returns the
    final path. Uses the same indent=2/sort_keys idiom as every other
    index writer so the file is bit-stable across regens for an
    unchanged corpus.
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    target = data_dir / "test_coverage.json"
    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    tmp.replace(target)
    return target
