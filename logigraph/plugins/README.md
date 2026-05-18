# Logigraph Plugins

Framework-specific cues for flow detection. Each plugin tells
logigraph what counts as a flow entrypoint, what counts as a
state-mutating sink, what HTTP/RPC methods imply mutation, and which
file-path conventions mark UI entries or API-client wrappers — for
the framework it covers. The classifier and `process-rank` heuristics
read these cues instead of hardcoding the web-API answer.

Same plugin shape as depgraph: a `Plugin` with `name`, `detect`, and
`cues` per the generic protocol in
[`kg.shared.plugins`](../../kg/shared/plugins/). The cue type is
`LogigraphCues`, defined in [`base.py`](./base.py).

> **Authoring a plugin?** Read [`AGENTS.md`](./AGENTS.md) first — it
> covers the open-source-only rule and the PR checklist (identical to
> the depgraph plugin rule, repeated here so each subsystem's docs
> stand alone).

---

## What plugins do

Without plugins, every flow-detection heuristic in
`logigraph/lib/cli/process.py` would assume web-API shape:
`kind=endpoint` is the entrypoint, `kind=model` is the sink, GET means
read, page.tsx is the UI entry. A CLI corpus, an event-driven service,
a data pipeline — all of these would produce zero candidates from
process-rank because none of those kinds exist in the corpus.

Plugins decouple flow-detection rules from framework assumptions.
Each plugin:

- **detects** whether its framework is in use (reads `package.json`,
  `pyproject.toml`, `requirements.txt`, or marker files like
  `vitest.config.ts`), and
- **contributes** a `LogigraphCues` describing the flow shape that
  framework follows.

Cues from active plugins union (sets) or take-max (kind weights). The
classifier and signal loops read the merged cues per project.

---

## Shipped plugins (Phase 1)

