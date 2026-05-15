# Consolidated `kg` CLI — Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract `depgraph/bin/depgraph` (~1600 LOC) into per-subcommand modules under `depgraph/lib/cli/`, introduce a `Context` dataclass that replaces the import-time `DEPGRAPH = resolve_data_dir(...)` global, and switch `kg.cli.depgraph` from the Phase 1 subprocess shim to native import-and-register.

**Architecture:** Each subcommand becomes `depgraph/lib/cli/<name>.py` exporting `cmd_<name>(args, ctx)` and `register(sub)`. Shared utilities live in `depgraph/lib/cli/_shared.py`. The standalone `bin/depgraph` script slims to ~15 lines that construct a `Context` and dispatch. The Phase-1 `kg.cli.depgraph` subprocess shim is replaced by native imports from `depgraph.lib.cli`.

**Tech Stack:** Python 3.11+, argparse, frozen dataclass for `Context`, pytest with `tmp_path` fixtures replacing the previous module-level DEPGRAPH dependency.

---

## File Structure

**New files (in `~/tools/knowledge-graph/depgraph/lib/cli/`):**
- `__init__.py` — `build_parser()` + module registration order
- `context.py` — `Context` dataclass + `from_data_dir`
- `_shared.py` — `find_nodes_for_target`, `_depgraph_commit_if_changed`, `mark_regen_in_progress`, `load_dependents_index` (each takes `ctx`)
- `regen.py`, `context_cmd.py`, `dependents.py`, `orphans.py`, `validate.py`, `self_check.py`, `health.py`, `stats.py`, `commit_summary.py`, `memory_sync.py`, `dossier.py`, `flag.py`, `repo.py` — 13 subcommand modules

**Modified files:**
- `depgraph/bin/depgraph` — shrinks from 1600 LOC to ~15 LOC over the extraction tasks; final shape constructs `Context` and dispatches
- `kg/cli/depgraph.py` — switches from `os.execvpe` to native subparser registration

**New tests (in `~/tools/knowledge-graph/tests/depgraph/`):**
- `conftest.py` — shared `Context` fixture
- `test_cli_smoke.py` — integration tests invoking `bin/depgraph` via subprocess
- Per-module test files added incrementally with each extraction (no large upfront test churn)

**Migrated tests:**
- `tests/kg/test_cli_subprocess_shims.py` — the depgraph shim tests stay green but get joined by an in-process assertion that `kg depgraph regen --help` reaches a real help surface.

---

## Task 1: Foundation — `Context`, `_shared`, dispatcher skeleton

**Files:**
- Create: `depgraph/lib/cli/__init__.py`
- Create: `depgraph/lib/cli/context.py`
- Create: `depgraph/lib/cli/_shared.py`
- Create: `tests/depgraph/conftest.py`
- Create: `tests/depgraph/test_context.py`

- [ ] **Step 1: Failing test for `Context.from_data_dir`**

Create `tests/depgraph/conftest.py`:

```python
"""Shared fixtures for depgraph.lib.cli tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

TOOL_ROOT = Path(__file__).resolve().parents[2]
DEPGRAPH_ROOT = TOOL_ROOT / "depgraph"
sys.path.insert(0, str(DEPGRAPH_ROOT))


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    """Build a minimal depgraph data dir with nodes/ + telemetry/."""
    (tmp_path / "nodes" / "_index").mkdir(parents=True)
    (tmp_path / "telemetry").mkdir()
    (tmp_path / "project.toml").write_text(
        '[project]\nname = "test"\n'
    )
    return tmp_path
```

Create `tests/depgraph/test_context.py`:

