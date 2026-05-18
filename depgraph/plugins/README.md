# Depgraph Plugins

Framework-specific classification cues, self-detected from a repo's
manifest files. Each plugin contributes the patterns a downstream
classifier needs to recognise route handlers, ORM models, React hooks,
test functions, etc. — and decides whether to activate based on the
repo's own dependencies.

The plugin pattern is the same shape as Vite / ESLint / pytest plugins:
a registry of self-detecting strategies, data-driven activation, no
imperative wiring. Adding a new framework is one new module in this
directory — no edits to the engine, no edits to other plugins.

> **Authoring a plugin?** Read [`AGENTS.md`](./AGENTS.md) first — it
> covers the open-source-only rule and the PR checklist.

---

## What plugins do

Classifiers in `depgraph/lib/classification/` look at primitive shape
(decorators, base classes, name patterns, etc.) and decide whether a
function is an `endpoint`, a `hook`, a `service`, etc. The *patterns*
those classifiers check against — `app.get` for routes, `useState` for
React hooks, `DeclarativeBase` for SQLAlchemy models — are **per
framework**. A project using Vue + Hapi + Mongoose has none of those
patterns; it has different patterns. Plugins ship the per-framework
patterns and decide which ones apply to a given repo.

Without plugins, the framework would have to either (a) hardcode one
assumed stack (React + FastAPI + SQLAlchemy + …) and misclassify every
other stack, or (b) check every possible pattern against every repo and
explode the false-positive rate. Plugins solve both: detection scopes
the pattern set, project authors can extend or veto.

---

## Architecture

Three pieces:

### 1. `Plugin` protocol — `base.py`

```python
@dataclass
class Plugin:
    name: str                                  # stable identifier
    detect: Callable[[Path], bool]             # is this framework active?
    cues: dict[str, LanguageCues]              # per-language contributions
```

A plugin is a value, not a class hierarchy. Each plugin module exports
a top-level `PLUGIN: Plugin = Plugin(...)`.

### 2. Registry — `__init__.py`

`_discover_plugins()` walks every subpackage of `depgraph.plugins` and
collects each `PLUGIN` it finds. `build_config(repo_path, ...)` runs
each plugin's detector and unions the active set's cues into a
`ClassificationConfig`. `build_config_for_repos(repo_paths, ...)`
extends this to multi-repo projects.

### 3. Plugin modules — `<slug>/plugin.py`

Each framework's cues + detector live in their own subpackage. The
shipped set:

| Plugin            | Detects via                                            | Contributes                                   |
| ----------------- | ------------------------------------------------------ | --------------------------------------------- |
| `general:python`  | always-on                                              | `orm_schema_link_vias` baseline               |
| `general:typescript` | always-on                                           | `orm_schema_link_vias` baseline               |
| `react`           | `react` in `package.json` deps                         | React built-in hook names (`useState`, `useEffect`, …) |
| `redux`           | `redux` or `react-redux` in `package.json`             | `useSelector`, `useDispatch`, `useStore`      |
| `tanstack-query`  | `@tanstack/react-query` (v4+) or `react-query` (v3)    | `useQuery`, `useMutation`, `useInfiniteQuery`, `useQueryClient`, … |
| `swr`             | `swr` in `package.json`                                | `useSWR`, `useSWRConfig`, `useSWRMutation`, … |
| `nextjs-hooks`    | `next` in `package.json`                               | `useRouter`, `usePathname`, `useSearchParams`, `useParams`, … |
| `react-i18next`   | `react-i18next` or `next-i18next`                      | `useTranslation`, `useSSR`                    |
| `react-intl`      | `react-intl` in `package.json`                         | `useIntl`                                     |
| `growthbook`      | `@growthbook/growthbook-react` / `@growthbook/growthbook` | `useFeature`, `useFeatureValue`, `useFeatureIsOn`, `useGrowthBook` |
| `vitest`          | `vitest` dep or `vitest.config.*` marker               | Vitest BDD primitives (`describe`/`it`/`expect`/…) |
| `mocha`           | `mocha` dep or `.mocharc.*` marker                     | Mocha BDD primitives (`describe`/`it`/`before`/`after`/…) |
| `express`         | `express` in `package.json` deps                       | `app.X` / `router.X` route decorators         |
| `prisma`          | `@prisma/client` dep or `prisma/schema.prisma` marker  | `Model` / `BaseEntity` ORM base classes       |
| `fastapi`         | `fastapi` in pyproject / requirements                  | Python `route_decorators` (FastAPI shape)     |
| `sqlalchemy`      | `sqlalchemy` in pyproject / requirements               | `DeclarativeBase` / `Base` / `BaseModel`      |
| `pytest`          | `pytest` dep, `pytest.ini`, or `[tool.pytest*]`        | `pytest.fixture` / `pytest.mark` / `pytest.raises` / … |

