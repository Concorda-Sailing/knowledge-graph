# Known Limitations — Depgraph Layered Substrate v0

This document is the canonical index of every v0-acceptable gap surfaced during Phases 1–5 of the layered-substrate rewrite. Each entry represents **deliberately pinned behavior**: the wild-corpus fixture asserts the current output exactly, so the entry here is also the description of what the tests enforce. Changing the implementation to close a gap requires first updating the relevant fixture's `expected.json` and `verification.md`, then removing or updating the entry here. Do not treat these as silent bugs — they are known trade-offs accepted for v0 with documented triggers for when they become worth investing in.

---

## Layer 1 — TypeScript Extractor

### TS-1: `bodyHasJsx` counts JSX anywhere in body, not just in return expressions

**Layer:** Extractor (TypeScript)
**Where pinned:** `depgraph/tests/fixtures/wild/primitives_ts/jsx_corners/`
**Current behavior:** `bodyHasJsx` scans all descendants of a function body. If JSX appears anywhere — including inside a variable initializer that is never returned — `returns_jsx` is set to `true`. A function like `sideEffectRender` that contains `const el = <span/>` inside its body but whose return type is `void` will still emit `returns_jsx=true`.
**Ideal behavior:** `returns_jsx` would be true only when JSX appears in a return expression (or the implicit return of an arrow function). A side-effect-only renderer that creates but doesn't return JSX would emit `returns_jsx=false`.
**Trigger for fixing:** When the classifier needs to distinguish "renders JSX as output" from "creates JSX as a side effect." In practice this matters if React server actions or portal renders become common enough that the over-detection produces mis-classifications.

---

### TS-2: `React.memo(...)` HOC wrapper emits outer binding as a variable, not a component

**Layer:** Extractor (TypeScript)
**Where pinned:** `depgraph/tests/fixtures/wild/primitives_ts/jsx_corners/` and `depgraph/tests/fixtures/wild/classification/component_HOC_wrapped/`
**Current behavior:** `const Card = React.memo(...)` has a `CallExpression` initializer. `extractFunctions` requires an `ArrowFunction` or `FunctionExpression` initializer; `extractVariables` skips those but keeps CallExpression. So `Card` emits as a `variable` primitive with no `returns_jsx`. The inner function argument passed to `memo()` is not synthesized as a named primitive (unless it happens to be named inline). The outer `Card` variable, which is the public export, does not classify as a component.
**Ideal behavior:** The extractor would recognize `React.memo(fn)`, `React.forwardRef(fn)`, and similar HOC wrappers and either unwrap to the inner function or emit the outer variable with an HOC annotation that the classifier can use to apply the inner function's `returns_jsx`.
**Trigger for fixing:** When the corpus contains enough HOC-wrapped components that mis-classification rate is observable in the kind-dirs output, or when the graph-query layer needs to answer "which variables are components?"

---

### TS-3: Method-level type parameters not captured in `template_parameters`

**Layer:** Extractor (TypeScript)
**Where pinned:** `depgraph/tests/fixtures/wild/primitives_ts/generics_constraints/`
**Current behavior:** Class-level `template_parameters` are captured correctly (e.g. `Repository<TEntity, TKey>` → `["TEntity", "TKey"]`). Method-level type parameters on an otherwise non-generic class method (e.g. `transform<TIn, TOut>()`) are not captured; `attributes.template_parameters` stays `[]` on the method primitive.
**Ideal behavior:** `signature.template_parameters` on the function primitive would reflect method-level type params: `["TIn", "TOut"]`.
**Trigger for fixing:** When downstream uses (e.g. inference passes, documentation generation) need to reason about generic method signatures.

---

### TS-4: Constructor parameter properties not extracted as class fields

**Layer:** Extractor (TypeScript)
**Where pinned:** `depgraph/tests/fixtures/wild/primitives_ts/overload_storm/`
**Current behavior:** `private locale: string` declared inside a constructor's parameter list (TypeScript parameter property shorthand) is not accessible via `cls.getProperties()` in ts-morph. The extractor only walks `getProperties()` for class fields. These properties are invisible — no variable primitive is emitted for them.
**Ideal behavior:** Constructor parameter properties would be detected via `ctor.getParameters().filter(p => p.isParameterProperty())` and emitted as variable primitives owned by the class.
**Trigger for fixing:** When graph queries need to enumerate all fields of a class, including those declared in constructors. Particularly relevant for Angular-style DI where all dependencies are parameter properties.