```python
"""Tests for depgraph.lib.cli.context.Context."""
from __future__ import annotations

from pathlib import Path

from lib.cli.context import Context


def test_from_data_dir_derives_paths(data_dir: Path) -> None:
    ctx = Context.from_data_dir(data_dir)
    assert ctx.DEPGRAPH == data_dir
    assert ctx.NODES == data_dir / "nodes"
    assert ctx.DEPENDENTS_INDEX == data_dir / "nodes" / "_index" / "dependents.json"
    assert ctx.CORPUS_META == data_dir / "nodes" / "_meta.json"
    assert ctx.TELEMETRY_DIR == data_dir / "telemetry"
    assert ctx.INJECTIONS_LOG == data_dir / "telemetry" / "injections.jsonl"
    assert ctx.ACKS_LOG == data_dir / "telemetry" / "acknowledgments.jsonl"


def test_framework_python_resolves_to_venv_when_available(data_dir: Path) -> None:
    """If the framework's .venv/bin/python3 exists, ctx.framework_python is that path."""
    ctx = Context.from_data_dir(data_dir)
    # Just assert it's a non-empty string; existence depends on the dev env.
    assert ctx.framework_python


def test_context_is_frozen(data_dir: Path) -> None:
    """Context is a frozen dataclass — mutation raises."""
    ctx = Context.from_data_dir(data_dir)
    import dataclasses
    with __import__("pytest").raises((dataclasses.FrozenInstanceError, AttributeError)):
        ctx.DEPGRAPH = Path("/elsewhere")  # type: ignore[misc]
```

- [ ] **Step 2: Run — expect import error**

```bash
cd /home/lgreenlee/tools/knowledge-graph
python3 -m pytest tests/depgraph/test_context.py -q
```

Expected: `ModuleNotFoundError: No module named 'lib.cli.context'`.

- [ ] **Step 3: Create `depgraph/lib/cli/context.py`**

```python
"""Per-invocation context shared by every depgraph subcommand handler.

Eliminates the import-time `DEPGRAPH = resolve_data_dir(...)` side effect
that prevented kg.cli.depgraph from importing handlers natively.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


# Tool location (where this package lives) — schemas, framework code.
_TOOL_ROOT = Path(__file__).resolve().parents[2]
_VENV_PYTHON = _TOOL_ROOT / ".venv" / "bin" / "python3"
_FRAMEWORK_PYTHON = str(_VENV_PYTHON) if _VENV_PYTHON.exists() else "python3"


@dataclass(frozen=True)
class Context:
    """Per-invocation paths derived from the resolved depgraph data dir.

    Built once in main() and passed to every cmd_* handler.
    """
    DEPGRAPH: Path
    NODES: Path
    DEPENDENTS_INDEX: Path
    CORPUS_META: Path
    TELEMETRY_DIR: Path
    INJECTIONS_LOG: Path
    ACKS_LOG: Path
    framework_python: str
    tool_root: Path

    @classmethod
    def from_data_dir(cls, data_dir: Path) -> "Context":
        dd = Path(data_dir).expanduser().resolve()
        nodes = dd / "nodes"
        return cls(
            DEPGRAPH=dd,
            NODES=nodes,
            DEPENDENTS_INDEX=nodes / "_index" / "dependents.json",
            CORPUS_META=nodes / "_meta.json",
            TELEMETRY_DIR=dd / "telemetry",
            INJECTIONS_LOG=dd / "telemetry" / "injections.jsonl",
            ACKS_LOG=dd / "telemetry" / "acknowledgments.jsonl",
            framework_python=_FRAMEWORK_PYTHON,
            tool_root=_TOOL_ROOT,
        )
```

- [ ] **Step 4: Create `depgraph/lib/cli/_shared.py`**

Copy these functions verbatim from `depgraph/bin/depgraph` (look up their current line numbers — they may have moved since the spec was written):
- `mark_regen_in_progress` — adapt to take `ctx` instead of using module globals; rename references from `NODES` → `ctx.NODES`, `CORPUS_META` → `ctx.CORPUS_META`
- `load_dependents_index` — same adaptation; uses `ctx.DEPENDENTS_INDEX`
- `find_nodes_for_target` — same; uses `ctx.NODES`, `project_repos(ctx.DEPGRAPH)`
- `_depgraph_commit_if_changed` — same; uses `ctx.DEPGRAPH` to set git cwd

Header for the file:

```python
"""Shared utilities used by multiple depgraph subcommand handlers.

Every function takes `ctx: Context` as its first parameter so handlers
don't reach for module globals. This is the refactor that unblocks
native import-and-register from kg.cli.depgraph.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# Make depgraph/lib/config importable.
_DEPGRAPH_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_DEPGRAPH_ROOT))
from config import project_repos  # noqa: E402

from .context import Context
```

Then port each function with `ctx: Context` as the new first arg. Example for `mark_regen_in_progress`:

