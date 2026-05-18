# Logigraph plugin architecture

Status: **proposed** (Phase 0 not yet started)
Author: agent + maintainer review
Date: 2026-05-18

Sibling plan to the depgraph plugin work that landed in commits
`b0192ac` and `714f88a`. Where depgraph's plugins solved
"what counts as a route / hook / model in this codebase," this plan
addresses logigraph's parallel question: "what counts as a flow
entrypoint, a state-mutating sink, a UI entry-path convention in this
codebase?" Today logigraph hardcodes the web-API answer to that
question in 14+ sites across `logigraph/lib/cli/process.py` and the
schema enums. A repo whose code shape isn't web-API (CLI tool, data
pipeline, event-driven service, ML system) gets silent classification
degradation, not an error.

This plan also course-corrects the architecture: shared plugin
infrastructure should live in `kg/shared/plugins/`, not in
`depgraph/plugins/` where logigraph would have to reach across into a
sibling subsystem's namespace to use it. `kg/shared/` is the
established home for cross-graph helpers (git, telemetry); plugin
infrastructure belongs there too.

---

## Background

### What's wrong today

Two related problems.

**Problem 1 — framework assumptions baked into logigraph.** A
post-depgraph-plugins audit of `logigraph/` surfaced five structural
gaps:

1. **`kind == "endpoint"` / `kind == "model"` hardcoding.** `process.py`
   branches on these strings at 14 sites (8 endpoint, 6 model) to
   decide what initiates a flow and what represents state-mutation
   convergence. Assumes web-API shape.

2. **REST HTTP-method semantics.** `process.py:241` filters out
   `GET::` endpoints because they're "reads, not state mutation." This
   builds in REST's verb-semantics distinction. Breaks for GraphQL,
   gRPC, event-sourced systems where reads can trigger side effects.

3. **UI-entry path conventions.** `process.py:313, 322, 376–380`
   hardcodes Next.js (`/page.tsx`), React hooks (`src/hooks/`), and
   API-client conventions (`lib/api.ts`, `lib/client.ts`). Won't
   detect Vue, Svelte, Remix, Astro, or any non-JS UI framework.

4. **Process-rank signals.** `process.py:112–441` ships seven
   flow-detection heuristics that all assume the web-API topology
   (entrypoint_fan_in, endpoint_forward_reach, convergence_on_model,
   page_initiated_flow, etc.). A CLI corpus or event-driven corpus
   would emit zero candidates from every signal.

5. **Schema-level enums.** `domain.schema.json` enums for `subkind` /
   `origin` assume a business-logic domain model.
   `process.schema.json` enums for claim `role` / surface `role`
   assume guard-clause / render / post-effect code organization. ML
   systems, infrastructure-as-code, reactive frameworks don't fit.

Plus nine minor hardcodings (`KIND_WEIGHT` heuristic weights,
definition-status enum, confidence enum, etc.) that are real but small.

**Problem 2 — wrong namespace for the plugin solution.** A naive port
of depgraph's plugin pattern to logigraph would have logigraph
plugins import `Plugin` from `depgraph.plugins.base`. That makes
logigraph reach across into a sibling subsystem's namespace for shared
infrastructure — a layering compromise that compounds the one we
already accept (`logigraph/extractors/reconcile.py` imports `chunker`
/ `embeddings` / `rollup` from `depgraph.lib`).

The right home for shared plugin infrastructure is `kg/shared/`. Its
own docstring (`kg/shared/__init__.py`) describes the convention:

> "Cross-graph shared helpers used by both depgraph and logigraph
> CLIs. Lives outside both lib/cli/ packages to avoid the
> namespace-overlap pitfall…"

Git helpers and telemetry helpers already live there. Plugin
infrastructure belongs there too.

### Why solve both at once

