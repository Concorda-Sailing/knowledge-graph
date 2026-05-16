# Consolidated `kg` CLI — Phase 4: port install.sh to Python

> Subagent-driven execution. Steps use `- [ ]` syntax.

**Goal:** Port `install.sh` (978 LOC bash, 7 subcommands) to Python under `kg/cli/install/`. Replace the Phase-1 subprocess shim with native registration. Keep `install.sh` as a back-compat alias for one transition release.

**Architecture:** Each install.sh subcommand becomes a focused module under `kg/cli/install/`. Helper functions (color output, backup_file, idempotent file writers, TOML/JSON merge) live in `kg/cli/install/_shared.py`. The `kg install` group's `register(sub)` adds one subparser per module.

**Tech Stack:** Python 3.11+ (stdlib only — no new deps). Subprocess for `git clone/pull` and `systemctl --user`.

---

## File structure

**New under `kg/cli/install/`:**
```
__init__.py          build_parser() + register-each-module
_shared.py           color helpers, backup_file, write_managed_block,
                     idempotent_write, run_systemctl, etc.
tools.py             cmd_tools (was cmd_install)
init.py              cmd_init (project scaffold)
hooks.py             cmd_hooks (settings.json hook block writer)
systemd.py           cmd_systemd (graphui unit gen + apply)
path.py              cmd_path (shell PATH block)
cascade.py           cmd_cascade (pre-push hook installer)
bootstrap.py         cmd_bootstrap (orchestrates tools+init+hooks+systemd+path)
```

**Modified:**
- `kg/cli/install.py` — currently a 30-line subprocess shim into install.sh. Becomes `kg/cli/install/__init__.py` package layout with `register(sub)` that imports each module's `register`.
- `install.sh` — kept as a back-compat wrapper that execs `kg install <argv>`. Will be deleted in a future release.

**New tests under `tests/kg/install/`:**
- `conftest.py` — fixtures for tmp_path-based install targets
- One test file per subcommand exercising idempotent apply paths

---

## Task list (9 tasks)

### P4T1: Foundation — convert `kg/cli/install.py` to package + `_shared.py`

- Move `kg/cli/install.py` → `kg/cli/install/__init__.py` (verbatim subprocess shim — no behavior change yet).
- Create `kg/cli/install/_shared.py` with:
  - Color output helpers (`color_red`, `color_green`, `color_yellow`, `color_dim` — mirror install.sh's TTY-aware behavior)
  - `log()`, `ok()`, `warn()`, `err()`, `die()` (print-style equivalents of the shell functions)
  - `backup_file(path: Path) -> None` — same `.bak.<mtime>` semantics
  - `require(cmd: str) -> None` — raises SystemExit if not on PATH
  - `check_prereqs()` — Python 3.10+ + git
- Run existing tests (258 pass). Smoke `kg install --help` still routes to install.sh (no behavior change). Commit.

### P4T2: Port `init` (scaffold a project's knowledge-graph layout)

Replace the subprocess-shim path in `kg/cli/install/__init__.py` for the `init` subcommand. Add `kg/cli/install/init.py`:
- `cmd_init(args)` mirrors `install.sh:234:cmd_init()` — creates `<project>/knowledge-graph/{depgraph,logigraph}/{project.toml,nodes/,dossiers/}` etc.
- Test: feed a tmp_path, assert directory layout + file contents.
- Update `kg/cli/install/__init__.py` to register `init` natively (no subprocess for this subcommand).
- Also flip `kg.cli.project._cmd_init` to call the Python init directly instead of shelling out.

### P4T3: Port `tools` (was `install`)

- Add `kg/cli/install/tools.py` with `cmd_tools(args)`.
- Mirrors `install.sh:151:cmd_install()`: clones depgraph/logigraph/graphui sub-repos if not present, runs `pip install -r requirements.txt` for graphui.
- Test against a tmp target path; verify the venv bootstrap + (mocked) git clone.

### P4T4: Port `hooks`

- `kg/cli/install/hooks.py` with `cmd_hooks(args)`.
- Mirrors `install.sh:409:cmd_hooks()`: emits the Claude Code hook block (settings.json snippet pointing at `kg hook ...`). `--apply` merges into `~/.claude/settings.json` preserving other hooks.
- Test: assert the apply-to-empty-settings produces a well-formed JSON; idempotent re-apply is a no-op; existing hooks of other types are preserved.

### P4T5: Port `systemd`

- `kg/cli/install/systemd.py` with `cmd_systemd(args)`.
- Largest port — `install.sh:548:cmd_systemd()` is 150 LOC. Generates graphui unit, validates data dirs exist (Phase 1 bug fix), bootstraps venv if missing, writes unit to `~/.config/systemd/user/`, runs `systemctl --user daemon-reload && enable && start`.
- All the Phase-1 install.sh improvements (sibling-with-hyphen layout, --depgraph-data-dir / --logigraph-data-dir overrides, preflight refusal, venv bootstrap) ported verbatim.
- Tests: unit-file generation against a tmp target; preflight refusal on missing data dirs; sibling-layout auto-detect.

### P4T6: Port `path`

- `kg/cli/install/path.py` with `cmd_path(args)`.
- Mirrors `install.sh:699:cmd_path()`: appends a sentinel-guarded PATH block to ~/.profile (or chosen rcfile). Idempotent. `--force` replaces a stale block.
- Test against a tmp rcfile.

### P4T7: Port `cascade`

- `kg/cli/install/cascade.py` with `cmd_cascade(args)`.
- Mirrors `install.sh:887:cmd_cascade()`: writes a pre-push hook into a target repo's `.git/hooks/pre-push` that regenerates the KG and commits/pushes KG changes when the target pushes.
- Test against a tmp repo.

### P4T8: Port `bootstrap`

- `kg/cli/install/bootstrap.py` with `cmd_bootstrap(args)`.
- Mirrors `install.sh:813:cmd_bootstrap()`: calls tools → init (or use-existing) → hooks → kg-orchestrator-register → systemd → path. Re-uses the other modules' handlers in-process.
- Test: dry-run path with mocked subprocess calls; verify orchestration order.

### P4T9: Convert `install.sh` to a thin alias of `kg install`

- Replace `install.sh` (978 LOC bash) with a ~10-line wrapper:
  ```bash
  #!/usr/bin/env bash
  # install.sh — back-compat alias. Real implementation lives in kg.cli.install.
  exec /home/lgreenlee/tools/knowledge-graph/bin/kg install "$@"
  ```
- Verify `install.sh systemd --project ~/foo --apply` and similar invocations still work.
- Commit.

(A separate future task can delete `install.sh` entirely once external scripts that hit it are migrated.)

---

## Phase 4 rules

- **NO behavior changes** — the Python port produces identical files, exit codes, and output as the bash version (subject to argparse formatting nuance for --help).
- **Idempotency preserved** — every `--apply` must be a no-op when the target state already matches.
- **Backups preserved** — every write to an existing file backs up to `<path>.bak.<mtime>` first, matching install.sh's `backup_file()`.
- Tests under `tests/kg/install/`, not buried in `tests/kg/`.
- Subagents follow Phase 2/3 patterns: REPLACE not ADD, system python, etc.
