# Layered substrate: primitives → code deps → system deps → knowledge

**Status:** Design — draft 2026-05-16
**Owner:** Logan Greenlee
**Scope:** `~/tools/knowledge-graph/` — all subsystems (depgraph framework, logigraph, graphui)

## Problem

The current depgraph captures a thin slice of the codebase and uses lexical heuristics to label each captured node.

**Capture is incomplete.** Today's TypeScript extractor walks only top-level function declarations and top-level exported `const = arrow` bindings. Class declarations and class methods are invisible. On class-heavy backends the miss can be several times larger than the top-level surface the extractor *does* see — methods, member variables, nested classes all unrepresented. Other languages have analogous gaps. Declarative sources projects often rely on (Prisma `schema.prisma`, SQL migrations, JSON schemas) are unrepresented entirely despite being source-controlled and load-bearing for rules about tenancy, schema evolution, and contract compatibility.

**Classification is lexical, not structural.** "Service" is decided by name regex (`react.ts` says "anything not PascalCase and not `use<Capital>` → service") and path filter (`service.ts` says "anything under `lib/pages/services/utils`"). Neither is grounded in what the symbol does. On real codebases with vendored upstream trees, codegen output, or non-conventional directory layouts, this can produce thousands of service nodes that aren't first-party code.

**The system layer is invisible.** Today's depgraph has nothing between code and knowledge. `route_calls` is a fragment — outbound HTTP calls only, statically resolved, brittle on call patterns that differ from whichever reference project the detector was originally tuned against. Webhook fan-out, queue producers and consumers, cross-service DB sharing, shared cache namespaces, file storage substrates, observability emitters, feature flag checks, auth provider trust — none represented. Logigraph rules about idempotency, audit-emit, and tenancy-filter want to claim against system-level facts that don't have node ids to claim against.

**Third-party code is conflated with our code.** `node_modules`, vendored upstream trees, generated client artifacts (e.g., `src/generated/<orm-client>/`) get walked and emit primitives indistinguishable from first-party code. Rules can't tell the difference between "we own this" and "we depend on this."

## Goals

- Capture **every named symbol** in the codebase — module, package, class, function, variable — uniformly across every source language the host project tracks. No kind decisions at extraction time.
- Treat **all structured sources as languages**: TypeScript, Python, Go, Rust, C, C++, SQL, JSON Schema, Prisma, OpenAPI, GraphQL, Protobuf. Each has its own parser; all emit the same primitive shape.
- Make **code-level dependencies a first-class layer**: edges between primitives with a documented taxonomy. Resolution graded `exact` / `fuzzy` / `unresolved`.
- Add a **system-level dependency layer** for inter-service runtime communication. Edges sourced from static evidence — code patterns, IaC, service configuration. Taxonomy covers HTTP, webhook, queue, shared DB, shared cache, file storage, notifications, observability, feature flags, auth trust, scheduled triggers.
- Move **classification to a derived step** over the captured graph. Kinds (component, hook, controller, service, model, util, test) come from structural rules over primitives + edges.
- Keep **scope sharp**: the dependency mapping covers first-party code only. Third-party and generated code appear as terminal targets — call sites resolve into them but we don't walk their internals. Boundary is set per-repo by config, not by heuristic. **Pointing the framework at the right code is the user's responsibility** — a human or LLM authors the per-repo include / exclude paths and language registry; the extractor walk that follows is deterministic.
- Keep **logigraph claim targets stable enough that existing rules don't need to be re-authored**. Migration is opt-in per rule; reconcile rewrites `depgraph_id` references where the structural hash matches.
- Keep the framework **project-agnostic**: project-specific extractors, configs, detectors, dossiers, and named examples live in the project's own knowledge-graph data repo, not in the framework. The framework absorbs patterns only once they generalize across multiple projects.

## Non-goals