---

## Configuration

Project authors control activation via `project.toml`:

```toml
[classification.plugins]
auto = true                              # default: auto-detect from manifests
enable = ["my-internal-framework"]       # force on (bypasses detector)
disable = ["jest"]                       # veto (overrides detector)
local_paths = ["./private-plugins"]      # load extra plugins from disk
```

- `auto = false` turns off detection entirely; only `general:*` baselines
  and anything in `enable` activate.
- `enable` and `disable` take plugin `name`s exactly (not module slugs;
  these match the registry's `Plugin.name`).
- `enable` wins over `disable` (a plugin listed in both is on).
- `local_paths` is documented in the next section.

For a synthetic test fixture with no `package.json` / `pyproject.toml`,
use `enable` to declare the framework set explicitly — see
`depgraph/tests/test_kitchen_sink.py::_write_project_toml`.

---

## Local (project-private) plugins

Not every framework belongs upstream. Internal company tools, in-house
ORMs, vendored fork-of-a-framework patterns, anything proprietary —
these should *work* against your codebase without being shared. The
plugin loader supports two project-local paths:

1. **Convention path** — `<data-dir>/plugins/` is auto-loaded if it
   exists. Drop `.py` files in there, each exporting a `PLUGIN: Plugin
   = Plugin(...)` constant. The registry treats them identically to
   shipped plugins; the only difference is they live in the project's
   knowledge-graph data dir (which typically isn't published) rather
   than the framework's source tree (which is).

2. **Explicit `local_paths`** — list extra directories (or individual
   `.py` files) in `project.toml` under `[classification.plugins]
   local_paths`. Relative paths resolve against the data dir.

```toml
[classification.plugins]
local_paths = [
    "./private-plugins",          # extra directory
    "/abs/path/to/acme_orm.py",  # single file
]
```

### Override semantics

A local plugin with the same `name` as a shipped one **replaces** the
shipped plugin entirely. Useful when the framework's default cues for a
public framework are wrong for your fork (e.g. you've forked React and
renamed every hook with a `useAcme*` prefix — ship a local plugin named
`react` to swap cues without forking the framework).

### Example: a private detector

`<data-dir>/plugins/acme_internal_orm.py`:

```python
"""Detect Acme's internal ORM (closed source).

`AcmeBase` is the company's base class for all DB-backed models. Recognise
it the same way SQLAlchemy's `DeclarativeBase` is recognised.
"""
from depgraph.lib.classification.config import LanguageCues
from depgraph.plugins.base import Plugin, has_pypi_dep

PLUGIN = Plugin(
    name="acme-internal-orm",
    detect=lambda repo_path: has_pypi_dep(repo_path, "acme-orm"),
    cues={
        "python": LanguageCues(
            orm_base_classes={"AcmeBase", "AcmeAsyncBase"},
        ),
    },
)
```

Done. The plugin loads on the next `kg depgraph regen`, classifies
Acme's models as `model` kind, and never leaves the company's
knowledge-graph data dir.

### When to upstream vs keep local

| Scenario                                              | Upstream (PR) | Keep local |
|--------------------------------------------------------|---------------|------------|
| Detects a publicly-available open-source framework     | ✅            |            |
| Detects an internal/proprietary/private codebase       |               | ✅         |
| Recognises a public framework but with company-specific naming overrides |  | ✅ (override locally) |
| Detects a vendored fork of an OSS framework you can't share |          | ✅         |
| Adds patterns for an OSI-licensed library not yet covered |  ✅         |            |

See [`AGENTS.md`](./AGENTS.md) for the full open-source-only rule that
governs upstream PRs — including the legal context for why agents in
particular must not publish private detectors without explicit
human authorisation.

---

## Cue reference

Each plugin's `cues` map contains `LanguageCues` keyed by language
name. The fields:

| Field                       | What the classifier uses it for                              | Example values                                       |
| --------------------------- | ------------------------------------------------------------ | ---------------------------------------------------- |
| `route_decorators`          | Endpoint classifier — function decorated by one of these     | `"app.get"`, `"router.post"`, `"GET"` (NestJS)       |
| `orm_base_classes`          | Model classifier — class `extends` one of these              | `"DeclarativeBase"`, `"Model"`, `"Document"`         |
| `test_framework_primitives` | Test classifier — decorator or call resolves to one of these | `"pytest.fixture"`, `"it"`, `"describe"`             |
| `hook_call_names`           | Hook classifier — function calls one of these                | `"useState"`, `"useEffect"`                          |
| `orm_schema_link_vias`      | Model classifier — class-attribute name linking to a schema  | `"__tablename__"`, `"@@map"`                         |

If your framework needs a cue not in this list, that's a signal the
classifier needs extension first — open an issue describing the
classifier rule before authoring the plugin.

---

## Detection helpers — `base.py`

Use these from a plugin's `detect` lambda. Each is robust to missing
files and bad JSON / TOML.

### `has_npm_dep(repo_path, package: str) -> bool`

True if `package` appears in `dependencies` / `devDependencies` /
`peerDependencies` of the nearest `package.json` (walks upward from
`repo_path`, so monorepos with a shared `package.json` work).

```python
detect=lambda p: has_npm_dep(p, "react")
```

### `has_pypi_dep(repo_path, package: str) -> bool`

True if `package` is in `pyproject.toml` (PEP 621 `[project.dependencies]`
or Poetry's `[tool.poetry.dependencies]`) or in `requirements.txt` /
`requirements-*.txt`. Case-insensitive on the package name; ignores
version specifiers.

```python
detect=lambda p: has_pypi_dep(p, "fastapi")
```

### `has_marker_file(repo_path, *globs) -> bool`

True if any glob (relative to `repo_path`) matches an existing file.
Useful when a tool is signalled by config presence rather than a
dependency entry — e.g. `pytest.ini`, `vitest.config.ts`.

```python
detect=lambda p: has_marker_file(p, "vitest.config.ts", "vitest.config.js")
```

### Combining detectors

```python
detect=lambda p: has_npm_dep(p, "jest") or has_marker_file(p, "jest.config.*")
```

If you need a detector beyond these helpers (e.g., parse a
`pyproject.toml` section), write it inline in a `_detect(repo_path)`
helper alongside the `PLUGIN =` assignment. Keep it pure (no
side-effects); the registry calls it once per repo.

---

## Authoring a plugin (worked example)

Adding NestJS:

### 1. Decide it's worth a plugin

NestJS is open-source (MIT). It has canonical patterns the existing
classifiers care about: `@Controller`, `@Get`/`@Post`/…, `@Injectable`.
The route decorator names don't overlap with Express's. Good plugin
candidate.

### 2. Create the module

```bash
mkdir depgraph/plugins/nestjs
touch depgraph/plugins/nestjs/__init__.py
```

### 3. Write `plugin.py`

```python
# depgraph/plugins/nestjs/plugin.py
"""NestJS plugin.

Activates when `@nestjs/core` is an npm dep. NestJS uses class-method
decorators on `@Controller`-tagged classes for routes:

    @Controller('users')
    export class UsersController {
      @Get(':id') findOne(...) { ... }
    }

The route decorators target METHODS, not module-level functions, so the
endpoint classifier sees them via the same `route_decorators` cue path
as Express / FastAPI.
"""
from depgraph.lib.classification.config import LanguageCues
from depgraph.plugins.base import Plugin, has_npm_dep

PLUGIN = Plugin(
    name="nestjs",
    detect=lambda repo_path: has_npm_dep(repo_path, "@nestjs/core"),
    cues={
        "typescript": LanguageCues(
            route_decorators={
                "Get", "Post", "Put", "Patch", "Delete",
                "Head", "Options", "All",
            },
        ),
    },
)
```

### 4. Add tests

Extend `depgraph/tests/test_plugin_registry.py`:

```python
def test_nestjs_detects_from_package_json(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({
        "dependencies": {"@nestjs/core": "^10.0.0"},
    }))
    cfg, active = build_config(tmp_path, auto=True)
    assert "nestjs" in active
    assert "Get" in cfg.languages["typescript"].route_decorators
```

### 5. Verify

```bash
.venv/bin/python -m pytest depgraph/tests/test_plugin_registry.py -v
.venv/bin/python -m pytest depgraph/tests -q       # full suite
```

### 6. Commit

```
depgraph/plugins/nestjs: add detector + route decorators for NestJS
```

Authoring more frameworks? See [`AGENTS.md`](./AGENTS.md) for the full
checklist + the legal scope rule.

---

## Testing your plugin

Add a test to `depgraph/tests/test_plugin_registry.py` following the
existing patterns. Each plugin should have at least:

- **Detection test** — create a `tmp_path` with the relevant manifest,
  call `build_config(tmp_path)`, assert the plugin is in the active list.
- **Cue contribution test** — same setup, then assert at least one
  contributed cue appears in the resulting `ClassificationConfig`.

If your plugin has multiple detection paths (npm dep + marker file +
explicit config), test each. Don't test the classifier behaviour here
— that's covered by the wider classifier test suite; plugin tests
verify the plugin contract only.

---

## Limitations & gaps

- **Extractor-side hardcoded sets.** `extract.ts` and `extract.py`
  still carry inline `TS_TEST_FRAMEWORK_PRIMITIVES` /
  `_PY_TEST_FRAMEWORK_PRIMITIVES` sets used at the `tests` edge pass to
  filter out framework machinery. The classification engine is fully
  plugin-driven; the extractor exclusion lists are not yet plumbed
  through. Impact is cosmetic (the unfiltered edges target
  `external::npm::<pkg>::<name>` which downstream classifiers ignore).
  Plumbing config through to the extractor subprocess is a future
  cleanup — see the commit landing this plugin system for context.

- **No extractor hooks yet.** Plugins today only contribute cues; they
  can't register additional AST walks. Frameworks with patterns the
  extractor doesn't yet understand (e.g. NestJS DI tokens, Django URL
  patterns, GraphQL resolvers) need the extractor to know about them
  too. Extractor-hook support is a follow-up that would extend the
  `Plugin` dataclass with an optional `extract_hook` field.

- **Detection is binary, not version-aware.** A plugin either fires or
  doesn't — there's no "react 16" vs "react 18" branch. If a
  framework's canonical patterns change across major versions, one
  plugin per version (e.g. `react`, `react-legacy`) is the v0 escape
  hatch.

- **No precedence model between plugins.** If two plugins contribute
  conflicting cues for the same key, the union semantics mean both
  patterns match. This is usually fine (more cues = more recognition),
  but a future model where one plugin can *replace* a cue from
  another might be needed for genuine conflicts.

---

## Related

- [`AGENTS.md`](./AGENTS.md) — PR-authoring instructions for AI agents,
  with the open-source-only scope rule.
- [`../lib/classification/`](../lib/classification/) — classifier
  implementations that consume the cues.
- [`../lib/edges.py`](../lib/edges.py) — edge taxonomy the classifiers
  ultimately drive.
