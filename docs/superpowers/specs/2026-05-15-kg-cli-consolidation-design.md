# Consolidated `kg` CLI

**Status:** Design — approved 2026-05-15
**Owner:** Logan Greenlee
**Scope:** `~/tools/knowledge-graph/{bin,kg,depgraph,logigraph,install.sh}`

## Problem

The framework ships four entry points — `kg`, `depgraph`, `logigraph`, `install.sh` — exposing 54 subcommands between them. Names duplicate (`regen`, `validate`, `health`, `stats`, `self-check`, `context`, `flag`, `unflag` exist in both `depgraph` and `logigraph`) and there is no shared discovery surface: a user has to know which of four CLIs owns a verb before `--help` can help them. The orchestrator (`kg`) is a real Python package but exposes only 4 commands while the heavy lifters (`depgraph`, `logigraph`) are bare scripts disjoint from it. There is no project selector either — every command relies on `cd`-based auto-detection or environment-variable plumbing.

## Goals

- Single discoverable entry point: `kg --help` lists every capability under named groups.
- Project selector: pick a project once (`kg project use <name>`) or per-command (`--project <name>`); every subsystem command honors the same resolution order.
- Preserve `depgraph` and `logigraph` invocations as thin aliases so muscle memory, hooks, and the systemd unit keep working unchanged.
- Internal cleanup: extract `depgraph/bin/depgraph` (1601 LOC) and `logigraph/bin/logigraph` (2154 LOC) monoliths into per-subcommand modules so adding/maintaining commands stops requiring touching kilo-line files.
- Persistent docs: human-readable `docs/CLI.md` plus a cross-session memory entry for the agent.

## Non-goals

- No semantic collapse of same-named-but-different verbs. `depgraph regen` and `logigraph regen` extract different things; they stay as separate implementations under a unified entry point.
- No port of `install.sh` to Python in this work (deferred to Phase 4). Bash handles file/systemd plumbing well; the rewrite has no user-visible benefit until Phase 5's shared-infra extraction.
- No new graphui changes.
- No changes to the Claude Code hook surface — `kg hook ...` already exists and continues to be how `settings.json` dispatches.

## Top-level shape

Five groups under `kg`:

```
kg project      registry + per-project config + per-project ops (13 commands)
kg depgraph     code-graph operations (16)
kg logigraph    rules-graph operations (24)
kg install      machine setup (6)
kg hook         dispatcher invoked by Claude Code (1)
```

The orchestrator (`kg add/list/remove`) and the per-project config layer collapse into one — a registered graph **is** a project. There is no separate `kg graph` group.

### `kg project` — 13 commands

```
Discover & switch:
  kg project list                          list all registered projects (default marked *)
  kg project show [<name>]                 inspect one (defaults to current)
  kg project current                       print current project + how it was resolved
  kg project use <name>                    set persistent default (writes kg-graphs.toml)
  kg project use --clear                   unset default

Register / scaffold:
  kg project add <path>                    register existing data dir
  kg project remove <name>                 unregister (does not delete on disk)
  kg project init <path>                   scaffold fresh project (was: install.sh init)

Per-project config:
  kg project add-repo <key> <path> [--extractor ... --detector ... --files-arg=... --force]
  kg project list-repos
  kg project remove-repo <key>
  kg project set <field> <value>           whitelist: primary_repo, logigraph.data_dir, memory.dir

Cross-subsystem:
  kg project health                        runs depgraph health + logigraph health + repo-exists
```

### `kg depgraph` — 16 commands

```
Lifecycle:    regen [--all|--since REF]   validate [--strict]   self-check   health   stats [--telemetry]
Inspect:      context <target>            dependents <id> [--depth N]   orphans [--purge]
Dossiers:     dossier-rank                dossier-draft <target>   dossier-finalize <id> <body> [--authored-by ...]   dossier-bump <id> [--status ...]
Flag/audit:   flag <id> --reason ...      unflag <id>
Utility:      commit-summary [files...]   memory-sync
```

### `kg logigraph` — 24 commands

```
Lifecycle:    regen   validate [--strict]   self-check   health   stats
Inspect:      context <target>   rules-for <target>   fan-out <id>   gaps   rollup   dossiers
Rules:        rule-rank   rule-draft <id>   rule-finalize <id> <body>   rule-bump <id>   rule-stub <id>
Process:      process-rank   process-draft   process-finalize   process-bump   process-stub
Domain:       domain-bump <id>
Flag:         flag <id>   unflag <id>
```