```python
def mark_regen_in_progress(ctx: Context) -> None:
    """Defect #2: write a regen marker so the hook can surface ..."""
    import datetime as _dt
    ctx.NODES.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "regen_status": "in_progress",
        "started_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
    }
    if ctx.CORPUS_META.exists():
        try:
            existing = json.loads(ctx.CORPUS_META.read_text())
            payload = {**existing, **payload}
        except (OSError, json.JSONDecodeError):
            pass
    tmp = ctx.CORPUS_META.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n")
    tmp.replace(ctx.CORPUS_META)
```

Similar mechanical changes for the other three. **Do not change behavior** — only the source of the paths.

- [ ] **Step 5: Create `depgraph/lib/cli/__init__.py`** (skeleton — modules wired in later tasks)

```python
"""depgraph CLI — modular subcommand layout.

Each subcommand has its own module exposing `cmd_<name>(args, ctx)` and
`register(sub)`. The dispatcher (`build_parser`) imports each module and
registers it; both `bin/depgraph` and `kg.cli.depgraph` call into the
same handlers.
"""
from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    """Construct the depgraph CLI's argparse tree.

    Modules are added in the same order as the legacy bin/depgraph script
    so --help output stays consistent.
    """
    parser = argparse.ArgumentParser(prog="depgraph")
    sub = parser.add_subparsers(dest="cmd", required=True)
    # Modules wired in subsequent tasks (Tasks 2–14):
    #   regen, context_cmd, dependents, orphans, validate, self_check,
    #   health, stats, commit_summary, memory_sync, dossier, flag, repo
    return parser
```

- [ ] **Step 6: Run tests — expect pass**

```bash
python3 -m pytest tests/depgraph/test_context.py -q
python3 -m pytest tests/ -q
```

Expected: `test_context.py` tests pass (3); existing 82 kg tests still pass; total 85.

- [ ] **Step 7: Commit**

