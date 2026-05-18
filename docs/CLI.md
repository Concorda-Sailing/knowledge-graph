# `kg` CLI reference

Single entry point for the knowledge-graph framework. Five groups
under `kg`; legacy `depgraph` / `logigraph` / `install.sh` scripts
still work and behave identically.

## Quick start

    kg project add ~/my-project-knowledge-graph    # register
    kg project use my-project                       # set as default
    kg depgraph regen                               # now uses the default

## Project resolution

Every command picks a project via this 7-step order (first match wins):

1. `--project <name>` or `--data-dir <path>` flag
2. `$KG_PROJECT` env var
3. `$DEPGRAPH_DATA_DIR` / `$LOGIGRAPH_DATA_DIR` env var (hook compat)
4. cwd-ancestor walk for `project.toml` + `nodes/`
5. `default = "..."` in `~/.claude/kg-graphs.toml`
6. The only registered project (implicit)
7. Error — lists registered projects + the right `--project` flag

`kg project current` prints the active project and which rule fired.

## Commands

### `kg project` — registry + per-project config

| Command | Description |
|---|---|
| `kg project list` | List registered projects (default marked `*`) |
| `kg project show [<name>]` | Inspect a project (defaults to current) |
| `kg project current` | Print active project + how it was resolved |
| `kg project use <name>` | Set persistent default in `kg-graphs.toml` |
| `kg project use --clear` | Unset the default |
| `kg project add <path>` | Register a data dir with the orchestrator |
| `kg project remove <name>` | Unregister (does not delete on disk) |
| `kg project init <path>` | Scaffold a fresh project layout |
| `kg project add-repo <key> <path> [--extractor ... --detector ... --files-arg=... --force]` | Add a `[repos.<key>]` entry |
| `kg project list-repos` | List configured repos |
| `kg project remove-repo <key>` | Remove a `[repos.<key>]` entry |
| `kg project set <field> <value>` | Set a whitelisted project.toml field |
| `kg project health` | Cross-subsystem health (depgraph + logigraph + repo paths) |

`--project <name>` and `--data-dir <path>` are recognized on each
subsystem subcommand (`kg project`, `kg depgraph`, `kg logigraph`) and
override the resolution order for one invocation. The flag goes
**after** the subsystem name, e.g. `kg depgraph --project <name> regen`
— not `kg --project <name> depgraph regen` (argparse rejects that).

#### `kg project set` — whitelisted fields

- `primary_repo` — `[project] primary_repo`. Validated against `[repos.*]` keys.
- `logigraph.data_dir` — `[logigraph] data_dir`. Cross-graph pointer.
- `memory.dir` — `[memory] dir`. Where memory-sync mirrors `~/.claude` files.

### `kg depgraph` — code-graph operations

`kg depgraph <subcommand>` resolves a project, builds a depgraph
`Context` from the resolved data dir, and dispatches in-process via
`depgraph.lib.cli.build_parser()`. `--help` reaches the real
subcommand argparse surface (no longer the top-level help only).
Pass `--project <name>` or `--data-dir <path>` for non-default
targets.

Subcommands: `regen`, `validate`, `health`, `self-check`, `stats`,
`context`, `dependents`, `orphans`, `commit-summary`, `memory-sync`,
`dossier-rank`, `dossier-draft`, `dossier-finalize`, `dossier-bump`,
`flag`, `unflag`, `repo-add`, `repo-list`, `repo-remove`.

See `kg depgraph <cmd> --help` for full options.

### `kg logigraph` — rules-graph operations

Same native-dispatch pattern as `kg depgraph`. Builds a logigraph
`Context` that includes the resolved `depgraph_dir` (logigraph
claims bind to depgraph nodes).

Subcommands: `regen`, `validate`, `health`, `self-check`, `stats`,
`context`, `rules-for`, `fan-out`, `gaps`, `rollup`, `dossiers`,
`rule-rank`, `rule-draft`, `rule-finalize`, `rule-bump`, `rule-stub`,
`process-rank`, `process-draft`, `process-finalize`, `process-bump`,
`process-stub`, `domain-bump`, `flag`, `unflag`.

### `kg install` — machine setup

Native Python implementations under `kg/cli/install/`. Subcommands:
`tools`, `init`, `hooks`, `systemd`, `path`, `cascade`, `bootstrap`.
See `kg install --help`. `install.sh` is now a 10-line wrapper that
execs `kg install` — kept for back-compat with external callers
(docs, prior bootstrap scripts).

### `kg hook <phase>`

Invoked by Claude Code via `~/.claude/settings.json`, not by humans.
Phases: `pre-edit`, `post-edit`, `session-start`, `session-end`,
`pre-irreversible`.

## Migration table

| Old command | New canonical |
|---|---|
| `kg list` | `kg project list` |
| `kg add <path>` | `kg project add <path>` |
| `kg remove <name>` | `kg project remove <name>` |
| `depgraph regen` | `kg depgraph regen` (or unchanged) |
| `logigraph rules-for X` | `kg logigraph rules-for X` (or unchanged) |
| `install.sh init <dir>` | `kg project init <dir>` (or `kg install ...`) |

Legacy `kg list` / `depgraph regen` / `install.sh init` keep working
as aliases — no migration required for muscle memory.

## Common errors

**"Multiple projects registered — pass --project <name> AFTER the
subcommand"** — either set a default once with `kg project use <name>`,
or pass `--project <name>` directly to the subsystem subcommand:
`kg depgraph --project <name> regen`. The flag does **not** go on the
top-level `kg` — argparse rejects `kg --project <name> depgraph ...`.

**"Project not registered"** — list available: `kg project list`,
then `kg project add <path>` if missing.

**`argparse` error on `--files-arg --only`** — use `=` syntax:
`--files-arg=--only`. Argparse can't distinguish a value starting with
`--` from a flag.

## File locations

- Registry: `~/.claude/kg-graphs.toml` (machine-maintained, manual edits tolerated)
- Tools root: `~/tools/knowledge-graph/`
  - `kg/`, `depgraph/`, `logigraph/`, `graphui/` — the four subsystems
  - `bin/kg`, `bin/depgraph`, `bin/logigraph` — CLI entry points (thin shims into the Python packages)
  - `install.sh` — back-compat shim that execs `kg install`
  - `tests/` — cross-subsystem test suite (run with `pytest` from this dir)
- Per-project data: `<project>/knowledge-graph/{depgraph,logigraph}/` (or the sibling-with-hyphen layout `<project>-knowledge-graph/{depgraph,logigraph}/`)
- Claude Code hooks: `~/.claude/settings.json`
- Systemd unit (user-mode graphui): `~/.config/systemd/user/graphui.service`
