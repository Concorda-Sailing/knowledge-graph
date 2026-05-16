# knowledge-graph

A small, project-agnostic substrate that gives an AI coding collaborator working memory about a codebase. Four pieces:

| Tool | What it does |
|---|---|
| **depgraph** | Code-structure nodes (models, services, endpoints, components, hooks, tests) + reverse-dependency index. Hooks into Claude Code's PreToolUse to inject dependents before every edit. |
| **logigraph** | Authored business rules, domain entities, and process flows. Hooks inject applicable rule prose + flow context on edit. Mediation-collision detection flags design defects. |
| **graphui** | FastAPI + Jinja2 dark-themed viewer for both graphs. Coverage gallery, repo-and-kind navigation, mobile-friendly cards, Needs-attention card, review queue with promote-from-draft. |
| **kg** | Single CLI entry point. Five groups (`project / depgraph / logigraph / install / hook`) dispatching natively in-process. Reads `~/.claude/kg-graphs.toml`; fans Claude Code hook events to whichever registered graph owns the file being edited. |

All four ship from this repo. Framework code lives in `~/tools/knowledge-graph/{depgraph,logigraph,graphui,kg}/`. Per-project data lives in `<project>-knowledge-graph/{depgraph,logigraph}/` — nodes, dossiers, extractors, telemetry, plus a root `project.toml` declaring the project and subsystems.

**Canonical CLI reference: [`docs/CLI.md`](./docs/CLI.md).** This README is the install + runbook narrative; `docs/CLI.md` is the full command tree, project-resolution order, and migration table.

---

## For humans: install with Claude Code

Open Claude Code in any directory and ask. Claude reads this README and runs the steps.

> **"Install knowledge-graph for this codebase."**

Claude clones the framework to `~/tools/`, scaffolds your project's data dirs, wires the Claude Code hooks, starts the graphui daemon, and verifies everything. Idempotent — safe to re-run.

Other useful asks (Claude follows the runbook in the next section):

> **"Add a new tracked repo to the graph."**
>
> **"Author a rule for `<short description>`."**
>
> **"Show me what's pending review on the graph."**
>
> **"Why is `<flag>` showing on the dashboard?"**
>
> **"Open graphui."** (Claude tells you the URL — typically `http://localhost:8081/graph/` or the LAN equivalent.)

### Optional ergonomics

The `kg` entry point handles everything; legacy `depgraph` / `logigraph` / `install.sh` invocations still work as aliases.

```bash
# Put the kg CLI on PATH
echo 'export PATH="$HOME/tools/knowledge-graph/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Set a default project so bare commands resolve from any cwd:
kg project use <project-name>

# Now these work from anywhere:
kg depgraph regen
kg logigraph health
kg project list-repos
```

Or run `kg install path --apply` to write a sentinel-guarded PATH block to `~/.profile` that puts the legacy `depgraph` and `logigraph` bin dirs on PATH too (preserves muscle memory).

---

## For Claude: runbook

This section is the source of truth for what to do when a user asks for knowledge-graph operations. Read carefully before acting. **For the full command tree, see [`docs/CLI.md`](./docs/CLI.md)** — this runbook covers the common workflows.

### Core layout (mental model)