```bash
git add depgraph/lib/cli/ tests/depgraph/
git commit -m "$(cat <<'EOF'
depgraph/lib/cli: foundation — Context dataclass, _shared utilities, build_parser skeleton

Phase 2 of the consolidated-kg-CLI rework needs a per-invocation
Context that replaces the import-time DEPGRAPH module global. This
commit ships:

  - depgraph/lib/cli/context.py    Context dataclass (frozen) +
                                   from_data_dir classmethod
  - depgraph/lib/cli/_shared.py    mark_regen_in_progress,
                                   load_dependents_index,
                                   find_nodes_for_target,
                                   _depgraph_commit_if_changed —
                                   each takes ctx as first arg
  - depgraph/lib/cli/__init__.py   build_parser() skeleton; module
                                   registrations added in Tasks 2-14

No subcommand has been extracted yet. bin/depgraph is unchanged and
keeps working exactly as before. Tasks 2-14 extract handlers one
module at a time; Task 15 slims bin/depgraph; Task 16 switches
kg.cli.depgraph to native registration.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Tasks 2–14: Extract subcommands (one per task)

Each extraction follows the same pattern:

1. **Read the handler in `depgraph/bin/depgraph`.** Find `cmd_<name>` and its corresponding `p_<name> = sub.add_parser(...)` block.
2. **Create `depgraph/lib/cli/<name>.py`** with:
   - The `cmd_<name>` body copied verbatim, but:
     - First parameter changes from `args: argparse.Namespace` to `args: argparse.Namespace, ctx: Context`
     - Every reference to module globals (`DEPGRAPH`, `NODES`, `DEPENDENTS_INDEX`, etc.) becomes `ctx.<NAME>`
     - Calls to shared helpers (`find_nodes_for_target`, `mark_regen_in_progress`, etc.) become `from ._shared import ...` and pass `ctx`
   - A `register(sub)` function that mirrors the existing `p_<name> = sub.add_parser(...)` block, ending with `p.set_defaults(func=cmd_<name>)`
3. **Update `depgraph/lib/cli/__init__.py`** to import and register the new module.
4. **Update `depgraph/bin/depgraph`**:
   - Replace the local `cmd_<name>` definition with `from lib.cli.<name> import cmd_<name>` (one line), OR delete it and adapt `bin/depgraph`'s dispatch to call it through ctx. Easiest: keep a one-line wrapper:
     ```python
     def cmd_<name>(args):
         from lib.cli.<name> import cmd_<name> as _impl
         return _impl(args, _CTX)  # _CTX is the module-level Context, constructed in main()
     ```
     — this means `bin/depgraph` still has a `_CTX` module global during extraction, but it's a Context not loose paths. Task 15 finishes the cleanup.
   - Replace the manual `p_<name> = sub.add_parser(...)` block with: just delete it; the parser is built by `lib.cli.build_parser()` now (well, after Task 15). During the extraction phase, leave the parser block in place but ensure each module's `register(sub)` is also called when `build_parser` is invoked.
5. **Write a per-module test** under `tests/depgraph/test_cli_<name>.py` exercising the handler directly with a fixture-built Context.
6. **Run tests + commit.**

To keep this plan readable, the 13 extraction tasks below give the **module name + line range to extract** rather than full handler code. Each task should reach a green test run before the commit.

### Task 2: `regen` → `depgraph/lib/cli/regen.py`

**Source:** `cmd_regen` (around lines 104–142) and `p_regen` block (around lines 1406–1409) in `depgraph/bin/depgraph`. Note: `cmd_regen` calls `mark_regen_in_progress()`, `project_repos(DEPGRAPH)`, `render_extractor`, `repo_detectors`, and `subprocess.call`. Adapt: receive `ctx`, pass `ctx` to `mark_regen_in_progress`, use `ctx.DEPGRAPH` for `project_repos`, `ctx.framework_python` for the reconcile subprocess.

**Test:** `tests/depgraph/test_cli_regen.py` — assert `cmd_regen` returns 0 on an empty repo set (no extractors to run, reconcile no-ops) and writes `_meta.json` with `regen_status='complete'`.

- [ ] Steps 1–6 of the pattern. Commit message:
  ```
  depgraph/lib/cli: extract regen
  
  Moves cmd_regen out of bin/depgraph into a focused module that
  takes a Context rather than module globals. mark_regen_in_progress
  now receives ctx explicitly via _shared.
  ```

### Task 3: `context` → `depgraph/lib/cli/context_cmd.py`

Note the file is named `context_cmd.py` (not `context.py`) because the latter is taken by the Context dataclass. Subcommand stays `context`.

**Source:** `cmd_context` and `p_ctx` block. Uses `find_nodes_for_target`, `load_dependents_index`.

**Test:** `tests/depgraph/test_cli_context.py` — feed a fake node JSON into ctx.NODES; assert handler prints node id + title.

- [ ] Standard pattern. Commit: `depgraph/lib/cli: extract context (subcommand)`.

### Task 4: `dependents` → `depgraph/lib/cli/dependents.py`

**Source:** `cmd_dependents` and `p_dep` block. Uses `load_dependents_index`, walks transitively up to `--depth`.

**Test:** assert depth-1 returns direct dependents, depth-2 includes their dependents.

- [ ] Standard pattern.

### Task 5: `orphans` → `depgraph/lib/cli/orphans.py`

**Source:** `cmd_orphans` and `p_orph` block. Uses `find_nodes_for_target` indirectly; checks source paths against `project_repos`.

**Test:** assert orphan detection works on a node whose source path is missing.

- [ ] Standard pattern.

### Task 6: `validate` → `depgraph/lib/cli/validate.py`

**Source:** `cmd_validate` and `p_val` block. JSON-schema validates every node file.

**Test:** valid + invalid node → assert exit codes.

- [ ] Standard pattern.

### Task 7: `self-check` → `depgraph/lib/cli/self_check.py`

**Source:** `cmd_self_check` and `p_sc` block. Synthesizes a fake PreToolUse payload and runs the hook.

**Test:** assert non-zero exit when hook is missing; zero exit when present.

- [ ] Standard pattern.

### Task 8: `health` → `depgraph/lib/cli/health.py`

**Source:** `cmd_health` and `p_health` block. Composite check.

**Test:** assert "clean" output on empty graph + non-zero exit when stale dossiers present.

- [ ] Standard pattern.

### Task 9: `stats` → `depgraph/lib/cli/stats.py`

**Source:** `cmd_stats` and `p_stats` block. Includes `--telemetry` flag.

**Test:** assert output mentions tier-A coverage; assert `--telemetry` adds the injection/ack section.

- [ ] Standard pattern.

### Task 10: `commit-summary` → `depgraph/lib/cli/commit_summary.py`

**Source:** `cmd_commit_summary` and `p_cs` block. Generates the trailer text from changed files.

**Test:** feed a list of changed file paths, assert summary mentions affected nodes.

- [ ] Standard pattern.

### Task 11: `memory-sync` → `depgraph/lib/cli/memory_sync.py`

**Source:** `cmd_memory_sync` and `p_ms` block. Mirrors ~/.claude memories into a configured dir.

**Test:** assert files are copied and credentials redacted.

- [ ] Standard pattern.

### Task 12: `dossier-*` → `depgraph/lib/cli/dossier.py`

Groups 4 subcommands sharing dossier-path helpers:
- `cmd_dossier_rank` / `p_dr`
- `cmd_dossier_draft` / `p_dd`
- `cmd_dossier_finalize` / `p_df`
- `cmd_dossier_bump` / `p_db`

**Module:** all 4 handlers + a `register(sub)` that registers all 4 subparsers.

**Test:** one test file with separate tests per handler.

- [ ] Standard pattern. Commit: `depgraph/lib/cli: extract dossier-rank / draft / finalize / bump`.

### Task 13: `flag`/`unflag` → `depgraph/lib/cli/flag.py`

Two subcommands sharing `find_nodes_for_target`:
- `cmd_flag` / `p_flag`
- `cmd_unflag` / `p_unflag`

**Test:** assert flag sets/clears `flagged=true` on the node JSON; assert commit happens.

- [ ] Standard pattern.

### Task 14: `repo-add`/`repo-list`/`repo-remove` → `depgraph/lib/cli/repo.py`

Three subcommands sharing `_strip_existing_repo_block` and `_format_repo_table` (already at the bottom of `bin/depgraph` from Phase 1):
- `cmd_repo_add` / `p_radd`
- `cmd_repo_list` / `p_rlist`
- `cmd_repo_remove` / `p_rrm`

Also move the helpers `_format_repo_table`, `_strip_existing_repo_block`, `_normalize_repo_path` into `repo.py` (these are repo-specific and unused elsewhere).

**Test:** roundtrip add → list → remove against a tmp project.toml.

- [ ] Standard pattern. Commit: `depgraph/lib/cli: extract repo-add / list / remove + helpers`.

---

## Task 15: Slim `bin/depgraph` to the entry-point shim

**Files:**
- Modify: `depgraph/bin/depgraph`
- Create: `tests/depgraph/test_cli_smoke.py`

- [ ] **Step 1: Smoke test for `bin/depgraph`**

Create `tests/depgraph/test_cli_smoke.py`:

```python
"""End-to-end smoke test for bin/depgraph after the slim-down."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[2]
DEPGRAPH_BIN = TOOL_ROOT / "depgraph" / "bin" / "depgraph"


def test_help_lists_all_subcommands(tmp_path: Path) -> None:
    """bin/depgraph --help lists every subcommand."""
    (tmp_path / "nodes").mkdir()
    (tmp_path / "project.toml").write_text('[project]\nname = "t"\n')
    res = subprocess.run(
        [sys.executable, str(DEPGRAPH_BIN), "--help"],
        capture_output=True, text=True,
        env={**os.environ, "DEPGRAPH_DATA_DIR": str(tmp_path)},
    )
    assert res.returncode == 0
    expected = [
        "regen", "context", "dependents", "orphans", "validate",
        "self-check", "health", "stats", "commit-summary", "memory-sync",
        "dossier-rank", "dossier-draft", "dossier-finalize", "dossier-bump",
        "flag", "unflag", "repo-add", "repo-list", "repo-remove",
    ]
    for sub in expected:
        assert sub in res.stdout, f"missing subcommand in --help: {sub}"


def test_validate_on_empty_repo_succeeds(tmp_path: Path) -> None:
    (tmp_path / "nodes").mkdir()
    (tmp_path / "project.toml").write_text('[project]\nname = "t"\n')
    res = subprocess.run(
        [sys.executable, str(DEPGRAPH_BIN), "validate"],
        capture_output=True, text=True,
        env={**os.environ, "DEPGRAPH_DATA_DIR": str(tmp_path)},
    )
    assert res.returncode == 0, f"stderr: {res.stderr}"
```

- [ ] **Step 2: Run — depending on Task 14's state, some assertions may fail**

```bash
python3 -m pytest tests/depgraph/test_cli_smoke.py -q
```

If extraction is complete (after Task 14), both tests should pass via the unmodified `bin/depgraph`. If not, fix before continuing.

- [ ] **Step 3: Slim `bin/depgraph` to the entry-point shim**

After all 13 extractions, `bin/depgraph` will still have a lot of dead code: the original `cmd_*` definitions (now replaced by `from lib.cli.<name> import cmd_<name>` shims), the manual subparser blocks (now duplicated by `lib.cli.build_parser`), and module-level constants. This step replaces the file with:

```python
#!/usr/bin/env python3
"""depgraph — CLI entrypoint. Constructs a Context from the resolved
data dir and dispatches into depgraph.lib.cli subcommand modules.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make depgraph/lib/ importable.
_DEPGRAPH_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_DEPGRAPH_ROOT))

