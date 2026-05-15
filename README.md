# knowledge-graph

A small, project-agnostic substrate that gives an AI coding collaborator working memory about a codebase. Three pieces:

| Tool | What it does |
|---|---|
| **depgraph** | Code-structure nodes (models, services, endpoints, components, hooks, tests) + reverse-dependency index. Hooks into Claude Code's PreToolUse to inject dependents before every edit. |
| **logigraph** | Authored business rules, domain entities, and process flows. Hooks inject applicable rule prose + flow context on edit. Mediation-collision detection flags design defects. |
| **graphui** | FastAPI + Jinja2 dark-themed viewer for both graphs. Coverage gallery, repo-and-kind navigation, mobile-friendly cards, Needs-attention card, review queue with promote-from-draft. |
| **kg** | Orchestrator. Reads `~/.claude/kg-graphs.toml`, fans Claude Code hook events to whichever registered graph owns the file being edited. One settings.json entry per phase replaces the per-project hand-wired hooks. |

All four ship from this one repo. Framework code lives in `~/tools/knowledge-graph/{depgraph,logigraph,graphui,kg}/`. Per-project data lives in `<project>-knowledge-graph/{depgraph,logigraph}/` — nodes, dossiers, extractors, telemetry, plus a root `project.toml` declaring the project and subsystems.

---

## For humans: install with Claude Code

Open Claude Code in any directory and ask. Claude reads this README and runs the steps.

> **"Install knowledge-graph for this codebase."**

Claude clones the framework to `~/tools/`, scaffolds your project's data dirs, wires the Claude Code hooks, starts the graphui daemon, and verifies all three. Idempotent — safe to re-run.

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

Optional ergonomics:

```bash
echo 'export PATH="$HOME/tools/knowledge-graph/depgraph/bin:$HOME/tools/knowledge-graph/logigraph/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
# now `depgraph regen` / `logigraph validate` work from any cwd
```

---

## For Claude: runbook

This section is the source of truth for what to do when a user asks for knowledge-graph operations. Read carefully before acting.

### Core layout (mental model)

```
~/tools/knowledge-graph/              (framework — clone once, shared across projects)
├── bin/kg                            ← orchestrator CLI (list/add/remove/hook)
├── kg/                               ← orchestrator package
├── depgraph/      bin/, hooks/, extractors/reconcile.py, lib/config.py, schema/
├── logigraph/     bin/, hooks/, extractors/reconcile.py, lib/config.py, schema/
├── graphui/       app/, .venv/       (FastAPI viewer)
├── install.sh                        ← installer + project scaffolder
└── README.md                         ← this file

<project>-knowledge-graph/            (per-project data — one repo per project)
├── project.toml                      [project] name; subsystems = ["depgraph", "logigraph"]
├── depgraph/
│   ├── project.toml                  [project] primary_repo; [logigraph] data_dir;
│   │                                 [repos.<key>] path, extractor, files_arg
│   ├── extractors/                   project-specific extractors (extract_api.py, …)
│   ├── nodes/                        produced by `bin/depgraph regen`
│   ├── dossiers/                     human-authored prose per node
│   └── telemetry/                    injections.jsonl, acknowledgments.jsonl
└── logigraph/
    ├── project.toml                  same shape; plus [depgraph] data_dir cross-ref
    ├── nodes/{rules,domain,processes}/
    ├── dossiers/{rules,domain,processes}/
    └── telemetry/

~/.claude/kg-graphs.toml              ← registry of installed graphs (kg add/remove edits this)
```

### When the user asks: "Install knowledge-graph"

1. If `~/tools/knowledge-graph/` doesn't exist, clone it:
   ```bash
   git clone https://github.com/Concorda-Sailing/knowledge-graph.git ~/tools/knowledge-graph
   ```
2. Resolve the project path. If the user is `cd`'d into the project, use `$PWD`. Otherwise ask which project root to wire up. The data repo conventionally lives at `<project>-knowledge-graph/` (sibling to the source repos), but can live anywhere — `kg add` takes the path.
3. Run the bootstrap:
   ```bash
   ~/tools/knowledge-graph/install.sh bootstrap <data-repo-path>
   ```
   This scaffolds `<data-repo-path>/{depgraph,logigraph}/` and root `project.toml`, writes the `kg`-orchestrated hook entries into `~/.claude/settings.json`, registers the data repo via `kg add <data-repo-path>`, and starts the graphui systemd `--user` service.
4. Verify:
   ```bash
   ~/tools/knowledge-graph/bin/kg list                          # data repo appears
   DEPGRAPH_DATA_DIR=<data-repo-path>/depgraph ~/tools/knowledge-graph/depgraph/bin/depgraph self-check
   LOGIGRAPH_DATA_DIR=<data-repo-path>/logigraph DEPGRAPH_DATA_DIR=<data-repo-path>/depgraph ~/tools/knowledge-graph/logigraph/bin/logigraph validate
   systemctl --user is-active graphui
   ```
5. Tell the user the graphui URL: `http://localhost:8081/graph/` (or LAN IP).

### When the user asks: "Add a new tracked repo"