| Plugin           | Detects via                                                   | Contributes                                                                |
|------------------|---------------------------------------------------------------|----------------------------------------------------------------------------|
| `general:logigraph` | always-on baseline                                         | empty cues (presence so active set is never empty)                         |
| `web-api`        | npm: express / @nestjs/core / fastify / @hapi/hapi / koa; pypi: fastapi / django / flask / starlette / sanic | `entrypoint_kinds={endpoint}`, `sink_kinds={model}`, `mutation_methods={POST,PUT,DELETE,PATCH}`, kind weights for hub-like models/hooks/services/schemas |
| `nextjs`         | npm: `next`                                                    | `ui_entry_path_globs` (app/page.tsx, pages/*.tsx), `api_client_path_globs` (lib/api.ts, lib/client.ts) |
| `nuxt`           | npm: `nuxt`                                                    | `ui_entry_path_globs` (pages/*.vue), `api_client_path_globs` (composables/) |
| `cli`            | `bin/*` executable, `**/__main__.py`, or `**/cli.py`            | `entrypoint_kinds={command}`, `sink_kinds={util}`, no mutation_methods (argv, not HTTP verbs) |
| `event-driven`   | npm: amqplib / kafkajs / @aws-sdk/client-sqs / nats / bull / bullmq; pypi: kafka-python / aio-pika / pika / celery / boto3 / nats-py | `entrypoint_kinds={handler}`, `sink_kinds={publisher}` |
| `data-pipeline`  | pypi: apache-airflow / prefect / dagster / luigi               | `entrypoint_kinds={task,stage,source}`, `sink_kinds={output,sink}`         |

---

## Configuration

Same shape as depgraph's plugin config. From `project.toml`:

```toml
[classification.plugins]
auto = true                                  # default: auto-detect from manifests
enable = ["web-api"]                         # force on, bypassing detector
disable = ["nextjs"]                         # veto, overrides detector
local_paths = ["./private-plugins"]          # additional plugin dirs
```

- `auto = false` turns off detection; only `general:logigraph` and
  anything in `enable` activate.
- `enable` and `disable` use plugin `name`s (e.g. `"web-api"`, not
  `"web_api"`).
- `enable` wins over `disable` (a plugin listed in both is on).
- Same `[classification.plugins]` block drives both depgraph and
  logigraph plugin activation; the plugin registries are separate but
  share the same configuration surface.

---

## Local (project-private) plugins

Identical mechanism to depgraph: drop a `.py` file under
`<logigraph-data-dir>/plugins/` and it's auto-loaded, OR list paths
in `[classification.plugins] local_paths`. Local plugins override
shipped ones with the same `name`.

Use this for proprietary frameworks the company doesn't want to
upstream — see `AGENTS.md` for the legal scope rule that governs
what should be a PR vs a local plugin.

---

## `LogigraphCues` reference

```python
@dataclass
class LogigraphCues:
    entrypoint_kinds: set[str]          # kinds whose nodes start a flow
    sink_kinds: set[str]                # kinds where state mutation lands
    mutation_methods: set[str]          # HTTP/RPC verbs that imply mutation
    ui_entry_path_globs: set[str]       # globs marking UI entry files
    api_client_path_globs: set[str]     # globs marking API-client wrappers
    test_path_globs: set[str]           # globs marking test files
    headless_skip_kinds: set[str]       # kinds excluded from headless-flow
    kind_weights: dict[str, float]      # per-kind weights for convergence
```

Empty fields mean "no opinion" — consuming code in `process.py` should
treat empty `mutation_methods` as "no filter applies" (every
entrypoint qualifies), empty `ui_entry_path_globs` as "no UI signal
configured," etc.

---

## Authoring a plugin (worked example)

Adding Hono (a small, fast TS web framework):

### 1. Confirm it's open source

Hono is MIT-licensed, distributed on npm. Eligible. (Read
[`AGENTS.md`](./AGENTS.md) for the full rule.)

### 2. Create the module

```bash
mkdir logigraph/plugins/hono
touch logigraph/plugins/hono/__init__.py
```

### 3. Write `plugin.py`

```python
# logigraph/plugins/hono/plugin.py
"""Hono plugin. Hono is an Express-shaped TS framework (method-chained
route handlers on a top-level app instance). The shape matches the
web-api cue set: endpoint entry, model sink, REST mutation methods."""
from kg.shared.plugins import Plugin, has_npm_dep

from logigraph.plugins.base import LogigraphCues

PLUGIN = Plugin(
    name="hono",
    detect=lambda repo_path: has_npm_dep(repo_path, "hono"),
    cues={"logigraph": LogigraphCues(
        entrypoint_kinds={"endpoint"},
        sink_kinds={"model"},
        mutation_methods={"POST", "PUT", "DELETE", "PATCH"},
    )},
)
```

### 4. Add a test

Extend `logigraph/tests/test_plugin_registry.py`:

```python
def test_hono_detects_from_package_json(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({
        "dependencies": {"hono": "^4.0.0"},
    }))
    _, active = build_config(tmp_path, auto=True)
    assert "hono" in active
```

### 5. Run

```bash
.venv/bin/python -m pytest logigraph/tests/test_plugin_registry.py
.venv/bin/python -m pytest logigraph/tests -q
```

### 6. Commit

```
logigraph/plugins/hono: detector + web-api-shaped cues for Hono
```

---

## Limitations & gaps

- **No depgraph extractor support for some `entrypoint_kinds` yet.**
  The `cli` plugin declares `entrypoint_kinds={"command"}` and
  `event-driven` declares `{"handler"}` — neither kind is currently
  emitted by depgraph extractors. Until they are, the `cli` /
  `event-driven` plugins' cue contributions only affect path-based
  signals (headless-skip behavior, test-path filtering, kind weights);
  the kind-based entrypoint check returns nothing. Adding those kinds
  is depgraph-classifier work, tracked separately.

- **No signal plugins yet.** Phase 1 makes cues pluggable; Phase 2
  (deferred per the rewrite plan) makes the heuristic signals
  themselves pluggable. A domain that needs a fundamentally different
  signal — say, "fan-in convergence on an event-bus topic" — has to
  wait for Phase 2.

- **No schema-enum extensions yet.** The hardcoded enums in
  `domain.schema.json` / `process.schema.json` (subkind, role, surface
  role, etc.) are Phase 3 territory and not addressed here.

---

## Related

- [`AGENTS.md`](./AGENTS.md) — PR-authoring instructions for AI
  agents, with the open-source-only scope rule.
- [`base.py`](./base.py) — `LogigraphCues` dataclass.
- [`../lib/cli/process.py`](../lib/cli/process.py) — consumes the
  cues via `_load_logigraph_cues(ctx)`.
- [`../../kg/shared/plugins/`](../../kg/shared/plugins/) — generic
  plugin registry shared with depgraph.
- [`../../depgraph/plugins/`](../../depgraph/plugins/) — sibling
  plugin layer for the classifier.