Phase 0 (the namespace refactor) blocks Phase 1 (the logigraph
plugins). If we build Phase 1 without Phase 0, every logigraph plugin
imports from `depgraph.plugins.*`, and undoing that later requires
touching every plugin module twice. Phase 0 is small (~1.5h of
mechanical edits, no behavior change) and unblocks the rest.

---

## Architecture (target)

```
kg/shared/plugins/
    __init__.py             Plugin dataclass, _discover_plugins,
                            _load_local_plugins, build_config_generic
    detectors.py            has_npm_dep, has_pypi_dep, has_marker_file

depgraph/plugins/
    __init__.py             depgraph wrapper: imports kg.shared.plugins,
                            wires LanguageCues merger + copier,
                            exports build_config / build_config_for_repos
                            that return a ClassificationConfig
    (base.py DELETED — Plugin + detectors come from kg.shared.plugins)
    general/  react/  vitest/  fastapi/  express/  prisma/  sqlalchemy/
    pytest_plugin/
                            each plugin module:
                                from kg.shared.plugins import Plugin
                                from depgraph.lib.classification.config
                                    import LanguageCues

logigraph/plugins/          (Phase 1)
    __init__.py             logigraph wrapper: imports kg.shared.plugins,
                            wires LogigraphCues merger + copier,
                            exports build_config / build_config_for_repos
                            returning logigraph's per-repo cue set
    base.py                 LogigraphCues dataclass (this lives here, not
                            in kg.shared, because it's logigraph-specific)
    general/  web_api/  nextjs/  nuxt/  cli/  data_pipeline/
    event_driven/
                            each plugin module:
                                from kg.shared.plugins import Plugin
                                from logigraph.plugins.base
                                    import LogigraphCues
```

### Generic core (Phase 0 destination)

`kg.shared.plugins` exposes:

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

@dataclass
class Plugin:
    name: str
    detect: Callable[[Path], bool]
    cues: dict[str, Any] = field(default_factory=dict)
    # cues is opaque to this layer — subsystems own the type
    # (LanguageCues for depgraph, LogigraphCues for logigraph)

def _discover_plugins(plugins_pkg, *, local_plugin_paths=None) -> list[Plugin]:
    ...

