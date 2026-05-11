# knowledge-graph

A small, project-agnostic substrate that gives an AI coding
collaborator working memory about a codebase:

| Tool | What it does | Repo |
|---|---|---|
| **depgraph** | Extracts code-structure nodes (models, services, endpoints, components, hooks, tests) + reverse-dependency index. Hooks into Claude Code's PreToolUse to inject dependent context before any edit. | [`depgraph`](https://github.com/Concorda-Sailing/depgraph) |
| **logigraph** | Authored business rules + a domain model (entities, relationships) with mediation-collision detection. Hooks inject applicable rule prose before edits. | [`logigraph`](https://github.com/Concorda-Sailing/logigraph) |
| **graphui** | FastAPI + Jinja2 viewer for both graphs. Renders dossiers, surfaces relationships, shows commit history and telemetry per node. Desktop + mobile. | [`graphui`](https://github.com/Concorda-Sailing/graphui) |

The three pieces are **framework code only** — they ship no
project-specific data. Each project that uses them maintains its own
data dir (`<project>/depgraph/`, `<project>/logigraph/`) with its
extractors, nodes, dossiers, telemetry, and a `project.toml`
declaring the project's repos.

## Quick start

```bash
git clone https://github.com/Concorda-Sailing/knowledge-graph.git
cd knowledge-graph

# Install tools + scaffold a fresh project + wire hooks + register
# graphui daemon, in one shot:
./install.sh bootstrap ~/your-project
```

Or step-by-step:

```bash
./install.sh                                        # framework only
./install.sh init ~/your-project                    # scaffold empty data dir
./install.sh hooks --project ~/your-project --apply # wire Claude Code hooks
./install.sh systemd --project ~/your-project --apply  # graphui daemon
```

If you already have a data repo to clone:

```bash
./install.sh --data owner/repo=~/your-project/depgraph
./install.sh hooks --project ~/your-project --apply
./install.sh systemd --project ~/your-project --apply
```

### Agent-runnable

`install.sh` is safe for Claude Code (or any other LLM agent) to run
unattended:

- No interactive prompts.
- Idempotent — re-running with the same args reports `already match`,
  `already current`, `already active`, and exits 0.
- ANSI colors auto-suppress when stdout is not a TTY (or `NO_COLOR=1`
  is set).
- Side-effecting subcommands (`hooks --apply`, `systemd --apply`)
  back up the existing file before writing.
- Exits non-zero on any failure; everything important goes to stderr.

## What gets installed

```
~/tools/
├── depgraph/        # CLI, hooks, schema, generic reconcile
├── logigraph/       # CLI, hooks, schema, calibration stub
└── graphui/         # FastAPI viewer (+ .venv)
```

## What you scaffold

```
~/your-project/
├── depgraph/
│   ├── project.toml         # name, repo paths
│   ├── extractors/          # your project-specific extractors
│   ├── nodes/               # populated by `bin/depgraph regen`
│   ├── dossiers/            # plain-language dossiers per node
│   └── telemetry/           # injection + acknowledgment logs
└── logigraph/
    ├── project.toml
    ├── nodes/{rules,domain}/
    ├── dossiers/{rules,domain}/
    └── telemetry/
```

## How the pieces fit

1. **You write extractors** in `<project>/depgraph/extractors/` that
   walk your codebase and emit JSON node files. The framework
   provides the JSON schema and a `reconcile` pass that builds
   reverse-dependency indexes.
2. **You hand-author (or LLM-draft + review) dossiers** — markdown
   files describing each significant node's purpose, invariants,
   gotchas. The depgraph hook injects these into Claude Code's
   reasoning context before any edit.
3. **You hand-author business rules** in `<project>/logigraph/nodes/
   rules/` with claims pointing at depgraph nodes. The logigraph
   hook injects applicable rule prose on every edit to a claimed
   file.
4. **The domain model** (`<project>/logigraph/nodes/domain/`)
   describes entities, roles, attributes, and the relationships
   between them. Relationships carry `from`, `to`, `mediated_by`,
   `cardinality`, `lifecycle`. Mediation collisions across distinct
   relationships are flagged at regen as design-defect signals.
5. **graphui** serves all of this over HTTP — coverage matrix,
   per-node detail with rules + dependents + history + telemetry,
   mediation collision banners, mobile-friendly layout.

## Telemetry

Both `depgraph` and `logigraph` log every injection (per file-edit)
and every acknowledgment (when the LLM's transcript mentions a node
or rule id post-hoc). Combined, this answers *"is the prose actually
being read, or shouted into the void?"* View via `bin/depgraph stats
--telemetry` and the graphui Telemetry card per node.

## Provenance

This substrate was designed and built incrementally as the internal
collaboration infrastructure for one project, then split into
reusable tools when it became clear the shape was general. There is
not yet a second project deploying it — early adopters welcome.

## License

[MIT](./LICENSE). Copyright (c) 2026 Logan Greenlee.

The software is provided **AS IS**, without warranty of any kind,
express or implied, including but not limited to merchantability,
fitness for a particular purpose, and non-infringement. See the
LICENSE file for the full text.