from config import resolve_data_dir  # noqa: E402
from lib.cli import build_parser  # noqa: E402
from lib.cli.context import Context  # noqa: E402


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    data_dir = resolve_data_dir("DEPGRAPH_DATA_DIR")
    ctx = Context.from_data_dir(data_dir)
    return args.func(args, ctx)


if __name__ == "__main__":
    sys.exit(main())
```

(`from config import` works because `_DEPGRAPH_ROOT/config.py` is added to path; the file actually lives at `depgraph/lib/config.py`, so adjust: `sys.path.insert(0, str(_DEPGRAPH_ROOT / "lib"))` or use `from lib.config import resolve_data_dir`. Pick whichever matches the existing import in bin/depgraph.)

- [ ] **Step 4: Run smoke + full suite — expect green**

```bash
python3 -m pytest tests/ -q
```

Expected: all tests pass. The big behavior-preservation check is the smoke test in Step 1 — every subcommand listed, validate succeeds on empty repo.

- [ ] **Step 5: Diff-check legacy output against current**

For each subcommand with a `--help` flag, diff against the pre-Phase-2 output (saved as a fixture):

```bash
git show HEAD~16:depgraph/bin/depgraph > /tmp/pre-phase2-depgraph
# ... mechanical diff comparison left to the implementer
```

Or simpler: just verify `kg depgraph health` continues to byte-for-byte match `depgraph health` (this is the assertion from Phase 1 Task 16 — re-run it).

- [ ] **Step 6: Commit**

```bash
git add depgraph/bin/depgraph tests/depgraph/test_cli_smoke.py
git commit -m "$(cat <<'EOF'
depgraph/bin/depgraph: slim to entry-point shim