def build_config_generic(
    repo_path: Path,
    plugins_pkg,                                    # e.g. depgraph.plugins
    cue_merger: Callable[[Any, Any], Any],          # subsystem-provided
    cue_copier: Callable[[Any], Any],               # subsystem-provided
    *,
    enable: list[str] | None = None,
    disable: list[str] | None = None,
    auto: bool = True,
    local_plugin_paths: list[Path] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Returns (cues_by_language, active_plugin_names). The caller
    wraps this and builds its own typed config object (e.g.
    ClassificationConfig for depgraph)."""
```

### Subsystem wrappers

Depgraph's wrapper (after Phase 0):

```python
# depgraph/plugins/__init__.py
from kg.shared.plugins import Plugin, build_config_generic
from depgraph.lib.classification.config import (
    ClassificationConfig, LanguageCues,
)

def _merge_language_cues(a: LanguageCues, b: LanguageCues) -> LanguageCues: ...
def _copy_language_cues(a: LanguageCues) -> LanguageCues: ...

def build_config(repo_path, **kwargs):
    cues_by_lang, active = build_config_generic(
        repo_path,
        plugins_pkg="depgraph.plugins",
        cue_merger=_merge_language_cues,
        cue_copier=_copy_language_cues,
        **kwargs,
    )
    return ClassificationConfig(languages=cues_by_lang), active
```

Logigraph's wrapper (Phase 1):

```python
# logigraph/plugins/__init__.py
from kg.shared.plugins import Plugin, build_config_generic
from logigraph.plugins.base import LogigraphCues

def _merge_logigraph_cues(a: LogigraphCues, b: LogigraphCues) -> LogigraphCues: ...
def _copy_logigraph_cues(a: LogigraphCues) -> LogigraphCues: ...

def build_config(repo_path, **kwargs):
    cues_by_kind, active = build_config_generic(
        repo_path,
        plugins_pkg="logigraph.plugins",
        cue_merger=_merge_logigraph_cues,
        cue_copier=_copy_logigraph_cues,
        **kwargs,
    )
    return cues_by_kind, active
```

### What's still subsystem-local

- The `Cues` dataclass (LanguageCues, LogigraphCues) — typed for each
  subsystem's needs.
- The merge function — knows the cue type's fields.
- The copy function — defensive copying for mutation safety.
- The per-subsystem `default_config()` convenience helper for tests.

### What moves to `kg/shared/`

- The `Plugin` dataclass — generic over cue type.
- Discovery (walking a package, finding `PLUGIN` instances).
- Local-plugin loading (importing arbitrary `.py` files).
- The activation pipeline (auto/enable/disable resolution).
- Detection helpers (`has_npm_dep`, `has_pypi_dep`, `has_marker_file`)
  — purely manifest-reading, no subsystem coupling.

---

## Priority + phasing

| Phase | Scope | Status | Trigger to build |
|---|---|---|---|
| **0** | Refactor depgraph plugins into `kg/shared/plugins/`. No behavior change. | **Build now** — blocks Phase 1 | Direct user direction |
| **1** | Logigraph cue plugins on shared infra. Migrate hardcoded `kind` / HTTP-method / path checks in `process.py`. | **Build after Phase 0** | Same — addresses the silent-degradation risk |
| 2 | Signal plugins — per-domain `process-rank` heuristics | **Deferred** | A non-web-API corpus emits zero candidates from existing signals AND we can name the signals we'd want |
| 3 | Schema extension — per-project enum overrides | **Deferred** | A real project hits a hard wall with an existing enum |
| 4 | Validator plugins — per-kind dossier requirements | **Deferred** | Bundles with Phase 3 — both touch dossier shape |

Phases 2–4 are scoped here for completeness; **don't build them
speculatively**. The depgraph rewrite plan's lesson (preserved in the
project-agnosticism work this session) is that designing for
hypothetical use cases adds complexity and gets scrubbed later. Build
them when concrete corpora drive the requirements.

---

## Phase 0 — Lift plugin infrastructure to `kg/shared/plugins/`

**Goal:** Move the generic parts of depgraph's plugin code into
`kg/shared/plugins/`. Subsystem-specific parts (cue types, mergers,
copiers) stay in `depgraph/plugins/`. No behavior change. Existing
tests pass unchanged. A configured project's regen produces byte-identical output.

### Moves

| From | To |
|---|---|
| `depgraph/plugins/base.py::Plugin` | `kg/shared/plugins/__init__.py` |
| `depgraph/plugins/base.py::has_npm_dep` | `kg/shared/plugins/detectors.py` |
| `depgraph/plugins/base.py::has_pypi_dep` | `kg/shared/plugins/detectors.py` |
| `depgraph/plugins/base.py::has_marker_file` | `kg/shared/plugins/detectors.py` |
| `depgraph/plugins/__init__.py::_discover_shipped_plugins` | `kg/shared/plugins/__init__.py` (parameterized — takes a package object) |
| `depgraph/plugins/__init__.py::_load_local_plugins` | `kg/shared/plugins/__init__.py` (already generic) |
| `depgraph/plugins/__init__.py::_discover_plugins` | `kg/shared/plugins/__init__.py` |
| `depgraph/plugins/__init__.py::build_config` (generic core) | `kg/shared/plugins/__init__.py` as `build_config_generic` |
| `depgraph/plugins/__init__.py::_merge_cues` | Stays in `depgraph/plugins/__init__.py` (typed for LanguageCues) |

### Touch list

1. **Create** `kg/shared/plugins/__init__.py` with the generic `Plugin`,
   discovery, loading, and `build_config_generic`.
2. **Create** `kg/shared/plugins/detectors.py` with the three detection
   helpers.
3. **Delete** `depgraph/plugins/base.py` (its contents moved).
4. **Rewrite** `depgraph/plugins/__init__.py` as a wrapper: imports
   from `kg.shared.plugins`, defines `_merge_language_cues` and
   `_copy_language_cues`, exports `build_config` / `build_config_for_repos`
   returning a `ClassificationConfig`.
5. **Update** the 9 shipped plugin modules — each currently does
   `from depgraph.plugins.base import Plugin, has_npm_dep, ...`; switch
   to `from kg.shared.plugins import Plugin` and
   `from kg.shared.plugins.detectors import has_npm_dep, ...`.
6. **Update** `depgraph/lib/classification/config.py::default_config()` —
   currently `from depgraph.plugins import _discover_plugins, _merge_cues`;
   becomes `from kg.shared.plugins import _discover_plugins` plus
   `from depgraph.plugins import _merge_language_cues, _copy_language_cues`.
7. **Run** `pytest depgraph/tests -q` — must pass unchanged.
8. **Regen** the configured project's depgraph corpus — output must be
   byte-identical to pre-refactor.

### Done definition (Phase 0)

- [ ] `kg/shared/plugins/__init__.py` and `kg/shared/plugins/detectors.py` exist.
- [ ] `depgraph/plugins/base.py` is deleted.
- [ ] All 9 shipped plugins import from `kg.shared.plugins`.
- [ ] No occurrences of `from depgraph.plugins.base` anywhere in the tree.
- [ ] `pytest depgraph/tests -q` passes (352 + 4 skipped, same as before).
- [ ] A configured project's regen produces a byte-identical corpus
      directory compared to a pre-refactor regen (determinism gate
      enforces this; manual diff confirms).
- [ ] Commit message: `kg/shared/plugins: lift generic plugin infrastructure out of depgraph/`

### Estimated effort

1.5 hours of focused work. Pure refactoring: no algorithmic changes,
just file moves and import updates.

### Risk

Low. The change is mechanical; the only failure mode is missing an
import. The test suite catches that. If anything goes wrong, the
revert is one `git revert` away.

---

## Phase 1 — Logigraph cue plugins on shared infrastructure

**Goal:** Make logigraph's "what counts as a flow entrypoint / sink /
UI entry" decisions configurable per project. Eliminate the silent-
degradation risk where a non-web-API corpus produces zero
`kind=endpoint` / `kind=model` nodes and process-rank emits zero
candidates.

### Files to create

```
logigraph/plugins/
    __init__.py             Wrapper over kg.shared.plugins —
                            imports build_config_generic,
                            wires LogigraphCues merger + copier
    base.py                 LogigraphCues dataclass
    general/
        __init__.py
        flow.py             Always-active baseline (no framework
                            assumptions — empty cue set, just present
                            so general:* parallels depgraph)
    web_api/
        __init__.py
        plugin.py           kind=endpoint as entry, kind=model as sink;
                            REST HTTP-method semantics
    nextjs/
        __init__.py
        plugin.py           Next.js path conventions: app/**/page.tsx,
                            pages/**/*.tsx, src/hooks/**,
                            lib/api.ts / lib/client.ts
    nuxt/
        __init__.py
        plugin.py           Nuxt path conventions: pages/**/*.vue,
                            composables/**
    cli/
        __init__.py
        plugin.py           kind=command (when extractor emits it) or
                            kind=function in bin/* / __main__ as entry
    data_pipeline/
        __init__.py
        plugin.py           Source / sink decorators (configurable);
                            common patterns from prefect/dagster/airflow
    event_driven/
        __init__.py
        plugin.py           Queue/topic subscriber decorators
                            (configurable patterns)

logigraph/plugins/README.md      Architecture + cue reference +
                                 worked example
logigraph/plugins/AGENTS.md      Open-source-only rule for upstream
                                 PRs; mirrors depgraph/plugins/AGENTS.md
```

### Files to modify

- `logigraph/lib/cli/process.py` — replace hardcoded `kind == "endpoint"`
  (8 sites) and `kind == "model"` (6 sites) with `cues.entrypoint_kinds`
  / `cues.sink_kinds` membership checks. Replace `GET::` filter
  (`process.py:241`) with `cues.mutation_methods` set membership.
  Replace path-hint regexes (`process.py:313, 322, 376–380`) with
  `cues.ui_entry_path_globs` / `cues.api_client_path_globs` glob matches.
- `logigraph/extractors/reconcile.py` — load logigraph plugins for the
  project, thread cues into process-rank.
- `logigraph/schema/` — **no schema changes in Phase 1** (the enums
  stay; Phase 3 handles extensions).

### `LogigraphCues` shape

```python
# logigraph/plugins/base.py
from dataclasses import dataclass, field

@dataclass
class LogigraphCues:
    """Per-framework cues for flow detection."""

    entrypoint_kinds: set[str] = field(default_factory=set)
    """Depgraph kinds whose nodes initiate a flow.
       web-api:        {"endpoint"}
       cli:            {"command"}    (when extractor emits "command")
       event-driven:   {"handler"}    (custom kind, plugin-introduced)"""

    sink_kinds: set[str] = field(default_factory=set)
    """Depgraph kinds whose nodes represent state-mutation convergence.
       web-api:        {"model"}
       cli:            {"util"}       (CLIs converge on shared utils)
       event-driven:   {"publisher"}  (custom kind)"""

    mutation_methods: set[str] = field(default_factory=set)
    """HTTP / RPC methods that imply state mutation.
       Empty set means no method filter applies (every endpoint qualifies).
       Examples: {"POST", "PUT", "DELETE", "PATCH"}"""

    ui_entry_path_globs: set[str] = field(default_factory=set)
    """Gitignore-style globs for files that are UI entry points.
       Nextjs:  {"app/**/page.tsx", "pages/**/*.tsx"}
       Nuxt:    {"pages/**/*.vue"}"""

    api_client_path_globs: set[str] = field(default_factory=set)
    """Gitignore-style globs for API-client / wrapper files.
       Nextjs:  {"lib/api.ts", "lib/client.ts", "src/lib/api.ts"}"""

    test_path_globs: set[str] = field(default_factory=set)
    """Globs marking a file as a test (excluded from flow heuristics).
       Most projects:  {"**/*.test.ts", "**/test_*.py", "**/tests/**"}"""
```

### Worked migration of one hardcoded site

**`process.py:63` before:**

```python
if node["kind"] != "endpoint":
    continue
```

**After:**

```python
if node["kind"] not in cues.entrypoint_kinds:
    continue
```

**`process.py:241` before:**

```python
if endpoint_id.startswith("GET::"):
    continue  # GET endpoints are reads, not state mutation
```

**After:**

```python
# When mutation_methods is configured, filter to mutating verbs only.
# Empty set means "every flow-initiator counts" (e.g., CLI commands,
# event handlers).
if cues.mutation_methods:
    method = endpoint_id.split("::", 1)[0]
    if method not in cues.mutation_methods:
        continue
```

**`process.py:313` before:**

```python
is_ui_entry = "/page." in path or path.endswith("/page.tsx")
```

**After:**

```python
from pathspec import PathSpec
ui_spec = PathSpec.from_lines("gitwildmatch", cues.ui_entry_path_globs)
is_ui_entry = ui_spec.match_file(path)
```

*(Use a pathspec helper — the project may already have one from
`depgraph/lib/path_filters.py`. Check before pulling in a dependency.)*

### Plugin examples

```python
# logigraph/plugins/web_api/plugin.py
from kg.shared.plugins import Plugin
from kg.shared.plugins.detectors import has_npm_dep, has_pypi_dep
from logigraph.plugins.base import LogigraphCues

PLUGIN = Plugin(
    name="web-api",
    detect=lambda repo_path: (
        has_npm_dep(repo_path, "express")
        or has_npm_dep(repo_path, "@nestjs/core")
        or has_npm_dep(repo_path, "fastify")
        or has_npm_dep(repo_path, "@hapi/hapi")
        or has_pypi_dep(repo_path, "fastapi")
        or has_pypi_dep(repo_path, "django")
        or has_pypi_dep(repo_path, "flask")
        or has_pypi_dep(repo_path, "starlette")
    ),
    cues={"logigraph": LogigraphCues(
        entrypoint_kinds={"endpoint"},
        sink_kinds={"model"},
        mutation_methods={"POST", "PUT", "DELETE", "PATCH"},
    )},
)
```

```python
# logigraph/plugins/nextjs/plugin.py
PLUGIN = Plugin(
    name="nextjs",
    detect=lambda repo_path: has_npm_dep(repo_path, "next"),
    cues={"logigraph": LogigraphCues(
        ui_entry_path_globs={
            "app/**/page.tsx", "app/**/page.jsx",
            "pages/**/*.tsx", "pages/**/*.jsx",
        },
        api_client_path_globs={
            "lib/api.ts", "lib/client.ts",
            "src/lib/api.ts", "src/lib/client.ts",
        },
    )},
)
```

```python
# logigraph/plugins/cli/plugin.py
PLUGIN = Plugin(
    name="cli",
    detect=lambda repo_path: (
        bool(list(repo_path.glob("bin/*")))
        or bool(list(repo_path.glob("**/__main__.py")))
        or bool(list(repo_path.glob("**/cli.py")))
    ),
    cues={"logigraph": LogigraphCues(
        entrypoint_kinds={"command"},   # depgraph CLI extractor would emit this
        sink_kinds={"util"},
        # No mutation_methods — CLI tools take argv, not HTTP verbs.
    )},
)
```

### Tests

Create `logigraph/tests/test_plugin_registry.py` mirroring
`depgraph/tests/test_plugin_registry.py`:

- Discovery — confirms `general:logigraph` always-on baseline is
  found, plus all shipped framework plugins.
- Detection — for each plugin, create a `tmp_path` with the relevant
  manifest, assert the plugin activates.
- Cue contribution — assert specific cues appear in the merged config.
- Override semantics — local plugin with same `name` replaces shipped.
- Bad local plugin — broken `.py` file reports on stderr but doesn't
  abort.
- Auto / enable / disable — same matrix as depgraph.

Create `logigraph/tests/test_process_rank_pluggable.py`:

- **Regression gate**: an existing web-API-shaped corpus with the
  `web-api` plugin active produces the same process-rank output as
  before the migration. (Captures the current behavior so we don't
  break it.)
- **Bug closure**: a synthetic CLI-shaped corpus (no `kind=endpoint`
  nodes, but `kind=command` nodes) with the `cli` plugin active
  produces non-zero process-rank output targeting the `kind=command`
  nodes. (Demonstrates the bug is fixed.)
- **Silent-degradation reproduction**: the same CLI corpus *without*
  the `cli` plugin active (or with no plugins active) produces zero
  candidates — this is the current behavior, and the test pins it
  with an explicit assertion so future regressions are caught.

### Commits (Phase 1)

Three logical commits:

1. `logigraph/plugins: registry skeleton + LogigraphCues protocol` —
   adds `logigraph/plugins/{__init__.py, base.py}`,
   `logigraph/plugins/general/`. No call sites changed yet; registry
   tests pass.
2. `logigraph/lib/cli/process: migrate kind/HTTP-method/path hardcoding to cue lookups` —
   swaps the 14 hardcoded sites. Adds the `web-api`, `cli`,
   `data_pipeline`, `event_driven`, `nextjs`, `nuxt` plugins. The new
   `test_process_rank_pluggable.py` lands here.
3. `logigraph/plugins: README + AGENTS docs` — parallels depgraph's
   docs. The open-source-only rule is repeated verbatim (frameworks
   are frameworks; legal scope doesn't change between subsystems).

### Done definition (Phase 1)

- [ ] `pytest logigraph/tests -q` green (existing tests + new
      `test_plugin_registry.py` + `test_process_rank_pluggable.py`).
- [ ] `pytest depgraph/tests -q` green (unaffected, but confirm).
- [ ] An existing web-API-shaped corpus regenerates with the same
      process-rank output as before the migration (regression gate).
- [ ] A synthetic CLI-shaped corpus regenerates with non-zero
      process-rank output when the `cli` plugin is active.
- [ ] `logigraph/plugins/{README,AGENTS}.md` ship the same legal scope
      rule depgraph's docs do, plus the worked example for adding a
      new logigraph plugin.

### Estimated effort

3–5 hours of focused work. The registry code is a near-copy of
depgraph's (refactored to use `kg.shared.plugins`). The migration is
mechanical (`grep -rn "kind ==" logigraph/lib/cli/process.py` lists
every site). Test authoring is the biggest single chunk.

### Risks (Phase 1)

| Risk | Mitigation |
|---|---|
| Migration breaks existing web-API corpora | The `web-api` plugin auto-activates whenever a web framework is in deps. Existing behavior preserved. |
| `pathspec` adds a dependency the project doesn't have | Check `depgraph/lib/path_filters.py` first — if it has a usable glob matcher, reuse. Worst case, vendor a small glob matcher inline. |
| `cli` plugin's `entrypoint_kinds={"command"}` references a kind the depgraph extractor doesn't emit today | Document the dependency. A CLI corpus would need either (a) a depgraph plugin that classifies command handlers as `kind=command`, or (b) a logigraph plugin that uses path globs to identify entry points without relying on `kind`. Phase 1 supports both. |
| Cross-plugin contradictions (web-api says mutation_methods has 4 verbs, GraphQL plugin says it has 0) | Union semantics: cues union, behavior is the most-permissive intersection. If two plugins genuinely conflict, the project author resolves via `[classification.plugins] disable`. |

---

## Phase 2 — Signal plugins (deferred)

**When to build:** when a non-web-API corpus produces zero candidates
from the existing seven `process-rank` signals AND we can name the
signals we'd want for that corpus.

### Sketch

```python
# kg/shared/signals.py (new)
@dataclass
class Signal:
    name: str
    cues_required: set[str]
        # e.g. {"entrypoint_kinds", "ui_entry_path_globs"}
    compute: Callable[[Corpus, Cues], dict[NodeId, float]]
```

Refactor each of `process.py`'s 7 hardcoded signals into a `Signal`
instance under `logigraph/signals/`. Each signal lives in its own
module. Logigraph plugins from Phase 1 can register additional
signals.

Process-rank runs every active signal whose `cues_required` are
satisfied by the active cue set; results are summed (or weighted —
TBD).

### Why defer

Designing the signal-registry interface without a concrete second-
domain corpus is over-fitting. The seven existing signals are tuned
for web APIs; we don't know what tuning a CLI corpus needs until we
have one. Build the signal-plugin layer when we hit it.

---

## Phase 3 — Schema extension (deferred)

**When to build:** when a real project hits a hard wall with the
existing schema enums (e.g., an ML team needs `subkind="dataset"` in
a domain dossier and can't make do with `"resource"`).

### Sketch

```toml
# project.toml
[logigraph.schema.extensions]
"domain.subkind" = ["dataset", "model", "pipeline", "metric"]
"process.claim.role" = ["aggregates", "deduplicates"]
```

- Extensions are **additive** — they union with built-in enums.
- `validate.py` reads the merged enum set when checking a dossier.
- Schemas themselves stay strict (no `"allowExtensions": true` in the
  JSON Schema documents); the merge happens at validation time, not
  at schema-load time.

### Why defer

Persistence-model questions (does a corpus with extended enums work
on a machine that doesn't see the extension?), schema-evolution
questions (what happens to old dossiers when an extension is added
later?), governance questions (who owns the extension list?). All
solvable, but premature without a concrete forcing function.

---

## Phase 4 — Validator plugins (deferred)

**When to build:** when a kind needs different required dossier
sections than `validate.py` enforces, OR when domain subkinds beyond
`"role"` need their own validation.

### Sketch

```python
# kg/shared/validators.py (new)
@dataclass
class DossierValidator:
    kind: str                           # "rule", "domain", "process"
    subkind: str | None = None          # narrow to a domain subkind
    required_sections: list[str] = field(default_factory=list)
    custom_check: Callable[[dict], list[str]] | None = None
```

Pulls `REQUIRED_RULE_DOSSIER_SECTIONS` etc. out of
`logigraph/lib/cli/validate.py`. Each validator plugin contributes
one or more `DossierValidator`s. Project-local validators override
built-ins on `(kind, subkind)` match.

### Why defer

Bundles cleanly with Phase 3 (both touch dossier shape). Doing them
together amortizes the schema-evolution cost.

---

## Out of scope

- **Changes to depgraph plugins.** Phase 0 is the only depgraph touch;
  it's a pure refactor with no behavior change. Everything else in
  this plan is logigraph-only.
- **Changes to dossier templates themselves.** Phase 4 territory.
- **Migration tooling for existing logigraph corpora.** Phase 1 is
  backward-compatible by design — the `web-api` plugin auto-activates
  when a web framework is detected, preserving current behavior. No
  data migration needed.
- **Cross-language flow detection** (e.g., a Python service calling a
  TS frontend). Depgraph already handles this via the unified
  primitive-ID space; logigraph cues operate on the unified corpus,
  so this falls out for free.
- **A `command` depgraph kind for CLI corpora.** The `cli` logigraph
  plugin in Phase 1 references this hypothetical kind via
  `entrypoint_kinds`, but the depgraph extractor doesn't emit it
  today. The cue is forward-compatible: when a depgraph plugin /
  extractor change introduces `kind=command`, the logigraph `cli`
  plugin picks it up automatically. Until then, the `cli` plugin
  relies on path globs (a fallback we'd add). Not adding a `command`
  kind in this plan.

---

## Open questions

1. **Should the cli/data_pipeline/event_driven plugins ship in Phase 1
   or wait for concrete corpora?** Authoring them speculatively
   without a real CLI or pipeline corpus to validate against risks
   the same over-fitting we just unwound from depgraph. Recommended:
   ship the protocol + `web-api` + `nextjs` + `nuxt` plugins in
   Phase 1 (they have concrete consumers), and stub the others as
   commented templates in their directories so adding them later is
   a 5-minute edit.

2. **Where does the `command` depgraph kind live, if/when added?**
   That's a depgraph-classifier question, not a logigraph one. Out
   of scope for this plan; raised in the depgraph rewrite plan's
   "future work."

3. **Should the logigraph plugin docs reference depgraph's plugin
   docs by link, or duplicate the legal scope rule?** Recommended:
   duplicate. The legal scope rule is short, the cost of duplication
   is small, and the two subsystems' plugin docs should stand alone.

---

## Effort summary

| Phase | Effort | Status |
|---|---|---|
| 0 — Refactor to `kg/shared/plugins/` | ~1.5h | Buildable now |
| 1 — Logigraph cue plugins | ~3–5h | Buildable after Phase 0 |
| 2 — Signal plugins | ~6–10h when triggered | Deferred |
| 3 — Schema extension | ~10–20h when triggered | Deferred |
| 4 — Validator plugins | ~4–6h when triggered (bundle with 3) | Deferred |

Phase 0 + Phase 1 together: a half-day to a day of focused work.
Closes the silent-degradation gap, leaves logigraph as architecturally
clean as depgraph now is, and sets up the deferred phases to land
incrementally when their forcing functions appear.