### `kg install` — 6 commands

```
kg install tools [--target ... --data ...]      (was: install.sh install)
kg install hooks --project <dir> [--apply]
kg install systemd --project <dir> [--apply] [--depgraph-data-dir ... --logigraph-data-dir ...]
kg install path [--rcfile ... --apply --force]
kg install cascade <target-repo> --depgraph <dir> [--apply]
kg install bootstrap <project-dir> [--data ...]
```

### `kg hook` — 1 command

```
kg hook <phase>     existing dispatcher, invoked by Claude Code settings.json
```

### Naming convention

Flat-dash verbs inside groups, matching the existing `dossier-rank` / `rule-draft` style — never sub-sub-grouped:

- `kg project add-repo` (not `kg project repo add`)
- `kg depgraph dossier-rank` (not `kg depgraph dossier rank`)
- `kg logigraph rule-draft` (not `kg logigraph rule draft`)

Single-word verbs only when the group itself is the resource (`kg project list`, `kg project add`).

## Project resolution

Every subsystem command resolves a project before doing anything. First match wins:

1. `--project <name>` / `--data-dir <path>` flag — one-off override
2. `$KG_PROJECT` env var — session override
3. `$DEPGRAPH_DATA_DIR` / `$LOGIGRAPH_DATA_DIR` env vars — hook compat (settings.json sets these)
4. Walk cwd ancestors for `project.toml` + `nodes/` — auto-detect when inside a project tree
5. `default = "..."` in `~/.claude/kg-graphs.toml` — persistent default set by `kg project use`
6. If exactly one project is registered, use it implicitly
7. Error with the list of registered projects and the right `--project` flag for each

`~/.claude/kg-graphs.toml` gains an optional top-level `default` key:

```toml
default = "concorda"

[[graph]]
name = "concorda"
path = "/home/lgreenlee/concorda-knowledge-graph"

[[graph]]
name = "kg-framework"
path = "/home/lgreenlee/knowledge-graph-meta/knowledge-graph"
```

`kg project list` marks the default with `*`. `kg project current` prints the active project and which resolution rule fired (e.g. `concorda — from kg-graphs.toml default`).

## Architecture

### Code layout

```
~/tools/knowledge-graph/
├── kg/                              existing Python package — unified CLI lives here
│   ├── __init__.py
│   └── cli/
│       ├── __init__.py              top-level dispatcher, group registration
│       ├── resolve.py               NEW — project resolver (the 7-step order)
│       ├── project.py               kg project — list/show/use/current/add/remove/init/add-repo/...
│       ├── depgraph.py              kg depgraph — imports from depgraph.lib.cli
│       ├── logigraph.py             kg logigraph — imports from logigraph.lib.cli
│       ├── install.py               kg install — Phase 1: shells out to install.sh
│       └── hook.py                  kg hook — existing dispatcher, unchanged
│
├── depgraph/
│   ├── bin/depgraph                 thin shim → `kg depgraph` + remaining argv
│   ├── lib/
│   │   ├── config.py                existing, unchanged
│   │   └── cli/                     NEW — one module per subcommand
│   │       ├── __init__.py          register_subparsers(sub) — called by kg.cli.depgraph
│   │       ├── regen.py             extracted from bin/depgraph cmd_regen
│   │       ├── context.py
│   │       ├── dependents.py
│   │       ├── orphans.py
│   │       ├── validate.py
│   │       ├── self_check.py
│   │       ├── health.py
│   │       ├── stats.py
│   │       ├── commit_summary.py
│   │       ├── memory_sync.py
│   │       ├── dossier.py           rank/draft/finalize/bump
│   │       ├── flag.py              flag/unflag
│   │       └── repo.py              add-repo/list-repos/remove-repo (also wired into kg project)
│
├── logigraph/
│   ├── bin/logigraph                thin shim → `kg logigraph`
│   └── lib/cli/                     same pattern as depgraph
│       ├── regen.py / validate.py / health.py / stats.py / self_check.py / context.py
│       ├── rules_for.py / fan_out.py / gaps.py / rollup.py / dossiers.py
│       ├── rule.py / process.py / domain.py    (lifecycle: rank/draft/finalize/bump/stub)
│       └── flag.py
│
└── install.sh                       kept as-is in Phase 1; Phase 4 ports to kg.cli.install
```

### Three architectural decisions

