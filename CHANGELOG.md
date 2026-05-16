# Changelog

Notable user-visible changes to the knowledge-graph framework.

## 2026-05-16 — Post-Phase-5 cleanup

- **lib namespace rename.** Phases 2-3 left both `depgraph/lib/` and `logigraph/lib/` reachable as the unqualified `lib` package, forcing a runtime `sys.modules` eviction in `kg/cli/logigraph.py` and a `_PatchedModule` hack in `tests/conftest.py`. Both `depgraph/` and `logigraph/` now have `__init__.py` markers and all imports are fully-qualified (`from depgraph.lib.X` / `from logigraph.lib.X`). 78 files touched, 403 tests still pass. The eviction logic is gone; `tests/conftest.py` is back to 18 LOC.
- **`kg add` strictness unification.** Legacy `kg add` now uses the same permissive `[project].name`-only requirement as `kg project add`. Backward-compatible with the existing strict-schema tests (their fixtures include the extra fields anyway).
- **`docs/CLI.md` refresh.** depgraph/logigraph/install sections reflect the Phase-2/3/4 native dispatch and the install.sh-as-alias state.
- **New tests.** End-to-end `kg install bootstrap` integration test; programmatic byte-for-byte parity regression between `bin/depgraph` and `kg depgraph` (same for logigraph). 8 parity cases all green.

## 2026-05-16 — Phase 5: shared infrastructure

- New `kg/shared/` package hosts cross-graph helpers (`git_commit_if_changed`, `default_actor`, `load_telemetry_events`). depgraph and logigraph re-export these via their `lib/cli/_shared.py` to preserve backward-compat names.
- Net result: fewer divergent copies of the same logic to maintain.

## 2026-05-16 — Phase 4: install.sh → Python port

- `install.sh` collapsed from 978 LOC of bash to a 10-line wrapper that execs `kg install`.
- All 7 install subcommands ported to focused Python modules under `kg/cli/install/`: `init`, `tools`, `hooks`, `systemd`, `path`, `cascade`, `bootstrap`.
- `kg install systemd` carries forward all the Phase-1 install.sh fixes: sibling-with-hyphen data-dir layout auto-detect, `--depgraph-data-dir` / `--logigraph-data-dir` overrides, preflight refusal on missing data dirs, graphui venv bootstrap if absent.
- `kg project init` no longer shells out — it imports the Python init handler directly.
- Output of `install.sh <sub>` and `kg install <sub>` is byte-for-byte identical (both routes hit the same Python).

## 2026-05-16 — Phase 3: logigraph extraction

- `logigraph/bin/logigraph` slimmed from 2154 LOC to 28 LOC.
- 24 subcommands extracted into 13 modules under `logigraph/lib/cli/` (rule lifecycle grouped into `rule.py`, process into `process.py`, etc.).
- `kg logigraph <subcommand>` dispatches in-process via the new modules; `kg logigraph rule-rank --help` reaches the real subcommand argparse surface (previously a top-level help only).
- `Context` dataclass replaces the import-time `LOGIGRAPH = resolve_data_dir(...)` global. Includes the resolved linked `depgraph_dir` (logigraph claims bind to depgraph nodes).
- Cross-graph `lib.rollup` import (depgraph's rollup helpers used by `logigraph rollup`) is now lazy inside the rollup handler instead of a module-scope `sys.path` mutation.
- `bin/logigraph <subcommand>` and `kg logigraph <subcommand>` produce byte-for-byte identical output.

## 2026-05-15 — Phase 2: depgraph extraction

- `depgraph/bin/depgraph` slimmed from 1601 LOC to 28 LOC.
- 18 subcommands extracted into 13 modules under `depgraph/lib/cli/` (dossier lifecycle grouped, flag/unflag grouped, repo-add/list/remove grouped, rest individual).
- `kg depgraph <subcommand>` dispatches in-process (no more subprocess shim).
- `Context` dataclass replaces the import-time `DEPGRAPH = resolve_data_dir(...)` global.

## 2026-05-15 — Phase 1: consolidated `kg` CLI entry point

- Single `kg ...` entry point with five top-level groups: `project`, `depgraph`, `logigraph`, `install`, `hook`.
- `kg project use <name>` sets a persistent default project in `~/.claude/kg-graphs.toml`; bare `kg depgraph regen` then resolves it from any cwd. Override per-command with `--project <name>` or `--data-dir <path>`.
- 7-step project resolution order: flag > `$KG_PROJECT` > `$DEPGRAPH_DATA_DIR`/`$LOGIGRAPH_DATA_DIR` > cwd-ancestor walk > `default` in `kg-graphs.toml` > single registered project > error.
- New: `kg project add-repo / list-repos / remove-repo / set / health`. `depgraph repo-add / repo-list / repo-remove` shipped alongside.
- Legacy `kg list / add / remove`, `depgraph X`, `logigraph X`, `install.sh X` all keep working unchanged. No migration required.
- `~/.claude/kg-graphs.toml` gains an optional top-level `default = "..."` key.
- New: `docs/CLI.md` reference; memory entry `reference_kg_cli.md` for cross-session agent context.

## Earlier fixes (uncategorized — also 2026-05-15)

- **graphui systemd unit**: corrected `DEPGRAPH_DATA_DIR` / `LOGIGRAPH_DATA_DIR` to point at the actual sibling-with-hyphen layout (`~/concorda-knowledge-graph/...`). Service had been rendering "No repos" because it was reading from a path that doesn't exist.
- **`depgraph repo-add` / `repo-list`**: new CLI for managing per-project `[repos.<key>]` tables — previously users had to hand-edit TOML and trip on the format.
- **`install.sh init` scaffold**: emits the correct `[repos.<key>]` sub-table form instead of the flat `[repos]` form (which the loaders reject).
- **`install.sh systemd`**: added `--depgraph-data-dir` / `--logigraph-data-dir` overrides + sibling-with-hyphen auto-detect + preflight refusal on missing data dirs + graphui venv bootstrap. These all carried into the Phase-4 Python port.

## Known deferred work

- **`depgraph validate --strict`** flag is wired but unused by the handler. Pre-existing from before this work; preserved verbatim through Phase 2.
- **`logigraph context` quirk on `rule::nonexistent`** — emits the missing-rule WARN to stderr instead of the "no rules apply" stdout message. Pre-existing from before this work; preserved through Phase 3.