```
~/tools/knowledge-graph/              (framework — clone once, shared across projects)
├── bin/kg                            ← single CLI entry point
├── kg/                               ← Python package
│   ├── cli/                          ← argparse dispatcher
│   │   ├── __init__.py               ← top-level parser, registers 5 groups
│   │   ├── project.py                ← kg project (registry + per-project config)
│   │   ├── depgraph.py               ← kg depgraph (native dispatch to depgraph.lib.cli)
│   │   ├── logigraph.py              ← kg logigraph (native dispatch to logigraph.lib.cli)
│   │   ├── install/                  ← kg install (init/tools/hooks/systemd/path/cascade/bootstrap)
│   │   ├── orchestrator.py           ← legacy `kg list/add/remove/hook` aliases
│   │   └── resolve.py                ← 7-step project resolver
│   ├── registry.py                   ← kg-graphs.toml load/save
│   ├── hook.py                       ← Claude Code hook dispatcher (`kg hook <phase>`)
│   └── shared/                       ← cross-graph helpers (git, telemetry)
├── depgraph/
│   ├── __init__.py                   ← package marker (post-namespace-rename)
│   ├── bin/depgraph                  ← 28-line shim → depgraph.lib.cli dispatch
│   ├── lib/
│   │   ├── config.py                 ← project_repos, path_to_repo_relative, etc.
│   │   └── cli/                      ← one module per subcommand (regen, validate, dossier, …)
│   ├── hooks/                        ← Claude Code injectors (pre_edit, post_edit, telemetry)
│   ├── extractors/                   ← reconcile + language extractors
│   └── schema/                       ← node JSON schemas
├── logigraph/                        ← same layout (lib/cli, hooks, extractors, schema)
├── graphui/                          ← FastAPI viewer (app/, .venv/)
├── install.sh                        ← 10-line alias of `kg install` (back-compat)
├── docs/CLI.md                       ← user-facing CLI reference
├── CHANGELOG.md                      ← phase-by-phase user-visible changes
└── README.md                         ← this file

<project>-knowledge-graph/            (per-project data — one repo per project)
├── project.toml                      [project] name; subsystems = ["depgraph", "logigraph"]
├── depgraph/
│   ├── project.toml                  [project] primary_repo; [logigraph] data_dir;
│   │                                 [repos.<key>] path, extractor, files_arg
│   ├── extractors/                   project-specific extractors (extract_api.py, …)
│   ├── nodes/                        produced by `kg depgraph regen`
│   ├── dossiers/                     human-authored prose per node
│   └── telemetry/                    injections.jsonl, acknowledgments.jsonl
└── logigraph/
    ├── project.toml                  same shape; plus [depgraph] data_dir cross-ref
    ├── nodes/{rules,domain,processes}/
    ├── dossiers/{rules,domain,processes}/
    └── telemetry/

~/.claude/kg-graphs.toml              ← registered graphs (kg project add/remove/use edits this)
```

### Project resolution

Every `kg depgraph` / `kg logigraph` / `kg project` command resolves a project before running. First match wins:

1. `--project <name>` / `--data-dir <path>` flag
2. `$KG_PROJECT` env var
3. `$DEPGRAPH_DATA_DIR` / `$LOGIGRAPH_DATA_DIR` env vars (hook compat)
4. cwd-ancestor walk for `project.toml` + `nodes/`
5. `default = "..."` in `~/.claude/kg-graphs.toml` (set by `kg project use <name>`)
6. The only registered project (implicit)
7. Error — lists registered projects + the right `--project` flag for each

`kg project current` prints the active project and which rule fired.

### When the user asks: "Install knowledge-graph"

1. If `~/tools/knowledge-graph/` doesn't exist, clone it:
   ```bash
   git clone https://github.com/Concorda-Sailing/knowledge-graph.git ~/tools/knowledge-graph
   ```
2. Resolve the project path. If the user is `cd`'d into the project, use `$PWD`. Otherwise ask which project root to wire up. The data repo conventionally lives at `<project>-knowledge-graph/` (sibling to the source repos), but can live anywhere — `kg project add` takes the path.
3. Run the bootstrap:
   ```bash
   ~/tools/knowledge-graph/bin/kg install bootstrap <data-repo-path>
   ```
   This scaffolds `<data-repo-path>/{depgraph,logigraph}/` and the root `project.toml`, writes the hook entries into `~/.claude/settings.json`, registers the data repo via `kg project add`, and starts the graphui systemd `--user` service.
4. Verify:
   ```bash
   ~/tools/knowledge-graph/bin/kg project list                            # data repo appears
   ~/tools/knowledge-graph/bin/kg --project <name> depgraph self-check
   ~/tools/knowledge-graph/bin/kg --project <name> logigraph validate
   systemctl --user is-active graphui
   ```
5. Tell the user the graphui URL: `http://localhost:8081/graph/` (or LAN IP).

`install.sh bootstrap <data-repo-path>` is equivalent (it execs `kg install bootstrap`); use whichever shape the user prefers.

### When the user asks: "Add a new tracked repo"

The native command is `kg project add-repo`; manual TOML editing is no longer the primary path.

```bash
kg project add-repo <key> <path> \
  [--extractor <prog> <arg> ...] \
  [--detector <name> ...] \
  [--files-arg=--only] \
  [--force]
```