**(a) Subcommand modules expose `register(subparsers)`, not just `cmd_*` handlers.** Argparse wiring lives next to the handler. `kg.cli.depgraph` reduces to ~30 lines: import each module, call its `register`. Adding a new subcommand is one file, no edits to the dispatcher.

**(b) `kg.cli.resolve.resolve_project()` runs at the start of every command, not at module import.** Returns a `Project` dataclass: `name`, `data_dir`, `depgraph_dir`, `logigraph_dir`, `source`. Today's `DEPGRAPH = resolve_data_dir(...)` at module-import time means `depgraph --help` from `~` is impossible — fixing that is a side benefit of this refactor.

**(c) `kg install` in Phase 1 is a Python wrapper that subprocesses `install.sh`.** No behavior change, just unifies help. Full port is Phase 4; install.sh's plumbing (systemd unit generation, hooks merge into settings.json, idempotent file writes) is fine in bash.

### Backward compatibility

- `depgraph <args>` → 5-line shim execs `kg depgraph <args>`. Output identical.
- `logigraph <args>` → same.
- `install.sh <subcommand> <args>` → unchanged.
- `kg hook ...` → unchanged, still invoked by `settings.json`.
- `~/.config/systemd/user/graphui.service` → unchanged (uvicorn ExecStart).

A scan of `~/.claude/settings.json` hook entries, the graphui systemd unit, and the cascade pre-push hook confirms no caller needs to change.

## Phasing

Five phases, each independently shippable. **The implementation plan that follows this design covers Phase 1 only.** Phases 2–5 each get their own design+plan cycle as scheduled. Phase 1 is the user-visible win; phases 2–5 are internal cleanup with no UX change.

- **Phase 1** — kg dispatcher, `kg.cli.resolve`, `kg project` group, `kg depgraph` / `kg logigraph` / `kg install` as subprocess shims into existing CLIs, CLI.md, memory entry. **Ships the discoverability and project-selector wins immediately.**
- **Phase 2** — extract `depgraph/bin/depgraph` subcommands into `depgraph/lib/cli/*.py` modules with `register(sub)` API. `kg.cli.depgraph` switches from subprocess to import-and-register. `bin/depgraph` becomes a 5-line shim.
- **Phase 3** — same for logigraph.
- **Phase 4** — port `install.sh` to `kg.cli.install` (Python). Keep install.sh as a shim for one release, then delete.
- **Phase 5** — shared infrastructure: argparse helpers, formatting, telemetry. Audit cross-subsystem duplication after phases 2–3 land.

## Persistent docs

Two artifacts shipped in Phase 1:

- **`docs/CLI.md`** in the kg-framework repo — human-discoverable. Full command tree, examples, migration table from old names, troubleshooting (resolution order, common errors).
- **`reference_kg_cli.md`** in the user's auto-memory — cross-session aide for the agent. Compact: group structure, recall hooks, gotchas (e.g. `--files-arg=--only` argparse quirk).

The memory entry links to the repo doc with `[[reference_kg_cli]]` linkbacks so future-me can verify against current state before recommending commands.

## Testing

Each phase has different shape:

- **Phase 1**: smoke-test that every command resolved via subprocess reproduces the existing CLI's output. Diff `kg depgraph regen --help` vs `depgraph regen --help`. Project-resolver unit tests for the 7-step order.
- **Phase 2 & 3**: per-subcommand-module unit tests as commands are extracted. The existing CLIs continue to work via the shim, so integration is verified by `bin/depgraph regen` (now shimming) producing the same output as before extraction.
- **Phase 4**: install.sh port replays the same `--apply` paths against a tempdir, diffs the resulting systemd unit / settings.json / Caddyfile against the bash version's output.
- **Phase 5**: no new behavior, regression-only.

## Open risks

- **`resolve_data_dir` is currently called at module-import time in `depgraph/bin/depgraph`.** Moving it inside command handlers may break callers that import depgraph modules and rely on `DEPGRAPH` being module-level. Phase 2 audits and fixes those sites.
- **`kg-graphs.toml` is read by both `kg` and the depgraph/logigraph hooks.** Adding a `default` key needs to be backward-compatible — older `kg` versions must ignore unknown top-level keys. The current parser (`tomllib.loads` then `cfg.get("graph", [])`) already does.
- **Argparse `nargs="+"` handlers consume positional args eagerly.** `kg project add-repo` already uses `--extractor` as `nargs="+"`; the design preserves this. Documented the `--files-arg=--only` workaround in help text.