---

## Layer 2 — Python Extractor

### PY-1: Function-local nested classes and functions not extracted

**Layer:** Extractor (Python)
**Where pinned:** `depgraph/tests/fixtures/wild/primitives_py/nested_everything/`
**Current behavior:** Classes and functions defined inside the body of a `FunctionDef` are not extracted as primitives. The extractor emits the outer function but does not recurse into its body for further definitions. `LocalClass`, `local_helper`, `FuncLocal`, and `nested_def` inside function bodies are absent from the graph.
**Ideal behavior:** A future pass would track closure-scoped and function-local definitions, enabling analysis of factory functions, class decorators that return classes, and similar patterns.
**Trigger for fixing:** When closure-scope tracking becomes necessary for a specific analysis. The cost is significant (exponential id-namespace growth for deeply nested patterns) so this is a deliberate scope limit, not a latent bug.

---

### PY-2: `if __name__ == "__main__":` block contents not extracted (intentional)

**Layer:** Extractor (Python)
**Where pinned:** `depgraph/tests/fixtures/wild/primitives_py/if_name_main/`
**Current behavior:** Definitions inside an `if __name__ == "__main__":` block are not extracted. `GUARDED_CONSTANT`, `GuardedClass`, and `guarded_helper` inside the guard are absent. `_walk_module_body` iterates only `tree.body` top-level statements; the `If` body is not descended.
**Ideal behavior:** This is intentional and correct. Guarded blocks run only when the file is the entry point, not when imported. Emitting them as module primitives would produce phantom nodes for modules that are both importable and executable. No change planned.
**Trigger for fixing:** N/A — this is correct behavior.

---

### PY-3: Walrus operator bindings and `If`-body assigns not extracted (intentional)

**Layer:** Extractor (Python)
**Where pinned:** `depgraph/tests/fixtures/wild/primitives_py/walrus_match_pep695/`
**Current behavior:** `NamedExpr` (walrus `:=`) nodes are never `Assign` or `AnnAssign`, so walrus bindings are invisible regardless of where they appear. Assign/AnnAssign nodes inside an `If` body are also not extracted because `_walk_module_body` only iterates `tree.body` (the top-level statement list). `VERSION_MAJOR` and `VERSION_MINOR` bound inside a walrus-guarded `If` block are absent.
**Ideal behavior:** This is intentional. These assignments only execute conditionally; emitting them as module primitives would imply unconditional availability. No change planned.
**Trigger for fixing:** N/A — this is correct behavior.

---

### PY-4: `type()` dynamic class emits as a variable primitive

**Layer:** Extractor (Python)
**Where pinned:** `depgraph/tests/fixtures/wild/primitives_py/if_name_main/`
**Current behavior:** `DynConfig = type("DynConfig", (), {...})` is an `Assign` node whose target is a bare `Name`. The extractor emits it as a `variable` primitive with `value_text` capturing the full right-hand expression. No class primitive is created.
**Ideal behavior:** A future classifier or extractor post-pass would detect `value_text` matching `type(<name>, ...)` and either annotate the variable primitive as a dynamically-created class or emit an auxiliary class primitive.
**Trigger for fixing:** When corpus analysis reveals enough `type()`-created classes that they need to participate in class-level graph queries (extends, instantiates edges, etc.).

---

## Layer 3 — Edge Resolution (Python)

### EDGE-1: Monkey-patching does not redirect existing `calls` edges