- No new logigraph node kinds. The knowledge layer continues to be rules / domain / processes.
- No runtime evidence in the system-dependency extractor at launch. Static analysis (code, config, IaC, DSL sources) is the bar; observability traces and runtime introspection are follow-ups.
- No graphui rewrite. Existing kind-dirs continue to populate; the difference is they're now derived from primitives + edges, not emitted by detectors.
- No retroactive byte-for-byte parity with prior pre-flip corpora. Parity splits into primitive-level + classification-level.
- No new Claude Code hook phases. `kg` dispatcher unchanged.

## Architecture

```
┌─ Layer 4: Knowledge ───────────────────────────────────────┐
│  rules / domain / processes (logigraph, unchanged shape)   │
│  claims point at layer 1 nodes OR layer 2 OR layer 3 edges │
└────────────────────────────┬───────────────────────────────┘
                             │ claims against
┌────────────────────────────▼───────────────────────────────┐
│  Layer 3: System-level dependencies                        │
│  service ↔ service (HTTP, gRPC)                            │
│  event/bus fan-outs (webhook, queue, topic)                │
│  shared infra (DB, cache, file storage, env, secrets)      │
│  notifications, observability, feature flags, auth, cron   │
└────────────────────────────┬───────────────────────────────┘
                             │ derived from layer 1 + 2
                             │ + system-level extractors
┌────────────────────────────▼───────────────────────────────┐
│  Layer 2: Code-level dependencies                          │
│  symbol → symbol edges                                     │
│  defines / extends / implements / calls / references /     │
│  instantiates / decorates / includes / assigns / reads /   │
│  imports / tests                                           │
└────────────────────────────┬───────────────────────────────┘
                             │ resolved from layer 1
┌────────────────────────────▼───────────────────────────────┐
│  Layer 1: Primitives                                       │
│  module / package / class / function / variable            │
│  Uniform across every source language (TS, Python, Go,     │
│  Rust, C, C++, SQL, JSON Schema, Prisma, OpenAPI,          │
│  GraphQL, Protobuf, …). Higher-order concepts (event,      │
│  model, endpoint, schema, table) are derived, not added.   │
└────────────────────────────────────────────────────────────┘
```

## Layer 1: Primitives

### The five primitives

| Primitive | Description |
|---|---|
| **module** | A source file in any tracked language. |
| **package** | An organizational container above module — folder, language namespace, crate. |
| **class** | Any named entity with member variables and/or member functions. Includes class, struct, interface, trait, enum, record, sum type, DB table, schema definition. The OO-flavored distinctions collapse into attributes. |
| **function** | A callable named binding. Top-level functions, methods (with `owner: <class_id>`), operator overloads, stored procedures, GraphQL resolvers — all functions. |
| **variable** | A non-callable named binding. Top-level constants, locals declared at module scope, class fields (with `owner: <class_id>`), DB columns, JSON properties — all variables. |

OO-flavored kinds (property, method, constant, interface, enum) are not separate types. They become attributes on the simpler kinds:

- `owner: <class_id>` — for functions / variables that are class members.
- `mutable: bool` — distinguishes constant from variable. Default true.
- `abstract: bool` — declares without implementing. An interface is a class with `abstract: true` on the class and on its declared members.
- `instantiable: bool` — false for interfaces, traits, abstract classes.
- `inheritable: bool` — false for sealed / final classes.
- `generated: bool` — set by extractor when the file is the output of codegen.
- `template_parameters: list<string>` — generics (C++ templates, TS generics, Rust generic params, Python TypeVar).
- `macro: bool` — for C/C++ preprocessor macros that look function-like or constant-like.
- `external: bool` — see "External terminals" below.

### Id format

Universal shape: `<repo>::<source-path>::<symbol-chain>`.

- module: `<repo>::<source-path>`
- package: `<repo>::<package-path>` (folder path; trailing slash stripped)
- class: `<repo>::<source-path>::<name>`
- function (top-level): `<repo>::<source-path>::<name>`
- function (class-owned method): `<repo>::<source-path>::<class>.<name>`
- variable (top-level): `<repo>::<source-path>::<name>`
- variable (class-owned field): `<repo>::<source-path>::<class>.<name>`