1. Pick an extractor for the new repo's language:
   - **Python:** `--extractor python3 '{kg_dir}/depgraph/extractors/generic/python/extract.py'` — detectors: `fastapi`, `sqlalchemy`, `pydantic`, `pytest`, `service`.
   - **TypeScript/JavaScript:** `--extractor npx tsx '{kg_dir}/depgraph/extractors/generic/typescript/extract.ts'` — detectors: `react`, `vitest`, `route-calls`, `service`.
   - **Go:** `--extractor python3 '{kg_dir}/depgraph/extractors/generic/go/extract.py'` — no shipped detectors; primitives only.
   - **Rust:** `--extractor python3 '{kg_dir}/depgraph/extractors/generic/rust/extract.py'` — no shipped detectors.
2. Repeat `--detector <name>` for each detector you want. Pass `--files-arg=--only` so the post-edit hook can target a single file (note the `=` — argparse can't parse `--files-arg --only` because `--only` starts with `--`).
3. If the project needs framework recognition the shipped detectors don't cover, author a project-local detector at `<data-repo>/depgraph/extractors/detectors/<name>.py` (or `.ts`). Copy the `TEMPLATE_detector.*` from the matching language dir. See `CONTRIBUTING-detectors.md` to upstream it as a PR.
4. Run `kg depgraph regen` and confirm nodes appear under `<data-repo>/depgraph/nodes/`.
5. If logigraph rules will claim against the new repo, also add the `[repos.<key>]` table to `<data-repo>/logigraph/project.toml` so path-classification works for the logigraph hook. (No `kg` shortcut for the logigraph side yet; hand-edit the TOML.)

### When the user asks: "Author a rule / process / domain entity"

1. Read the relevant schema first: `~/tools/knowledge-graph/logigraph/schema/{rule,process,domain}.schema.json`. Each defines required fields and `$defs.warning`.
2. Use the naming convention: `<kind>::<category>::<short_name>` (lowercase, underscores). The filename mirrors the id with `::` → `__`.
3. Required fields by kind:
   - **Rule**: `statement` (one-sentence), `claims_code` (≥1; each pinned via `depgraph_id` + `remote_hash`), `references_domain` (≥1).
   - **Process**: `flow` (object: `action` required; `ui_surface`, `endpoint` optional), `steps` (≥1; each with `claims_code`, optional `transitions: [{to, when}]`).
   - **Domain**: `subkind` (role/resource/attribute/relationship/action), `summary`. Relationships need `from`, `to`, `predicate`, `mediated_by`, `cardinality`, `lifecycle`.
4. Set `definition_status: "llm_drafted"` initially. Compute `structural_hash` as `sha256(<id>).hexdigest()` for new nodes.
5. Author the dossier file in the matching `dossiers/<kind>/` subdir. Rule dossiers MUST contain sections `## The rule`, `## Why it exists`, `## Decision table`. Domain (role subkind) dossiers have their own required sections per `kg logigraph validate`. Process dossiers have no required sections (pointer semantics).
6. Run `kg logigraph validate` — fix any errors before declaring done.
7. Run `kg logigraph regen` — confirm 0 orphans, 0 stale, no new collisions.
8. Tell the user the draft is in the review queue at `http://<host>:8081/graph/review` so they can promote via the UI's bump button.

### When the user asks: "What's pending review?"

1. `http://localhost:8081/graph/review` is the canonical list.
2. CLI alternative: `kg logigraph stats` shows the per-kind `llm_drafted` count.
3. The index page's "Needs attention" card also surfaces `unreviewed_dossier` flags (one per `llm_drafted` node) plus any reconcile-detected drift/orphans.

### When the user asks: "Why is `<flag>` showing on the dashboard?"

1. Flags live in `<data-repo>/logigraph/nodes/_meta.json::flags` — read it directly or via graphui's index page.
2. Each flag has `kind` (defect/drift/gap/review_due/incident), `severity`, `message`, `tracked` boolean, optional `tracking_ref`, and an `affected` list of node ids.
3. **Fresh** (`tracked: false`) = triage. Either resolve in code (delete the source of the drift) or formalize via the warning shape on the affected node (set `tracked: true` + add `tracking_ref`).
4. **Tracked** (`tracked: true`) = acknowledged but live. Don't re-flag; reference the existing `tracking_ref` if proposing to actually fix.
5. Auto-derived warnings (`discovered_by: "reconcile"`) come from `extractors/reconcile.py::build_flags` — codes include `mediation_collision`, `stale_claim`, `orphan_claim`, `orphan_domain_ref`, `unreviewed_dossier`, `stub_dossier`.

### Conventions Claude must follow (framework-level rules)

- **No hardcoded project strings outside `project.toml`.** Path resolution goes through `lib/config` helpers (`path_to_repo_relative`, `project_repos`, `basename_path_map`, `repo_for_basename`, `primary_repo_path`). Never `Path.home() / "<literal-basename>"`. Never `seg.startswith("<literal-prefix>")` as a tracked-repo check.
- **Warnings use the universal shape.** Required fields: `code`, `kind`, `severity`, `message`, `tracked`, `discovered_at`, `discovered_by`. Defined as `$defs.warning` in each schema. New node kinds copy it verbatim.
- **Schemas live with the tool, not with the data.** `~/tools/knowledge-graph/<framework>/schema/`, never `<data-repo>/<framework>/schema/`.
- **Bumping `definition_status` to `human_reviewed` is the *user's* call, not Claude's.** Author drafts; surface them via the review queue; let the human click Promote in graphui.
- **Commit trailers**: every commit in a tracked repo should end with `kg depgraph commit-summary` output. Greppable via `git log --grep="Depgraph:"`.
- **Imports are fully-qualified.** Inside framework code: `from depgraph.lib.X import ...` / `from logigraph.lib.X import ...` (NOT bare `from lib.X`). The `lib` namespace overlap from earlier was retired in favor of explicit package paths.

### Hook environment

`settings.json` carries **one entry per phase** pointing at the `kg` orchestrator. `kg hook <phase>` reads `~/.claude/kg-graphs.toml`, classifies the edited path against each registered graph's source roots, and dispatches to the owning graph's inject/regen handlers. Phases: `pre-edit`, `post-edit`, `pre-irreversible`, `session-start`, `session-end`.

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Edit|Write|MultiEdit",
      "hooks": [{
        "type": "command",
        "command": "/home/<user>/tools/knowledge-graph/bin/kg hook pre-edit",
        "timeout": 10
      }]
    }],
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "/home/<user>/tools/knowledge-graph/bin/kg hook post-edit",
        "timeout": 120
      }]
    }]
  }
}
```

Multi-project setups are handled by the registry, not by duplicating hook entries — `kg project add <data-repo>` registers another graph; the dispatcher fans the event out. Run `kg project list` to see what's registered; run `kg --help` (or `kg <group> --help`) for the authoritative subcommand surface.

### Regen lifecycle

```
source change
   ↓