**Layer:** Edges (Python)
**Where pinned:** `depgraph/tests/fixtures/wild/edges/monkey_patch/`
**Current behavior:** `SomeClass.method = lambda self, x: x * 2` at module level performs a runtime attribute replacement. The extractor does not model this. Calls to `obj.method(5)` where `obj: SomeClass` resolve to the original `SomeClass.method` primitive (the one defined in the class body), not the lambda. Additionally, lambda nodes (`ast.Lambda`) are never extracted as function primitives — the patching assignment's target is an `ast.Attribute`, which `_variable_primitives` skips.
**Ideal behavior:** A flow-sensitive or module-level assignment pass would detect `ClassName.method = <expr>` patterns and update the edge table so that subsequent calls resolve to the patched target. The lambda itself would be extracted under a synthesized name.
**Trigger for fixing:** When the corpus contains enough monkey-patching (common in test doubles, plugin systems, and old-style Python extensions) that undetected patches cause observable analysis errors.

---

### EDGE-2: Chained method calls `a.b.c()` dropped silently (no unresolved edge)

**Layer:** Edges (Python)
**Where pinned:** `depgraph/tests/fixtures/wild/edges/method_call_chains/`
**Current behavior:** `client.users.get().filter().first()` — when `call.func` is an `ast.Attribute` whose `value` is itself an `ast.Attribute` (not a bare `ast.Name`), `_resolve_call_edge` returns `[]`. No edge — not even an unresolved one — is emitted. The chain is silently dropped.
**Ideal behavior:** At minimum, an unresolved edge would be emitted for each chained call so the graph acknowledges that a call occurred. A more complete implementation would attempt to chase the chain by tracking intermediate attribute types.
**Trigger for fixing:** When graph queries produce "dangling call sites" diagnostics and chained calls are a significant source of noise. The silent drop currently prevents over-claiming but loses signal.

---

### EDGE-3: Decorator-list nodes in body walk produce spurious `calls` edges

**Layer:** Edges (Python)
**Where pinned:** `depgraph/tests/fixtures/wild/edges/decorator_target_resolution/`
**Current behavior:** `_attach_call_edges` uses `ast.walk(fn_node)` to find `Call` nodes. When a function is decorated, the decorator expression is part of the function's AST subtree and is visited by the walk. This can cause the decorated function itself to appear as if it calls its own decorators, producing a `calls` edge that should instead be a `decorates` edge. The current implementation works around this for the simple decorator case tested in the fixture, but the underlying walk boundary is not enforced.
**Ideal behavior:** `_attach_call_edges` would exclude the decorator list from its walk (or `_attach_decorator_edges` would mark those calls as already-handled so the call edge pass skips them).
**Trigger for fixing:** When corpus analysis shows functions with false self-referential `calls` edges due to decorator expressions. Most commonly surfaces with parameterized decorators.

---

### EDGE-4: Conditional rebinding — last-assign-wins via `ast.walk` BFS order (intentionally pinned wrong)

**Layer:** Edges (Python)
**Where pinned:** `depgraph/tests/fixtures/wild/edges/conditional_rebinding/`
**Current behavior:** In `if x: s = A() else: s = B(); s.do_work()`, both assignments are visited by `ast.walk`. BFS order visits `if.body[0]` (s=A) before `if.orelse[0]` (s=B), so `var_types["s"]` ends up as `B`. The `calls` edge targets `B.do_work`, which is wrong at runtime when the `if` branch executes. This is deterministic but incorrect behavior.
**Ideal behavior:** A flow-sensitive analysis would model both branches and emit two `calls` edges (one to `A.do_work`, one to `B.do_work`) to cover both paths, or model the join point correctly.
**Trigger for fixing:** When flow-sensitive analysis (dataflow / SSA) is added to the edge-resolution layer. This fixture is explicitly the regression target for that future pass — do not "fix" the test without implementing the full flow-sensitive pass.

---

### EDGE-5: Dynamic dispatch via computed callees (`getattr(obj, name)()`) dropped or emits to synthetic target

**Layer:** Edges (Python)
**Where pinned:** `depgraph/tests/fixtures/wild/edges/dynamic_dispatch/`
**Current behavior:** When `call.func` is itself a `Call` expression (computed callee, e.g. `getattr(obj, name)()`), `_resolve_call_edge` emits an unresolved edge to `external::unresolved::computed_callee`. When the callee is a bare `Name` not in `local_names` (e.g. a builtin like `getattr` called standalone), `[]` is returned. In both cases the true dispatch target is unknown.
**Ideal behavior:** At minimum, a consistent unresolved edge with a meaningful `via` field. A more complete implementation would recognize `getattr(obj, name)` as a dynamic dispatch pattern and emit a `db_access`-style fuzzy annotation.
**Trigger for fixing:** When dynamic dispatch patterns become frequent enough to distort the graph (e.g. in plugin registries, ORMs, or middleware chains).

