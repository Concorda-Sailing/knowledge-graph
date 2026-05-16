# Consolidated `kg` CLI — Phase 3: extract logigraph subcommands

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development.

**Goal:** Apply Phase 2's pattern to `logigraph/bin/logigraph` (2154 LOC, 24 subcommands). Extract into `logigraph/lib/cli/*.py` modules, slim `bin/logigraph` to a shim, switch `kg.cli.logigraph` from subprocess to native dispatch.

**Architecture:** Identical to Phase 2 with one wrinkle — logigraph claims against a depgraph corpus, so its `Context` carries both `LOGIGRAPH` paths and a resolved `depgraph_dir`. Helpers needing depgraph corpus data take that as part of `ctx`. The cross-graph `lib.rollup` import (currently `_lib_pkg.__path__.append(depgraph/lib)`) moves out of module scope into a lazy import inside the rollup-using handlers (or stays at module scope of the helper that needs it).

**Tech Stack:** Python 3.11+, argparse, frozen dataclass for `Context`, pytest fixtures.

---

## File structure

**New under `logigraph/lib/cli/`:**

```
__init__.py          build_parser() + register-each-module
context.py           Context dataclass (LOGIGRAPH + depgraph_dir + …)
_shared.py           shared helpers (repo_relative, find_rules_for_target,
                     _logigraph_commit_if_changed, etc.)

# 1 module per subcommand for the lifecycle + inspect commands:
regen.py / validate.py / health.py / self_check.py / stats.py
context_cmd.py       (context subcommand — _cmd suffix avoids dataclass clash)
rules_for.py / fan_out.py / gaps.py / rollup_cmd.py / dossiers.py

# Grouped lifecycle modules:
rule.py              rule-rank / draft / finalize / bump / stub
process.py           process-rank / draft / finalize / bump / stub
domain.py            domain-bump (one-cmd module for symmetry)
flag.py              flag / unflag
```

15 modules. Subcommand-to-module mapping mirrors Phase 2's structure.

**Modified:**
- `logigraph/bin/logigraph` — slimmed from 2154 LOC to ~30 LOC over the extraction tasks.
- `kg/cli/logigraph.py` — switched from `os.execvpe` shim to native dispatch via `logigraph.lib.cli`.

**New tests under `tests/logigraph/`:**
- `conftest.py` with `data_dir` fixture (logigraph-shaped layout)
- `test_context.py`
- Per-module test files added with each extraction

---

## Task list (10 tasks)

Aggressive bundling vs Phase 2's 16-task split — established pattern + lessons from Phase 2 mean each subagent needs less per-task scaffolding.

### Task 1: Foundation — `Context`, `_shared`, dispatcher skeleton

Create `logigraph/lib/cli/{context,_shared,__init__}.py` + `tests/logigraph/{conftest,test_context}.py`.

`Context` carries: `LOGIGRAPH` (root data dir), `NODES`, `DOSSIERS_DIR`, `RULE_DIR`, `PROCESS_DIR`, `DOMAIN_DIR` (each computed from data_dir), `CALIBRATION_DIR`, `TELEMETRY_DIR`, `depgraph_dir` (resolved via the existing `_depgraph_dir()` lookup logic — env var, project.toml `[depgraph] data_dir`, or raise), `framework_python`, `tool_root`.

`_shared.py` ports: `repo_relative`, `find_rules_for_target`, `_logigraph_commit_if_changed`, and any other helpers used by ≥2 subcommands. Each takes `ctx: Context`.

After this task: foundation in place, no extractions. Tests verify `Context.from_data_dir` derives paths correctly.

### Task 2: Lifecycle bundle — regen, validate, health, self-check, stats

5 modules, one per command. Mechanical port pattern from Phase 2 (REPLACE inline handler with 3-line wrapper, no duplicates, tests at `tests/logigraph/test_cli_<mod>.py`).

`cmd_stats` may share `_load_telemetry_events` with depgraph's version — duplicate it in `_shared.py` or import from `depgraph.lib.cli._shared` (cross-graph import). Decide at implementation time.

### Task 3: Context (subcommand) → `context_cmd.py`

The `context` subcommand prints applicable rules for a target. Uses `find_rules_for_target` from `_shared`.

### Task 4: Inspect bundle — rules-for, fan-out, gaps, rollup, dossiers

5 modules. `rollup_cmd.py` (not `rollup.py` to avoid clash with the existing `lib/rollup.py` rollup helper module).

### Task 5: rule.py — rule-rank / rule-draft / rule-finalize / rule-bump / rule-stub

One module, 5 handlers, single `register(sub)` adding all 5 subparsers.

### Task 6: process.py — process-rank / draft / finalize / bump / stub

Same shape as rule.py.

### Task 7: domain.py — domain-bump

One-handler module for symmetry with rule/process.

### Task 8: flag.py — flag / unflag

Mirrors Phase 2's depgraph/lib/cli/flag.py.

### Task 9: Slim `bin/logigraph` to entry-point shim

After Tasks 2-8, all handlers live in `lib/cli/*.py`. `bin/logigraph` shrinks to ~30 LOC: resolve `LOGIGRAPH_DATA_DIR`, build `Context`, dispatch via `lib.cli.build_parser()`.

Verify `bin/logigraph --help` lists all 24 subcommands in legacy order. Run full pytest suite and live `logigraph health` against concorda.

### Task 10: kg.cli.logigraph native registration

Replace the `os.execvpe` shim in `kg/cli/logigraph.py` with native import of `logigraph.lib.cli.build_parser` + in-process dispatch. Mirrors Phase 2 Task 16.

Add a parity test: `kg logigraph rules-for --help` reaches the subcommand argparse. Byte-for-byte diff `kg logigraph health` vs legacy `logigraph health` against concorda.

---

## Cross-graph linking — explicit handling

The legacy script extends `lib.__path__` at module scope to import depgraph's `lib.rollup`. Phase 3 moves this out of module scope:

- `rollup_cmd.py` does the path extension lazily inside the handler (or at import time of *that* module only, not the package).
- `_shared.py` does NOT depend on depgraph's lib.

Keep the existing `_DEPGRAPH_VENV / FRAMEWORK_PYTHON` discovery logic — package it into `Context.framework_python`.

---

## Phase 3 risks

- **Cross-graph rollup import.** Easy to break by losing the `sys.path` mutation. Mitigation: explicit test in `test_cli_rollup_cmd.py` that exercises the rollup pipeline.
- **`_depgraph_dir()` priority.** Legacy: env > project.toml `[depgraph].data_dir` > error. `Context.from_data_dir` should keep this exact priority since hook contexts often set the env var.
- **Phase 2's lessons:** REPLACE not ADD (grep must return 1), tests under `tests/logigraph/` (not `logigraph/tests/`), test with system `python3`. These warnings must appear in every extraction subagent prompt.
- **Test count.** Going in: 148 passing. Expected end: ~200 (148 + ~50 from per-module logigraph tests).