After all 13 subcommand modules have been extracted into
depgraph/lib/cli/, the original 1600-LOC script reduces to a
~15-LOC entry point that constructs a Context from the resolved
data dir and dispatches via lib.cli.build_parser().

bin/depgraph X output matches pre-refactor byte-for-byte (verified
against fixture and the kg depgraph parity diff).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 16: Switch `kg.cli.depgraph` to native registration

**Files:**
- Modify: `kg/cli/depgraph.py`
- Modify: `tests/kg/test_cli_subprocess_shims.py` (rename for clarity + extend)

- [ ] **Step 1: Extend the existing kg.cli.depgraph tests**

Append to `tests/kg/test_cli_subprocess_shims.py`:

```python
def test_kg_depgraph_regen_help_reaches_subcommand_help(single_project: dict) -> None:
    """After Phase 2, `kg depgraph regen --help` shows the regen subcommand's
    real argparse help, not just the top-level depgraph help."""
    res = _run(single_project["registry"], "depgraph", "regen", "--help")
    assert res.returncode == 0
    assert "--all" in res.stdout or "--since" in res.stdout
```

- [ ] **Step 2: Run — expect failure**

```bash
python3 -m pytest tests/kg/test_cli_subprocess_shims.py -q -k regen_help
```

Subprocess-shim path falls through to `depgraph regen --help` already so this might already pass — verify. If it does, skip ahead. If not, proceed to Step 3.

- [ ] **Step 3: Rewrite `kg/cli/depgraph.py` for native registration**