---

## Layer 3 — Edge Resolution (TypeScript)

### EDGE-6: `tests` edges require `ast.Assert` ancestor — `unittest.TestCase.assertEqual` and chai `assert.equal` not detected

**Layer:** Edges (Python/TypeScript — test-edge recognition)
**Where pinned:** Plan spec Task 3.6; fixture at `depgraph/tests/extractors/fixtures/edges_py/tests/`
**Current behavior:** The Python `tests`-edge recognizer walks up from a `Call` node looking for an `ast.Assert` ancestor. `unittest`-style assertions (`self.assertEqual(add(1, 2), 3)`) are method calls on `self`, not `ast.Assert` nodes. They are not recognized as assertion contexts, so calls inside them do not produce `tests` edges. Similarly, the TS recognizer looks for an `expect(...)` wrapper; chai-style `assert.equal(...)` calls are not currently detected.
**Ideal behavior:** The assertion-scope check would include a known-framework-call list: `self.assert*`, `self.expect*` (unittest), `assert.equal`, `assert.ok`, `expect(...).to.*` (chai). Any of these would qualify as an assertion scope for the enclosed calls.
**Trigger for fixing:** When the corpus contains a codebase using unittest or chai heavily enough that its test coverage graph is meaningfully incomplete.

---

## Layer 4 — SQL Pipeline

### SQL-1: Alembic `op.*`-style migration files not parsed

**Layer:** SQL (migration recognition)
**Where pinned:** `depgraph/tests/fixtures/wild/sql/alembic_op_style/`
**Current behavior:** `is_migration_file()` checks for a `text()` call in the Python AST (the SQLAlchemy 2.x pattern where raw SQL is wrapped in `text(...)`). Alembic files use `op.create_table(...)`, `op.add_column(...)`, etc. — no `text()` call — so `is_migration_file()` returns `False`. The file is filtered out before `extract_migration` runs. Result: 0 tables extracted, test skips.
**Ideal behavior:** A parallel Alembic-aware migration recognizer would detect `from alembic import op` or `op.create_table` patterns and extract schema operations from the Alembic DSL rather than from embedded SQL strings.
**Trigger for fixing:** When the corpus includes Alembic migrations. Deferred until a corpus using the Alembic DSL is onboarded.

---

### SQL-2: Standalone `.sql` files not extracted (no v0 extractor)

**Layer:** SQL (file coverage)
**Where pinned:** `depgraph/tests/fixtures/wild/sql/bare_sql_file/`
**Current behavior:** The SQL pipeline only processes Python files that contain embedded SQL strings (via `rglob("*.py")`). Pure `.sql` files (schema dumps, hand-written DDL) are not found. Test skips because `rglob("*.py")` yields nothing for a `.sql`-only `src/` tree.
**Ideal behavior:** A standalone `.sql` extractor would be registered in `languages.toml` and would process `.sql` files directly through the sqlglot parser, extracting table/column/FK primitives from DDL.
**Trigger for fixing:** When a corpus contains significant hand-written SQL schema files outside the Python migration layer.

---

### SQL-3: `db_access` fallback — unknown receiver type targets `external::unresolved::db_target`

**Layer:** SQL / System stub (db_access)
**Where pinned:** Plan spec Task 4.6; `depgraph/lib/system_stub/db_access.py`
**Current behavior:** When the `db_access` recognizer sees `session.query(X)` or `db.add(x)` but cannot resolve `X` to a Python class primitive with a `references → schema` edge (either because `X` is not in the local symbol table, or because no schema primitive exists for the referenced table), it emits a `db_access` edge with `target = "external::unresolved::db_target"` and `confidence = "unresolved"`. The true schema table is unknown.
**Ideal behavior:** A more complete resolver would follow import chains, check transitive `references` edges, and attempt fuzzy matching by class name against schema primitives before falling back to the unresolved sentinel.
**Trigger for fixing:** When graph queries produce too many `external::unresolved::db_target` entries to be useful, or when a specific corpus has a well-known ORM pattern that could be resolved with a targeted heuristic.

