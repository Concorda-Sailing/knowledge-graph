# Consolidated `kg` CLI — Phase 2: extract depgraph subcommands

**Status:** Design — approved 2026-05-15
**Owner:** Logan Greenlee
**Scope:** `~/tools/knowledge-graph/{depgraph/bin/depgraph,depgraph/lib/cli/,kg/cli/depgraph.py}`

## Problem

`depgraph/bin/depgraph` is a 1601-LOC monolith hosting 18 subcommands (the original 16 plus `repo-add`, `repo-list`, `repo-remove` from Phase 1's prep work) and ~20 helper functions. Adding or maintaining a subcommand requires touching this single file. Worse, the script computes `DEPGRAPH = resolve_data_dir(...)` at module import time, which means importing it from `kg.cli.depgraph` (the Phase 1 subprocess shim) would trigger data-dir resolution before any command runs — making native import-and-register impossible.

Phase 1 worked around this by execing the script via subprocess. That preserves correctness but blocks the architectural goal: kg should own argument parsing, expose `--help` natively, and call into shared Python handlers without process boundaries.

## Goals

- Extract each subcommand into a focused module under `depgraph/lib/cli/<name>.py` with a uniform `register(sub)` API.
- Introduce a `Context` dataclass that holds `DEPGRAPH`, `NODES`, `DEPENDENTS_INDEX`, `CORPUS_META`, `TELEMETRY_DIR`, `INJECTIONS_LOG`, `ACKS_LOG`, and `framework_python`. Built once in `main()` from the resolved data-dir, passed to every handler.
- Both entry points (`bin/depgraph` standalone and `kg.cli.depgraph` via kg) construct `Context` and dispatch into the same `depgraph.lib.cli.*` modules. Zero duplication.
- `kg.cli.depgraph` switches from subprocess shim to native registration: `kg depgraph regen --help` becomes a real kg-owned help surface.
- No behavior changes. `kg depgraph X` and `depgraph X` continue to produce byte-for-byte identical output.

## Non-goals

- No new subcommands, no semantic changes, no UI tweaks.
- No changes to extractors, reconcile, dossier-storage, or graph-data format.
- No port of `logigraph` — Phase 3 covers logigraph with the identical pattern.
- No port of `install.sh` — Phase 4 territory.
- No shared-infra extraction across depgraph/logigraph — Phase 5.

## Architecture

### `Context` dataclass

```python
# depgraph/lib/cli/context.py
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Context:
    """Per-invocation paths derived from the resolved DEPGRAPH data dir.

    Constructed once in main() and passed to every cmd_* handler.
    Eliminates the module-level `DEPGRAPH = resolve_data_dir(...)`
    import-time side effect that blocked kg.cli.depgraph from
    importing handlers natively.
    """
    DEPGRAPH: Path
    NODES: Path
    DEPENDENTS_INDEX: Path
    CORPUS_META: Path
    TELEMETRY_DIR: Path
    INJECTIONS_LOG: Path
    ACKS_LOG: Path
    framework_python: str  # path to framework's venv python, or "python3"

    @classmethod
    def from_data_dir(cls, data_dir: Path) -> "Context":
        # ...derive all paths from data_dir
```

### Module structure

Thirteen modules under `depgraph/lib/cli/`:

```
__init__.py          exports build_parser() and dispatch() helpers
context.py           Context dataclass + from_data_dir
regen.py             cmd_regen
context_cmd.py       cmd_context (named with _cmd suffix to avoid clash with context.py)
dependents.py        cmd_dependents
orphans.py           cmd_orphans
validate.py          cmd_validate
self_check.py        cmd_self_check
health.py            cmd_health
stats.py             cmd_stats
commit_summary.py    cmd_commit_summary
memory_sync.py       cmd_memory_sync
dossier.py           cmd_dossier_rank / draft / finalize / bump (share node lookup + dossier path helpers)
flag.py              cmd_flag / cmd_unflag (share find_nodes_for_target)
repo.py              cmd_repo_add / list / remove (already share _strip_existing_repo_block + _format_repo_table)
```

Each module exposes:
- `cmd_<name>(args, ctx: Context) -> int` — the handler
- `register(sub: argparse._SubParsersAction) -> None` — adds the subparser, sets `func`

Shared utilities currently in `bin/depgraph` (e.g. `find_nodes_for_target`, `_depgraph_commit_if_changed`, `mark_regen_in_progress`, `load_dependents_index`) move to `depgraph/lib/cli/_shared.py` and take `ctx` as a parameter.

### Entry points

`depgraph/bin/depgraph` becomes ~15 lines:

```python
#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.config import resolve_data_dir
from lib.cli import build_parser
from lib.cli.context import Context

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    data_dir = resolve_data_dir("DEPGRAPH_DATA_DIR")
    ctx = Context.from_data_dir(data_dir)
    return args.func(args, ctx)

if __name__ == "__main__":
    sys.exit(main())
```

`kg/cli/depgraph.py` becomes a native subparser registrar (no more `os.execvpe`):

```python
"""kg depgraph — native subcommand registration via depgraph.lib.cli."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

from kg.cli import resolve

# Make depgraph/lib importable
_DEPGRAPH_ROOT = Path(__file__).resolve().parents[2] / "depgraph"
sys.path.insert(0, str(_DEPGRAPH_ROOT))
from lib.cli import build_parser as _depgraph_build_parser  # noqa: E402
from lib.cli.context import Context as _DepgraphContext  # noqa: E402


def _run(args, extra):
    try:
        proj = resolve.resolve_project(
            project_name=getattr(args, "project", None),
            data_dir=Path(args.data_dir).expanduser() if getattr(args, "data_dir", None) else None,
        )
    except resolve.ProjectResolutionError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    sub_parser = _depgraph_build_parser()
    sub_args = sub_parser.parse_args(extra)
    ctx = _DepgraphContext.from_data_dir(proj.depgraph_dir)
    return sub_args.func(sub_args, ctx)


def register(sub):
    p = sub.add_parser(
        "depgraph",
        help="Code-graph operations (regen, dependents, dossiers, ...).",
        add_help=False,
    )
    p.add_argument("--project")
    p.add_argument("--data-dir")
    p.set_defaults(func=_run, wants_extra=True)
```

(`add_help=False` and `wants_extra=True` from Phase 1 are preserved. Help still falls through to the depgraph subcommand's argparse instance, which now has a proper help surface.)

### Shared dispatcher

`depgraph/lib/cli/__init__.py` exposes:

```python
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="depgraph")
    sub = p.add_subparsers(dest="cmd", required=True)
    # import each module and call register
    from . import (regen, context_cmd, dependents, orphans, validate,
                   self_check, health, stats, commit_summary, memory_sync,
                   dossier, flag, repo)
    for mod in (regen, context_cmd, dependents, orphans, validate,
                self_check, health, stats, commit_summary, memory_sync,
                dossier, flag, repo):
        mod.register(sub)
    return p
```

## Testing

- **Per-module unit tests** under `tests/depgraph/test_cli_<name>.py`. Each test constructs a `Context` from a tmp_path fixture and calls the handler directly. Faster + more focused than subprocess tests.
- **Integration smoke** in `tests/depgraph/test_cli_smoke.py`: invokes `bin/depgraph` via subprocess against a real fixture, verifies output matches expectation.
- **kg/cli/depgraph parity check** in existing `tests/kg/test_cli_subprocess_shims.py`: the `kg depgraph --help` and `kg depgraph validate` tests stay green. After this phase, also assert that `kg depgraph regen --help` reaches the actual subcommand help (which now lives in `depgraph.lib.cli.regen.register`).
- **Behavior-preservation check** as a final task: diff `depgraph <every-subcommand> --help` before vs after the refactor across a temp checkout of the pre-refactor commit. Output must match byte-for-byte.

## Phasing within Phase 2

Within Phase 2, work proceeds in three internal stages:

1. **Foundation** (1 task): Create `Context` dataclass, `_shared.py` with utilities, and the `build_parser` skeleton. No subcommand extraction yet.
2. **Extraction** (13 tasks): One subcommand module per task. After each extraction, both `bin/depgraph` and the rest of `bin/depgraph` keep working (handlers gradually move out; the script becomes a shrinking adapter).
3. **Cutover** (2 tasks): `bin/depgraph` slims to the 15-line shim; `kg/cli/depgraph.py` switches from `os.execvpe` to native registration.

Total: ~16 tasks in the Phase 2 implementation plan.

## Open risks

- **Import-time side effects beyond `DEPGRAPH`.** `bin/depgraph` also computes `_VENV_PYTHON`, `FRAMEWORK_PYTHON`, `TOOL_ROOT`. These move to `Context` (for tool root + framework python) and `_shared.py` (for framework_python computation).
- **`find_nodes_for_target` is called by multiple subcommands.** Lives in `_shared.py` and takes `ctx` so the per-module handlers stay focused.
- **Argparse subparser ordering.** The `--help` output's subcommand list order depends on registration order. Phase 1's `bin/depgraph --help` shows: `regen, context, dependents, orphans, validate, self-check, health, stats, commit-summary, memory-sync, dossier-rank, dossier-draft, dossier-finalize, dossier-bump, flag, unflag, repo-add, repo-list, repo-remove`. The new `build_parser` must register modules in this same order so help output is identical.
- **Shared state via `_depgraph_commit_if_changed`.** Calls `subprocess.run(["git", ...])` inside DEPGRAPH dir. Stays in `_shared.py`; receives `ctx.DEPGRAPH` explicitly.
- **`os.environ` mutation in cmd_regen.** Adds `DEPGRAPH_DATA_DIR=...` to the subprocess env. Stays scoped to the handler.
- **kg.cli.depgraph: argparse exit on parse errors.** Argparse calls `sys.exit(2)` on bad args. When invoked through kg, that exits the kg process — desired behavior since the user invoked it directly.