Existing logigraph claims like `<repo>::<source-path>::Foo` resolve unchanged. Method-level ids (`<repo>::<source-path>::ClassName.methodName`) are new but follow the same pattern.

### Every primitive carries

- `signature` — for callable primitives, the callable shape (parameters, return type, modifiers). Empty for variables.
- `source` — repo, path, line range, language (which extractor emitted it).
- `structural_hash` — sha256 of canonicalized name + signature + scope body. Powers reconcile's stale-claim detection.

### The include boundary

What counts as "ours" is set **per-repo via configuration**, not via heuristic. The framework provides defaults (skip `node_modules`, `.git`, `target/`, `dist/`, common build outputs); each project's `project.toml` overrides:

```toml
[repos.frontend-app]
path = "/path/to/frontend-app"
include_paths = ["src/**"]
exclude_paths = ["src/generated/**"]
languages = ["typescript", "json-schema"]

[repos.backend-api]
path = "/path/to/backend-api"
include_paths = ["src/**", "lib/**", "config/**", "migrations/**", "prisma/**"]
exclude_paths = ["src/generated/**", "src/shared-interfaces/**"]
languages = ["typescript", "sql", "prisma", "json-schema"]
```

The config is the parameter. A human or an LLM authors it; the extractor walk that follows is deterministic. Reproducible regen requires only the config + the tracked repos' current state.

**The framework does not infer first-party scope from heuristics.** Path patterns, naming conventions, and language inference are not reliable across projects — what's vendored vs authored, what's tracked vs ignored, what's first-party vs upstream are decisions only the user can make. **Pointing the framework at the correct locations is the user's responsibility** (a human writes the config; an LLM may draft it for review). Wrong config produces wrong corpus by design: the alternative — heuristic guessing — silently mislabels code in ways rules cannot detect.

### External terminals

Code outside the include set, vendored upstream trees, and generated client artifacts do not become primitives. They appear as **terminal targets** in the edge graph — leaves that calls and references point at, but which we never walk into.

Terminal id format: `external::<source>::<package>::<symbol-chain>`. Examples:

