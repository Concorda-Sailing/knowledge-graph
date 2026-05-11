# knowledge-graph

Umbrella for the **Concorda Sailing knowledge-graph substrate** — three
project-agnostic tools that together give an AI coding collaborator
working memory about a codebase:

| Tool | What it does | Repo |
|---|---|---|
| **depgraph** | Extracts code-structure nodes (models, services, endpoints, components, hooks, tests) + reverse-dependency index. Hooks into Claude Code's PreToolUse to inject dependent context before any edit. | [`Concorda-Sailing/depgraph`](https://github.com/Concorda-Sailing/depgraph) |
| **logigraph** | Authored business rules + a domain model (entities, relationships) with mediation-collision detection. Hooks inject applicable rule prose before edits. | [`Concorda-Sailing/logigraph`](https://github.com/Concorda-Sailing/logigraph) |
| **graphui** | FastAPI + Jinja2 viewer for both graphs. Renders dossiers, surfaces relationships, shows commit history and telemetry per node. Designed for desktop and mobile. | [`Concorda-Sailing/graphui`](https://github.com/Concorda-Sailing/graphui) |

The three pieces are **framework code only** — they ship no
project-specific data. Each project that uses them maintains its own
data dir (`<project>/depgraph/`, `<project>/logigraph/`) with its
extractors, nodes, dossiers, telemetry, and a `project.toml`
declaring the project's repos.

## Quick install

```bash
git clone https://github.com/Concorda-Sailing/knowledge-graph.git
cd knowledge-graph
./install.sh
```

The default target is `~/tools/` — pass `--target /some/other/path`
to override. The installer clones the three tool repos, sets up
graphui's Python venv, and prints the next steps for wiring hooks
into your Claude Code `~/.claude/settings.json`.

## What gets installed

```
~/tools/
├── depgraph/        # CLI, hooks, schema, generic reconcile
├── logigraph/       # CLI, hooks, schema, calibration stub
└── graphui/         # FastAPI viewer (+ .venv)
```

Nothing else is touched without your explicit consent. The installer
does **not** modify `~/.claude/settings.json` or register systemd
units automatically — it prints the snippets and lets you decide.

## Scaffold a new project

```bash
./install.sh init ~/myproject
```

Creates:

```
~/myproject/
├── depgraph/
│   ├── project.toml         # name, repo paths
│   ├── extractors/          # your project-specific extractors go here
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
   walk your codebase and emit JSON node files. The framework provides
   the JSON schema and a `reconcile` pass that builds reverse-dependency
   indexes.
2. **You hand-author (or LLM-draft + review) dossiers** — markdown
   files describing each significant node's purpose, invariants,
   gotchas. The depgraph hook injects these into Claude Code's
   reasoning context before any edit.
3. **You hand-author business rules** in `<project>/logigraph/nodes/
   rules/` with claims pointing at depgraph nodes. The logigraph hook
   injects applicable rule prose on every edit to a claimed file.
4. **The domain model** (`<project>/logigraph/nodes/domain/`)
   describes entities, roles, attributes, and the relationships
   between them. Relationships carry `from`, `to`, `mediated_by`,
   `cardinality`, `lifecycle`. Mediation collisions across distinct
   relationships are flagged at regen as design-defect signals.
5. **graphui** serves all of this over HTTP — coverage matrix,
   per-node detail with rules+dependents+history+telemetry, mediation
   collision banners, mobile-friendly layout.

## Telemetry

Both `depgraph` and `logigraph` log every injection (per
file-edit) and every acknowledgment (when the LLM's
transcript mentions a node or rule id post-hoc). Combined, this
answers "is the prose actually being read, or shouted into the void?"
View via `bin/depgraph stats --telemetry` and the graphui Telemetry
card per node.

## Status

This substrate was designed and built incrementally for the
[Concorda Sailing](https://members.massbaysailing.org/) project
between 2026-04 and 2026-05. The split into reusable tools landed
2026-05-11. Concorda's own use is the reference implementation.

For the longer arc this substrate is part of, see Logan Greenlee's
notes on POLIS.

## License

TBD — currently private repos under the Concorda-Sailing org. Open up
when there's a second project deploying these tools.