Stop hook on touched file (or `kg depgraph regen`)
   ↓
mark _meta.regen_status: in_progress
   ↓
extractors emit per-node JSON (deterministic, no LLM)
   ↓
reconcile.py
   ├─ rebuild reverse-edge index (depgraph) / by_code, by_file, by_domain (logigraph)
   ├─ refresh remote_hash on every claim from depgraph corpus; mark stale on drift
   ├─ detect orphans (file deleted) and orphan domain refs (rule references unauthored entity)
   ├─ detect mediation collisions (relationships sharing storage)
   ├─ write _meta.json with regen_status: complete + flags array
   ↓
PreToolUse on Edit
   ↓
hook reads nodes + flags; injects applicable dossier + dependents + warnings
```

If a regen crashes mid-flight, `_meta.regen_status` stays `in_progress` and the next hook surfaces a torn-graph banner. Re-run `kg depgraph regen` (and `kg logigraph regen`) to recover.

### Framework self-tracking (advanced)

The framework can track itself: `~/knowledge-graph-meta/knowledge-graph/` is a data repo (registered as `kg-framework`) whose `project.toml` lists `~/tools/knowledge-graph/{depgraph,logigraph,graphui}` as tracked repos. Authored rules (`rule::config::no_hardcoded_project_strings`, `rule::warnings::use_universal_object_shape`) fire on framework edits, so when extending the framework Claude sees its own invariants. Not required for normal project use; a useful dogfood when contributing to the framework itself.

---

## License

[MIT](./LICENSE). Copyright (c) 2026 Logan Greenlee.

The software is provided **AS IS**, without warranty of any kind, express or implied, including but not limited to merchantability, fitness for a particular purpose, and non-infringement. See the LICENSE file for the full text.