```python
"""kg depgraph — native subcommand registration via depgraph.lib.cli.

Phase 2 replaces the Phase-1 subprocess shim. kg now owns argparse
end-to-end; --help reaches the real subcommand help surface; handlers
run in-process. Exit codes and signals pass through naturally.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from kg.cli import resolve

_DEPGRAPH_LIB = Path(__file__).resolve().parents[2] / "depgraph" / "lib"
sys.path.insert(0, str(_DEPGRAPH_LIB))
from cli import build_parser as _depgraph_build_parser  # noqa: E402
from cli.context import Context as _DepgraphContext  # noqa: E402


def _run(args: argparse.Namespace, extra: list[str]) -> int:
    try:
        proj = resolve.resolve_project(
            project_name=getattr(args, "project", None),
            data_dir=Path(args.data_dir).expanduser() if getattr(args, "data_dir", None) else None,
        )
    except resolve.ProjectResolutionError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    sub_parser = _depgraph_build_parser()
    if extra and extra[0] in ("-h", "--help"):
        sub_parser.print_help()
        return 0
    sub_args = sub_parser.parse_args(extra)
    ctx = _DepgraphContext.from_data_dir(proj.depgraph_dir)
    return sub_args.func(sub_args, ctx)


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "depgraph",
        help="Code-graph operations (regen, dependents, dossiers, ...).",
        add_help=False,
    )
    p.add_argument("--project")
    p.add_argument("--data-dir")
    p.set_defaults(func=_run, wants_extra=True)
```

- [ ] **Step 4: Run — expect pass**

```bash
python3 -m pytest tests/kg/ -q
python3 -m pytest tests/ -q
```

Expected: full suite green.

- [ ] **Step 5: Byte-for-byte diff vs legacy**

```bash
diff <(DEPGRAPH_DATA_DIR=/home/lgreenlee/concorda-knowledge-graph/depgraph depgraph/bin/depgraph health 2>&1) \
     <(bin/kg depgraph health 2>&1)
echo "diff_exit=$?"
```

Expected: empty diff, exit 0. (Same check as Phase 1 Task 16, but now both paths run the same Python code in-process.)

- [ ] **Step 6: Commit**

```bash
git add kg/cli/depgraph.py tests/kg/test_cli_subprocess_shims.py
git commit -m "$(cat <<'EOF'
kg.cli.depgraph: switch to native subcommand registration

After Phase 2's extraction, kg.cli.depgraph imports from
depgraph.lib.cli and dispatches in-process instead of os.execvpe'ing
the depgraph binary.

Benefits:
  - `kg depgraph regen --help` reaches the real argparse help
    surface (Phase 1's add_help=False shim only routed top-level
    help to depgraph; per-subcommand help fell through to argparse
    inside the spawned process).
  - One Python process for the whole kg invocation — faster startup,
    better error formatting.
  - No DEPGRAPH_DATA_DIR env-var bridge needed; Context is built
    from the resolved project's depgraph_dir and passed in.

Output continues to byte-for-byte match `depgraph X`.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Self-review

**Spec coverage:**

- Foundation: Context + _shared + skeleton → Task 1 ✓
- 13 subcommand extractions → Tasks 2-14 ✓
- bin/depgraph slim → Task 15 ✓
- kg.cli.depgraph native → Task 16 ✓
- Behavior preservation (diff check) → Task 16 Step 5 ✓
- Per-module tests → each task's Step 5/test ✓

**Placeholder scan:** Tasks 2-14 reference "Source: cmd_X around lines Y-Z" rather than re-pasting 100-LOC handlers. This is deliberate — the extraction is mechanical, and re-pasting would 5x the plan file. Each task still says exactly what changes (first-arg signature, global → ctx, helper imports). If an implementer needs the exact code, they read `bin/depgraph` directly.

**Type consistency:**
- `Context` fields named identically everywhere (DEPGRAPH, NODES, etc. — uppercase to match the legacy module globals they replace).
- `cmd_<name>(args, ctx)` signature uniform across all 13 modules.
- `register(sub)` signature uniform.
- `build_parser()` signature stable (called by both entry points + by `kg.cli.depgraph._run`).

**Scope check:** 16 tasks; each is a single commit. Final state: depgraph is fully modularized; kg owns the full argparse tree for `kg depgraph`. Phases 3-5 will handle logigraph (same pattern), install.sh port, and shared-infra extraction in separate plans.
