# Consolidated `kg` CLI — Phase 5: shared infrastructure

> Subagent-driven execution. Steps use `- [ ]`.

**Goal:** Lift the duplicated helpers in `depgraph/lib/cli/_shared.py` and `logigraph/lib/cli/_shared.py` into a single cross-graph module under `kg/shared/`. Reduces drift and avoids the lib/cli/ namespace overlap pitfall that Phase 3's conftest hack works around.

**Scope discipline:** only lift helpers that are genuinely duplicated. Don't try to unify `find_nodes_for_target` (depgraph-specific) with `find_rules_for_target` (logigraph-specific); they share a name but not semantics.

---

## Identified duplications (audit done before plan)

1. **`git_commit_if_changed(repo_dir, paths, message, actor=None) -> bool`** — depgraph and logigraph both ship this with identical logic (git add, git commit with author/co-author, return True if anything committed). Different names (`_depgraph_commit_if_changed`, `git_commit_if_changed`) but same shape.

2. **`load_telemetry_events(path, since_hours=None) -> list[dict]`** — depgraph has it (moved to `_shared.py` in P2T9). Logigraph's `cmd_stats` has its own copy.

3. **`default_actor() -> str`** — logigraph has it; depgraph synthesizes the actor inline in `cmd_flag`. Worth sharing.

(Color helpers — `kg/cli/install/_shared.py` has them but depgraph/logigraph don't use color, so not lifted.)

---

## File structure

**New:**
- `kg/shared/__init__.py` — empty marker
- `kg/shared/git.py` — `git_commit_if_changed`, `default_actor`
- `kg/shared/telemetry.py` — `load_telemetry_events`
- `tests/kg/shared/test_git.py`, `tests/kg/shared/test_telemetry.py`

**Modified:**
- `depgraph/lib/cli/_shared.py` — re-export from `kg.shared.git` / `kg.shared.telemetry`; delete local copies.
- `logigraph/lib/cli/_shared.py` — same.
- Any subcommand modules that import from the local `_shared` keep working (the names re-export).

---

## Tasks (3)

### P5T1: Create `kg.shared` with git + telemetry modules + tests

- Create `kg/shared/__init__.py`, `kg/shared/git.py`, `kg/shared/telemetry.py`.
- Write the git module with `git_commit_if_changed(repo_dir, paths, message, actor=None) -> bool` and `default_actor() -> str`. The body is the union of depgraph's and logigraph's implementations — pick the logigraph version (which has the `actor` parameter) since it's the superset.
- Write the telemetry module with `load_telemetry_events(path, since_hours=None)`.
- Add `tests/kg/shared/conftest.py` and per-module test files. Cover the happy path + the no-events case for telemetry; cover git commit/no-change/with-actor cases for git_commit_if_changed.
- Run full suite — must stay at 340 passing.
- Commit.

### P5T2: depgraph/lib/cli/_shared.py re-exports + delete local copies

- In `depgraph/lib/cli/_shared.py`, replace the local `_depgraph_commit_if_changed` and `load_telemetry_events` with imports from `kg.shared.git` and `kg.shared.telemetry`. Keep the names backward-compat:
  ```python
  from kg.shared.git import git_commit_if_changed as _depgraph_commit_if_changed
  from kg.shared.telemetry import load_telemetry_events
  ```
- Delete the local bodies.
- Run full suite — must stay green.
- Commit.

### P5T3: logigraph/lib/cli/_shared.py re-exports + delete local copies

- Same pattern as P5T2 for logigraph: re-export `git_commit_if_changed`, `default_actor`, `load_telemetry_events` from `kg.shared`. Delete the local copies.
- The logigraph stats handler may currently inline `_load_telemetry_events` — update its import.
- Run full suite — must stay green.
- Commit.

Phase 5 ends here. Larger refactors (argparse helpers, output formatting) are deferred — most of the wins are in the git + telemetry consolidation, and further extraction risks over-abstraction without measurable benefit.
