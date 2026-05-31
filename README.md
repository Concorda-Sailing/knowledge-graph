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

## For humans: install with Claude Code or Grok

Open your AI coding environment (Claude Code or Grok) in any directory and ask it to install.

> **"Install knowledge-graph for this codebase."**

The AI clones the framework to `~/tools/`, scaffolds your project's data dirs, wires hooks (both Claude Code and Grok are supported), starts the graphui daemon, and verifies everything. Idempotent — safe to re-run.

`kg install hooks --for grok` (or `--for both`) writes a native Grok hook file to `~/.grok/hooks/knowledge-graph.json` in addition to (or instead of) the shared `~/.claude/settings.json` block. Grok reads both locations.

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
# Set a default project so bare commands resolve from any cwd:
kg project use <project-name>

# Now these work from anywhere:
kg depgraph regen
kg logigraph health
kg project list-repos
```

`kg install bootstrap` already writes the PATH block to `~/.profile`,
so if you installed via the runbook below you can skip this step. If
you set the framework up manually (clone-only, no `bootstrap`), run
`kg install path --apply` once to add the framework's bin dirs to
`PATH`. If your shell doesn't read `~/.profile`, pass `--rcfile
~/.bashrc` (or your shell's equivalent).

---

## For Claude / Grok: runbook

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
│   │                                 [repos.<key>] path, languages, migrations_dirs,
│   │                                 include_paths, exclude_paths
│   │                                 (see depgraph/README.md for the full key reference;
│   │                                  include_paths/exclude_paths are required for any
│   │                                  repo with tests or generated code)
│   ├── extractors/                   project-local extractors (only if a language the
│   │                                 framework doesn't ship)
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

1. If `~/tools/knowledge-graph/` doesn't exist, clone it from the
   upstream (or your own fork — substitute the org in the URL):
   ```bash
   git clone https://github.com/Concorda-Sailing/knowledge-graph.git ~/tools/knowledge-graph
   ```
2. Resolve the project path. If the user is `cd`'d into the project,
   use `$PWD`. Otherwise ask which project root to wire up. The data
   repo conventionally lives at `<project>-knowledge-graph/` (sibling
   to the source repos), but can live anywhere — `kg project add`
   takes the path. Both layout conventions work:
   - **sibling-with-hyphen** — `~/<project>-knowledge-graph/` (the path
     IS the bundle).
   - **nested** — `~/<project>/` (bundle becomes
     `<project>/knowledge-graph/`).
3. Run the bootstrap:
   ```bash
   ~/tools/knowledge-graph/bin/kg install bootstrap <data-dir>
   ```
   Replace `<data-dir>` with the path from step 2. Bootstrap
   scaffolds `<data-dir>/{depgraph,logigraph}/` and the root
   `project.toml`, writes the hook entries into
   `~/.claude/settings.json`, registers the data repo via `kg project
   add`, and starts the graphui systemd `--user` service.
4. Verify. The `--project` flag goes on each subsystem subcommand
   (`kg depgraph`, `kg logigraph`), not at the top level:
   ```bash
   ~/tools/knowledge-graph/bin/kg project list                            # data repo appears
   ~/tools/knowledge-graph/bin/kg depgraph --project <name> self-check
   ~/tools/knowledge-graph/bin/kg logigraph --project <name> validate
   systemctl --user is-active graphui
   ```
   If only one project is registered, the `--project` flag is
   optional and the command resolves to that project implicitly.
5. Tell the user the graphui URL: `http://localhost:8081/graph/` (or
   LAN IP).

`install.sh bootstrap <data-dir>` is equivalent (it execs `kg install
bootstrap`); use whichever shape the user prefers.

### When the user asks: "Add a new tracked repo"

Two paths exist:

- **Manual TOML edit** (the only path that supports every v2 key).
  Edit `<data-repo>/depgraph/project.toml` and add a `[repos.<key>]`
  table. This is what the steps below describe.
- **`kg project add-repo <key> <path>`** — the native command. Useful
  for the v1-style cases (extractor command + detector + files-arg)
  but does **not** yet accept v2 keys (`languages`,
  `include_paths`, `exclude_paths`, `migrations_dirs`). For v2
  configurations, run it to seed the entry and then edit the TOML to
  fill in the v2 keys.

Manual TOML edit:
The shipped per-language extractors at `depgraph/extractors/{python,
typescript,sql}/` are driven by the per-repo `languages` list — no
per-repo extractor command needed for Python, TypeScript/JavaScript, or
SQL migrations.

1. **Pick a meaningful `<key>`** — it surfaces in every node id
   (`<key>::<rel-path>::<symbol>`) and is the label graphui uses for the
   repo on every page. Short role names for multi-repo (`api`, `web`,
   `mobile`); the project name for single-repo (`acme`, `widgetly`).
   Don't use `app`/`repo`/`main`/`src` — they look like placeholders
   forever.
2. Add the table:
   ```toml
   [repos.<key>]
   path = "~/<project>-<key>"
   languages = ["python"]          # subset of {python, typescript, sql}; inferred if omitted
   migrations_dirs = ["migrations"] # required when languages includes "sql"
   exclude_paths = [                # scope what's tracked; the framework only skips a handful of build dirs
     "**/tests/**", "**/__tests__/**", "**/build/**",
   ]
   ```
   See `depgraph/README.md` for the full per-repo key reference, and the
   v2 classification rules under `depgraph/lib/classification/` for how
   `kind` is assigned (`component`, `hook`, `endpoint`, `service`,
   `model`, `schema`, `test`, `util`).
3. **Scope the repo with `include_paths` / `exclude_paths`.** Required
   for almost every real repo — without it, test trees, generated code,
   and vendored deps end up in the corpus and produce orphan edges.
4. Run `kg depgraph regen` and confirm nodes appear under
   `<data-repo>/depgraph/nodes/<kind>/`.
5. If logigraph rules will claim against the new repo, also add the
   `[repos.<key>]` table to `<data-repo>/logigraph/project.toml` so
   path-classification works for the logigraph hook. (No `kg` shortcut
   for the logigraph side yet; hand-edit the TOML.)

For a language the framework doesn't ship, the v1 subprocess fallback
in `lib/cli/regen.py::_mode_a_v1_fallback` still honors per-repo
`extractor = ["cmd", "args", ...]` configs. New repos should prefer the
shipped per-language extractors.

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