- `external::npm::<package>::<symbol>` — third-party library symbol
- `external::npm::@<orm>/client::<Client>.<entity>.<method>` — generated ORM client method
- `external::pypi::<package>::<symbol>` — Python library symbol
- `external::saas::<vendor>::<event-topic>` — third-party event topic (e.g., a payment processor's `charge.succeeded`)
- `external::vendored::<upstream-lib>::<symbol>` — code checked into the repo but not first-party authored

The principle: **external means we treat it as a black box.** We know the surface we call into; we don't reason about its internals.

When black-box treatment loses load-bearing structural information, we parse the source-of-truth DSL instead. Prisma's generated client is external, but `schema.prisma` is a language we extract — so a `db_access` edge from our code to a Prisma model targets the *schema*-sourced primitive, not the generated client. The system-layer extractor that recognizes Prisma call patterns is responsible for that resolution. Same shape applies to OpenAPI codegen (parse the spec), protobuf (parse `.proto`), GraphQL (parse the SDL).

### Language registry

Languages are first-class. The framework ships a registry mapping language name to extractor invocation + file patterns:

```toml
# Shipped defaults at ~/tools/knowledge-graph/depgraph/languages.toml
[languages.typescript]
extensions = [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"]
extractor = "{kg_dir}/depgraph/extractors/typescript/extract.ts"

[languages.python]
extensions = [".py"]
extractor = "{kg_dir}/depgraph/extractors/python/extract.py"

[languages.sql]
extensions = [".sql"]
extractor = "{kg_dir}/depgraph/extractors/sql/extract.py"

[languages.prisma]
extensions = [".prisma"]
extractor = "{kg_dir}/depgraph/extractors/prisma/extract.ts"

# … and so on for go, rust, c, cpp, json-schema, openapi, graphql, protobuf
```

A per-project `project.toml` can add project-local languages (custom DSLs, internal schema formats) without forking the framework.

### Per-language extraction outline

Each language's extractor walks its native AST and emits the five primitives. Implementation notes per language:

- **TypeScript / JavaScript** — ts-morph. Emits `ClassDeclaration`, `MethodDeclaration`, `PropertyDeclaration`, `FunctionDeclaration`, `VariableDeclaration` (top-level *and* class-scoped), `InterfaceDeclaration` (as class with `abstract: true`), `EnumDeclaration` (as class), `TypeAliasDeclaration` (as class with `instantiable: false`). Object-literal API clients (`export const profileApi = { ... }`) emit a class with method/variable members per property.
- **Python** — stdlib `ast`. `ClassDef`, `FunctionDef`, `AsyncFunctionDef`, `Assign` / `AnnAssign` at class or module scope. Class members captured regardless of path. Pydantic models and SQLAlchemy mappers are not special-cased; their base-class heritage is just an `extends` edge inspected at derivation.
- **Go** — tree-sitter-go. `function_declaration`, `method_declaration` (receivers; method's `owner` is the receiver type's class id), `type_declaration` (structs, interfaces), `const_declaration`, `var_declaration`.
- **Rust** — tree-sitter-rust. `fn_item`, `impl_item` blocks (methods get the impl-target as owner), `struct_item`, `enum_item` (variants with payload become sub-classes via `extends` to the enum class), `trait_item` (class with `abstract: true`), `const_item`, `static_item`.
- **C** — tree-sitter-c. `function_definition`, top-level `declaration`, `struct_specifier`, `enum_specifier`, `union_specifier`, `typedef`, `preproc_def` (variables/functions with `macro: true`). Header/source declaration-definition pairs merge into one primitive, preferring the definition's `source` block; declaration sites recorded as additional `defines` edges. Forward-declaration-only symbols are primitives with no body. `#include` directives emit `includes` edges at Layer 2.
- **C++** — tree-sitter-cpp. C's set plus `class_specifier`, `namespace_definition` (emit as package), `template_declaration` (sets `template_parameters` on the affected class/function), member functions (with `owner` set to the enclosing class), friend declarations (as a `references` edge at Layer 2). Operator overloads are just methods named `operator+`, `operator==`, etc.
- **SQL** — tree-sitter-sql or sqlparse. `CREATE TABLE` → class with column variables. `CREATE VIEW` → class. `CREATE FUNCTION` / stored procedures / triggers → functions. `CREATE INDEX` → emits `references` edges (no primitive). Schemas (Postgres-style `CREATE SCHEMA foo`) → packages.
- **JSON Schema** — official parser. Each `$schema`-bearing file is a module. Top-level `type: object` definitions → classes. `properties` → variables. `definitions` / `$defs` → nested classes. `$ref` → `references` edge. `allOf` / `anyOf` / `oneOf` → `extends` / `implements` edges.
- **Prisma** — `@prisma/sdk` or hand-rolled tree-sitter. `schema.prisma` is one module declaring multiple models. `model User { ... }` → class. Fields → variables (with `mutable` from `@updatedAt` annotation, etc.). `@relation` → `references` edge. `enum Status { ... }` → class with variable members. Generator and datasource blocks are configuration, not primitives — they feed Layer 3 (the datasource block IS the `db_access` target).
- **OpenAPI** — swagger-parser. `components.schemas.*` → classes. `paths.*` → functions (one per HTTP method + path). `parameters` and `responses` → references to schema classes. Each function carries `http_method` + `url_pattern` in its signature for Layer 3 to match against.
- **GraphQL SDL** — graphql-js. `type Foo { … }` → class. `interface`, `union`, `enum` → classes (with `abstract` / sum-type attributes). `Query`, `Mutation`, `Subscription` resolvers → functions. `@directive` annotations → `decorates` edges.
- **Protobuf** — protoc plugin or tree-sitter-proto. `message` → class. fields → variables. `service` → class containing `rpc` functions. `import` → `references` edge. Nested messages → nested classes.

### Migration files as a sub-genre

Schema-modifying files (Django migrations, Alembic, Rails, Prisma migrations, raw SQL migrations) are modules in their host language but carry **ordinal/temporal metadata** no other module does:

- `migration_order` — ordinal or timestamp sortable across migrations in the same repo.
- `up_operations[]` / `down_operations[]` — references to the operation primitives (CREATE TABLE statement, ALTER COLUMN call, etc.) that constitute the migration in each direction.
- `applied_at` (optional) — if the migration history is tracked in a checkable file.

These are attributes on the module primitive, not new primitive kinds. Rules about migration discipline ("every NOT NULL column add has a default", "every destructive migration has a comment") become structural claims against these attributes.

## Layer 2: Code-level dependencies

### Edge taxonomy

| Edge | Source | Target | Notes |
|---|---|---|---|
| `defines` | module / class / package | child primitive | Structural containment. Implicit from extraction. |
| `extends` | class | class | Superclass; superinterface for interfaces; supertrait for Rust. Multi-target allowed (C++ multiple inheritance). |
| `implements` | class | class (with `abstract: true`) | Interface / trait conformance. Multi-target. |
| `calls` | function | function | Resolved or fuzzy. Carries `via` (direct call, method call, super call, hook call, etc.). |
| `instantiates` | function | class | `new Foo()`, `Foo()`, struct literal, dataclass construction. |
| `references` | any primitive | any primitive | Imports, type references, decorator targets, GraphQL `$ref`, foreign-key columns. The catch-all for "this primitive names that one". |
| `reads` | function | variable | Read access to a variable / property. Distinguished from `assigns` so immutability rules can check. |
| `assigns` | function | variable | Write access to a variable / property. |
| `decorates` | function / class | function / class | Python decorators, TS class/method decorators, Rust attribute proc-macros, GraphQL SDL directives. |
| `includes` | module | module | C/C++ `#include`. Distinct from `references` because preprocessor inclusion is textual, not symbolic. |
| `imports` | module | module / primitive | Symbol import (Python `from X import Y`, TS `import { Y } from "X"`, Rust `use X::Y`). Separate from `references` so module-level dep analysis can run without walking every symbol. |
| `tests` | function (test) | function / class / variable | Test asserts behavior of target. Replaces the per-node `tests[]` array. |

External terminals can be edge targets but not edge sources. We never know what `external::npm::express::Router` calls.

### Resolution rules

Graded:

- **`exact`** — import + name + scope chain unambiguously identify a single first-party primitive id (or a known external terminal).
- **`fuzzy`** — name matches exactly one primitive by name across the corpus but the import path didn't resolve. Logged for review.
- **`unresolved`** — target is dynamic (computed property access, runtime dispatch) or external to a non-registered package. Record the surface text but no target id.

Each edge carries `via` (the bridge mechanism), `where` (file:line), and `confidence`. Reconcile keeps a single source-of-truth index per direction (`by_source`, `by_target`) that graphui reads.

## Layer 3: System-level dependencies

### Edge taxonomy

| Edge | Source | Target | Evidence sources |
|---|---|---|---|
| `http_call` | function | endpoint primitive in target service | code: HTTP client SDKs + URL constants; config: API base URLs in env files |
| `webhook_publish` | function | inbound handler in target service | code: webhook URL registration; IaC: webhook subscription resources |
| `webhook_subscribe` | inbound handler function | event identifier | code: route registration + event-type discrimination |
| `queue_produce` | function | topic/queue identifier | code: publish SDK calls; IaC: queue resources |
| `queue_consume` | handler function | topic/queue identifier | code: subscription SDK calls; IaC: subscription resources |
| `db_access` | function | schema-sourced table class | code: ORM method calls resolved through generated-client patterns; DSL: `schema.prisma` and SQL migrations as canonical source |
| `cache_access` | function | cache key namespace | code: Redis client `key` prefixes, in-memory cache instance identifiers |
| `file_storage_access` | function | bucket / path namespace | code: S3 / GCS / Azure Blob SDK calls; local fs operations against known dirs |
| `notification_send` | function | channel + recipient handle | code: email / SMS / push / chat SDK calls. `channel` attribute distinguishes (email / sms / push / chat). |
| `observability_emit` | function | sink identifier | code: Sentry / DataDog / Prometheus / OpenTelemetry SDK calls |
| `feature_flag_check` | function | flag identifier | code: LaunchDarkly / GrowthBook / custom flag-system SDK calls |
| `auth_trust` | service | identity provider identifier | code + config: JWT issuer URLs, OAuth / OIDC discovery endpoints, auth-SDK configuration |
| `schedule_trigger` | scheduled task | function | code: cron-job declarations, scheduled-function frameworks; IaC: CloudWatch Events / Kubernetes CronJob resources |
| `config_read` | function | config key | code: `process.env.X`, `os.environ.get("X")`, JSON / YAML / TOML config imports |
| `env_share` | service | service | derived: two services reading the same config key (`config_read` edges that share a target) |
| `external_service_call` | function | external SaaS endpoint terminal | code: SDK calls to third-party services (payment processors, identity providers, notification providers, verification services, etc.). Distinct from `http_call` because target is external. |

### Evidence sources

System-level extractors are project-aware. They walk the corpus across all tracked repos in one pass and emit edges that span repo boundaries.

- **HTTP edge extractor.** Inputs: Layer-1 primitives (including OpenAPI-sourced endpoint classes if available) + Layer-2 `calls` edges where the target is a known HTTP-client terminal. Matches outbound URL to endpoint primitive in target service; surfaces `unresolved` if the endpoint isn't defined in any tracked service.
- **Webhook extractor.** Walks the corpus for registration patterns — inbound handlers (route registrations in HTTP frameworks), outbound publishers (webhook publish utilities), and vendor-specific verification entry points. Matches publishers to subscribers by URL + event type.
- **Queue extractor.** Per-language SDK call patterns across common queue / messaging / event-bus providers. Optional IaC pass reads queue declarations from Terraform / Helm / Kubernetes manifests and cross-references.
- **DB extractor.** Combines DSL-sourced schema primitives (Prisma, SQL DDL, migrations) with Layer-2 `calls` into ORM clients (Prisma generated client, SQLAlchemy session, GORM, Diesel). Emits `db_access` edges from the calling function to the schema-sourced table primitive.
- **Cache / file-storage extractors.** Same pattern: SDK call recognition + namespace tracking.
- **Notification / observability / feature-flag extractors.** SDK call pattern recognition. Channel and target identifier extracted from arguments.
- **Auth-trust extractor.** Walks env / config files + auth SDK initialization sites for issuer URLs and provider identifiers. Two services with `auth_trust` to the same provider share an implicit coupling — surfaces as an `env_share`-style aggregation.
- **Schedule extractor.** Cron syntax recognition in config and IaC. A scheduled-task registration emits a `schedule_trigger` edge to the consuming function.

**Tests as secondary evidence.** A test that asserts `service A calls service B with payload X` is evidence of an `http_call` edge. Tests feed Layer-3 extractors as a secondary evidence source after code; useful for cases where the call pattern is too dynamic for static recognition.

**Static-only at launch.** Runtime evidence (observability traces, OpenAPI spec consumption from deployed services, deployed-manifest inspection) is deferred. Static analysis catches structural cases; runtime catches the dynamic remainder.

## Layer 4: Knowledge

Logigraph node shapes are unchanged. The substantive change is what claims can target:

- **Rules** continue to claim against Layer-1 ids via `claims_code`. Existing claims (e.g., `<repo>::<source-path>::Foo`) resolve because top-level symbol ids are unchanged. New claims can target method-level ids (`<repo>::<source-path>::ClassName.methodName`) or Layer-3 edge ids.
- **Processes** unchanged; step claims may now target system-level edges.
- **Domain** unchanged. Domain entities may grow optional `bound_to_system_edge[]` fields to anchor the entity to specific runtime communication patterns.

Rules claim against first-party primitives only. They can *reference* an external terminal (e.g., a rule about webhook signature verification might mention a vendor's verification entry point) but the claim *anchor* is the first-party code calling into the external.

Reconcile's stale-claim detection now spans three layers. A claim with `depgraph_id` is resolved against the union; if the primitive moved but the `structural_hash` matches a new id, the claim auto-rewrites.

## Derived classification

The kinds surfaced in graphui — component, hook, controller, service, model, util, test — are derived from primitives + edges by a classification engine that runs after extraction.

### Classification rules (initial set)

| Kind | Structural rule |
|---|---|
| **component** | function / method whose body returns JSX **or** PascalCase variable bound to an HOC call (`React.forwardRef`, `React.memo`) **or** PascalCase alias of a known component |
| **hook** | function whose name matches `use<Capital>` **and** calls another known hook or a React built-in hook |
| **endpoint / controller** | function targeted by an inbound HTTP route registration (Layer-3 evidence) |
| **service** | function with at least one of: `db_access` edge, `queue_produce` edge, `webhook_publish` edge, `notification_send` edge, `file_storage_access` edge **AND** transitively called from at least one endpoint |
| **model** | class with `extends` to a known ORM base **or** sourced from a schema-language extractor (Prisma model, SQL table, GraphQL type) |
| **schema** | class sourced from a schema-language extractor that is referenced by an endpoint signature |
| **util** | function called by at least one classified kind **and** classifies as none of the above |
| **test** | function whose body calls a known test framework primitive (`it`, `test`, `pytest.fixture`, `t.Run`, `#[test]`) |

Auth requirements and tenancy markers don't become kinds — they become **attributes** on the classified primitives (`auth_required: yes/no/admin`, `tenant_scoped: bool`), surfaced from middleware-stack and parameter-name evidence. Classification conflicts (a function that returns JSX *and* makes a `db_access` call) flag rather than resolve silently.

### Language generality

Each rule expresses a structural shape. Cues are per-language. A "component" in React (returns JSX) maps to a "view" in Vue (default-exports a component options object), to a template-bound handler in Django, to a UI struct in Yew. The classification engine takes per-language cue mappings as input; the rule shape doesn't change.

External primitives don't classify. Generated primitives don't classify (rules don't anchor against them).

## Migration plan

Sequential because each layer feeds the next.

### Phase 1: Language registry + primitive extractors

- Build the language registry (shipped defaults + per-project overrides). Extractor invocation is parameterized by registry entry, not hardcoded per repo.
- Land the simplified primitive emitter in the TypeScript extractor: every class, function, variable, with full attribute set.
- Land the equivalent in Python, Go, Rust, C, C++ (incrementally; prioritize the languages most heavily used in the host project).
- Ship Prisma + SQL + JSON Schema + OpenAPI + GraphQL + Protobuf extractors. They emit the same primitive shape.
- Include / exclude boundary config goes in per-repo `project.toml`. Walk is deterministic given config.
- External terminal id format wired in: calls and references to non-tracked symbols emit terminal targets, not stub primitives.

No classification changes yet. Corpus grows; graphui shows the new kinds (class, methods inside classes, schema-sourced tables) with empty dossier coverage.

### Phase 2: Code-edge layer

- Implement the edge taxonomy. The existing `depends_on` field on each node becomes derived from this edge index, not emitted ad-hoc per detector.
- Resolution starts at `exact` only. `fuzzy` and `unresolved` add later behind a confidence threshold.
- `tests` becomes an edge; the old per-node `tests[]` array is recomputed from the index.

### Phase 3: Derived classification

- Implement the classification engine. Existing kind-dirs (`components/`, `hooks/`, `services/`) become its output, not the extractor's.
- New flag: `classification_conflict` for primitives that satisfy multiple kinds' rules.
- Existing logigraph claim ids continue to resolve because top-level symbol ids are unchanged.

### Phase 4: System-level edges

- One extractor at a time, ordered by leverage:
  1. **HTTP + DB** — closes the largest substrate gap (route_calls + tenancy claims).
  2. **Webhook** — closes idempotency claims.
  3. **Queue + Notification** — closes audit-emit and side-effect claims.
  4. **Cache + File-storage + Observability** — closes the rest.
  5. **Feature-flag + Auth-trust + Schedule + Config-read** — fills in cross-cutting evidence.
- Each extractor is project-level (operates on the union of tracked repos). Project-local first; the framework absorbs the patterns that generalize.

### Phase 5: Logigraph claim targets

- Allow rule claims against Layer-3 edge ids.
- Backfill rules that today wait on substrate gaps in any tracked project.

Phases 1–3 are framework work. Phases 4–5 may need framework support but per-edge extractors can ship under the project-local pattern first and migrate upstream once stable.

## Open questions

1. **Parity strategy.** ~~Existing parity fixtures lock layer-1 + layer-2 output…~~ **Resolved 2026-05-16:** no backward-compatibility constraint. The `tests/extractors/test_pre_flip_parity.py` gate and its 8 `pre_flip_nodes/*.json` fixtures are retired. Concorda's depgraph corpus is regenerated from scratch once the new pipeline lands; logigraph claims become stale en masse and are re-authored (or auto-rewritten via reconcile where the new `structural_hash` matches). New fixtures are seeded from the first clean phase-1 regen and lock the layered model going forward.
2. **Persistence model for derived nodes.** **Resolved 2026-05-16:** option (a) — write derived nodes to disk under kind-dirs. Classifier replaces today's extractor as the writer; graphui's file-read model is unchanged. Lazy derivation (option b) stays reachable later if classifier iteration becomes painful.
3. **Migration-attribute granularity.** A migration's `up_operations[]` could list each statement-as-primitive (one function call per CREATE / ALTER), or aggregate into one "migration step." The former is more powerful for rule claims; the latter is simpler. Lean toward statement-as-primitive but resolve in phase 1 of SQL extractor work — out of scope for the first implementation pass (see "Implementation scope" below).

## Implementation scope (added 2026-05-16)

First implementation pass: **JavaScript, TypeScript, Python only.** The full language registry (Go, Rust, C, C++, SQL, JSON Schema, Prisma, OpenAPI, GraphQL, Protobuf) stays the architectural target but does not ship in this pass. System-layer (L3) extractors and logigraph L3-claim support land after L1 + L2 + L3-classification on the JS/TS/Python substrate is stable.

Phases for this pass:

1. **L1 primitive extractors** — JS/TS (ts-morph) and Python (stdlib `ast`) emit the five primitives with full attribute set. Class methods, class fields, top-level functions, top-level variables, module + package primitives. No kind decisions.
2. **L2 edge layer** — defines / extends / implements / calls / instantiates / references / reads / assigns / decorates / imports / tests. `includes` not relevant (no C/C++ in scope). Resolution `exact` only at launch.
3. **L3 derived classification** — classification engine over (primitives + L2 edges) producing component / hook / endpoint / controller / service / model / schema / util / test. Service classification under JS/TS/Python uses available evidence (db client patterns, http client patterns, queue SDK patterns) emitted as a thin L3 stub specifically for classifier consumption; full L3 system edges are a later pass.

## Decision points

Before phase 1 starts, the following must resolve:

- [x] Parity strategy — resolved (drop the gate; regen from scratch)
- [x] Persistence model for derived nodes — resolved (option a, disk kind-dirs)
- [x] Implementation language scope — resolved (JS/TS/Python first)

Open question 3 resolves later, alongside the SQL extractor work that is out of scope here.