---

## Layer 5 — Classification

### CLS-1: `endpoint + service` cannot conflict by design

**Layer:** Classification (classifier engine)
**Where pinned:** `depgraph/tests/fixtures/wild/classification/endpoint_AND_service_conflict/`
**Current behavior:** A function with a `@router.get` decorator (endpoint predicate fires) that also issues a direct `db_access` call (which would satisfy the service side-effect requirement) classifies as `endpoint` with an empty `conflicts` list. The service classifier guards with `if p["id"] in endpoints: continue` — it never evaluates a node already classified as an endpoint, so no conflict decision is ever recorded.
**Ideal behavior:** This is intentional and correct. An endpoint that directly queries the database is still an endpoint, not a service. The guard exists precisely to prevent this false conflict. No change planned.
**Trigger for fixing:** N/A — this is correct behavior by design.

---

### CLS-2: Hook chain one-hop limitation — transitive `use<Hook>` chains not fully resolved

**Layer:** Classification (hook classifier)
**Where pinned:** `depgraph/tests/fixtures/wild/classification/hook_calling_hook_chain/`
**Current behavior:** The hook classifier fires when a `use<Capital>` function directly calls a known external React hook (e.g. `useState`, `useEffect`). In the chain `useFoo → useBar → useState`: `useBar` calls `useState` (external) directly → classifies as hook. `useFoo` calls `useBar` (a local user-defined function) → `useBar`'s id is not in `known_hook_externals` → `useFoo` does not classify as hook.
**Ideal behavior:** A second-pass propagation would re-examine all `use<Capital>` functions after the first pass, and if any of their callees are now classified as `hook`, also classify them as `hook`. Repeat until stable. This is acknowledged in `hook.py` line 29–30 and deferred to Task 5.7.
**Trigger for fixing:** Task 5.7 — the second-pass hook propagation. At that point, `expected.json` for this fixture should be updated to include `useFoo = hook`.

---

### CLS-3: HOC-wrapped components — outer variable invisible to classifier

**Layer:** Classification (component classifier)
**Where pinned:** `depgraph/tests/fixtures/wild/classification/component_HOC_wrapped/`
**Current behavior:** The component classifier only considers `function` primitives (requires `primitive == "function"`, `name[0].isupper()`, and `returns_jsx == True`). `const Card = memo(forwardRef(...))` emits `Card` as a `variable` primitive. The classifier never examines variables, so `Card` stays `kind = None`. If the fixture includes a named inner function (`CardInner`), that inner function classifies as `component`. The public export name `Card` does not.
**Ideal behavior:** The classifier would detect HOC patterns on variable primitives (`value_text` starts with known HOC calls: `memo(`, `forwardRef(`, `connect(`, etc.) and propagate the `component` kind from the inner function to the outer variable.
**Trigger for fixing:** When graph queries need to look up components by their public export name (which is the HOC-wrapped variable) rather than by the inner function name. Common when analyzing component import/usage patterns.

---

## How to Add to This List

Adding a known limitation has a fixed protocol:

1. **Fixture first.** Pin the behavior in a wild fixture: create or update `expected.json` to assert the current (imperfect) output, and write a `verification.md` that explicitly calls out the behavior as a v0 known limitation and why it is acceptable.
2. **Then add an entry here.** Copy the entry template (Name, Layer, Where pinned, Current behavior, Ideal behavior, Trigger for fixing) and append it to the relevant layer section.
3. **Commit both in the same unit.** The fixture change and the doc change are one commit. The commit message should name the limitation slug.

When a limitation is **fixed**:
1. Update the fixture's `expected.json` to the correct output.
2. Update or delete the fixture's `verification.md` limitation note.
3. Remove the entry from this doc (or move it to a "Fixed in vN" appendix if historical tracing is useful).
4. Commit all three changes together.