1. Read the current `<data-repo>/depgraph/project.toml`.
2. Add a new `[repos.<key>]` table. Use a framework language extractor:
   - **Python:** `extractor = ["python3", "{kg_dir}/depgraph/extractors/generic/python/extract.py"]`. Available detectors: `fastapi`, `sqlalchemy`, `pydantic`, `pytest`, `service`.
   - **TypeScript/JavaScript:** `extractor = ["npx", "tsx", "{kg_dir}/depgraph/extractors/generic/typescript/extract.ts"]`. Available detectors: `react`, `vitest`, `route-calls`, `service`.
   - **Go:** `extractor = ["python3", "{kg_dir}/depgraph/extractors/generic/go/extract.py"]`. No shipped detectors; primitives only.
   - **Rust:** `extractor = ["python3", "{kg_dir}/depgraph/extractors/generic/rust/extract.py"]`. No shipped detectors.
   List the wanted detectors via `detectors = [...]`. Set `files_arg = "--only"` so the post-edit hook can target a single file.
3. If the project needs framework recognition the shipped detectors don't cover, author a project-local detector at `<data-repo>/depgraph/extractors/detectors/<name>.py` (or `.ts`). Copy the `TEMPLATE_detector.*` from the matching language dir. See `CONTRIBUTING-detectors.md` to upstream it as a PR.
4. Run `bin/depgraph regen` and confirm nodes appear under `<data-repo>/depgraph/nodes/`.
5. If logigraph rules will claim against the new repo, also add the `[repos.<key>]` table to `<data-repo>/logigraph/project.toml` so path-classification works for the logigraph hook.

### When the user asks: "Author a rule / process / domain entity"

1. Read the relevant schema first: `~/tools/knowledge-graph/logigraph/schema/{rule,process,domain}.schema.json`. Each defines required fields and `$defs.warning`.
2. Use the naming convention: `<kind>::<category>::<short_name>` (lowercase, underscores). The filename mirrors the id with `::` → `__`.
3. Required fields by kind:
   - **Rule**: `statement` (one-sentence), `claims_code` (≥1; each pinned via `depgraph_id` + `remote_hash`), `references_domain` (≥1).
   - **Process**: `flow` (object: `action` required; `ui_surface`, `endpoint` optional), `steps` (≥1; each with `claims_code`, optional `transitions: [{to, when}]`).
   - **Domain**: `subkind` (role/resource/attribute/relationship/action), `summary`. Relationships need `from`, `to`, `predicate`, `mediated_by`, `cardinality`, `lifecycle`.
4. Set `definition_status: "llm_drafted"` initially. Compute `structural_hash` as `sha256(<id>).hexdigest()` for new nodes.
5. Author the dossier file in the matching `dossiers/<kind>/` subdir. Rule dossiers MUST contain sections `## The rule`, `## Why it exists`, `## Decision table`. Domain (role subkind) dossiers have their own required sections per `bin/logigraph validate`. Process dossiers have no required sections (pointer semantics).
6. Run `bin/logigraph validate` — fix any errors before declaring done.
7. Run `bin/logigraph regen` — confirm 0 orphans, 0 stale, no new collisions.
8. Tell the user the draft is in the review queue at `http://<host>:8081/graph/review` so they can promote via the UI's bump button.

### When the user asks: "What's pending review?"

1. `http://localhost:8081/graph/review` is the canonical list.
2. CLI alternative: `bin/logigraph stats` shows the per-kind `llm_drafted` count.
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
- **Commit trailers**: every commit in a tracked repo should end with `bin/depgraph commit-summary` output. Greppable via `git log --grep="Depgraph:"`.

### Hook environment

`settings.json` carries **one entry per phase** pointing at the `kg` orchestrator. `kg` reads `~/.claude/kg-graphs.toml`, classifies the edited path against each registered graph's source roots, and dispatches to the owning graph's inject/regen scripts. Phases: `pre-edit`, `post-edit`, `pre-irreversible`, `session-start`, `session-end`.

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

Multi-project setups are handled by the registry, not by duplicating hook entries — `kg add <data-repo>` registers another graph; the dispatcher fans the event out. Run `kg list` to see what's registered; run `kg --help` for the authoritative subcommand surface.

### Regen lifecycle

```
source change
   ↓
Stop hook on touched file (or `bin/depgraph regen`)
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

If a regen crashes mid-flight, `_meta.regen_status` stays `in_progress` and the next hook surfaces a torn-graph banner. Re-run `bin/depgraph regen` (and `bin/logigraph regen`) to recover.

### Framework self-tracking (advanced)

The framework can track itself: `~/knowledge-graph-meta/knowledge-graph/` is a data repo (registered as `kg-framework`) whose `project.toml` lists `~/tools/knowledge-graph/{depgraph,logigraph,graphui}` as tracked repos. Authored rules (`rule::config::no_hardcoded_project_strings`, `rule::warnings::use_universal_object_shape`) fire on framework edits, so when extending the framework Claude sees its own invariants. Not required for normal project use; a useful dogfood when contributing to the framework itself.

## License

[MIT](./LICENSE). Copyright (c) 2026 Logan Greenlee.

The software is provided **AS IS**, without warranty of any kind, express or implied, including but not limited to merchantability, fitness for a particular purpose, and non-infringement. See the LICENSE file for the full text.
