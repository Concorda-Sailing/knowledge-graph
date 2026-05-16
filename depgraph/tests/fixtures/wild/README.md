# Wild corpus — synthetic-pathological test fixtures

These fixtures aren't representative of any specific project. They're hand-crafted to exercise the corners of the framework — patterns that would break a naive extractor. Concorda is the framework's *first consumer*, not its test case; the wild corpus is what proves the framework correct.

## Layout

Each fixture directory contains:
- `README.md` — what's tested + why this pattern is tricky
- `src/` — source file(s); typically small (one file, <60 lines)
- `expected.json` — ground truth: primitive ids + edges + classification decisions
- `verification.md` — reviewer's log (see template in plan)

**`repo-path` convention.** The test harness passes the *fixture root* (NOT `fixture/src`) as `--repo-path`. The extractor walks recursively, so source files at `<fixture>/src/foo.ts` are emitted with path `src/foo.ts` and ids like `fixture::src/foo.ts::Bar`. This convention is identical across all phases (TS, Python, SQL). Fixture authors: write your `expected.json` ids with the `src/` prefix.

## Inventory

### Phase 1 — TS primitives (primitives_ts/)
- anonymous_zoo — default-exported anonymous functions + named function expressions
- overload_storm — function with 5 overload declarations + 1 impl; class with same
- name_collisions — same name as instance method, static method, class field, type alias
- decorator_stack — 3+ stacked decorators incl. parameterized
- generics_constraints — generic class with constrained type params + generic methods
- jsx_corners — memo + forwardRef wrapping, conditional null returns, JSX never returned
- tsconfig_paths_complex — overlapping path aliases, nested aliases
- re_export_chain — barrel → barrel → impl, 3 hops

### Phase 2 — Python primitives (primitives_py/)
- dunder_zoo — __init_subclass__, __set_name__, __class_getitem__, properties
- metaclasses — metaclass=ABCMeta, class Bar(type), dynamic __new__
- dataclass_pydantic_namedtuple — three coexisting with overlapping fields
- nested_everything — class-in-class-in-function, function-in-class-in-function
- decorator_factories — @functools.wraps-decorated, parameterized, stacked
- walrus_match_pep695 — walrus + match/case + PEP 695 generics
- if_name_main — module-level state inside if __name__ == "__main__" (should NOT extract); dynamic class via type()
- relative_dots — `from ...pkg.sub import X` (multi-level relative)

### Phase 3 — L2 edges (edges/) — 9 fixtures
- method_call_chains — client.users.get().filter().first() chained calls
- instance_passing — function takes typed param, calls method on it
- dynamic_dispatch — getattr/setattr-style calls, computed callees → unresolved
- monkey_patch — SomeClass.method = lambda — patched method exists at runtime
- circular_imports_py — A imports B imports A
- circular_imports_ts — same shape, TS
- conditional_rebinding — `if x: s = A() else: s = B(); s.do_work()` — v0 walk-order semantics produce last-assign-wins; fixture pins this (wrong-but-deterministic) behavior so a future flow-sensitive pass has a regression target
- decorator_target_resolution — decorator from external lib vs local
- read_assign_global — module-scope variable read in fn-A, assigned in fn-B

### Phase 4 — SQL + schema (sql/)
- multi_dialect_create — postgres SERIAL, mysql AUTO_INCREMENT, sqlite AUTOINCREMENT
- alembic_op_style — uses op.create_table instead of text()
- bare_sql_file — standalone .sql with multiple CREATE TABLE
- self_referential_fk — node.parent_id REFERENCES node(id)
- circular_fk — A → B → A
- mixed_text_and_op — migration using both text() and op.* calls
- dynamic_sql_warning — only f-string interpolated SQL → warnings, no schema
- alter_replay_chain — CREATE → ALTER ADD → ALTER TYPE → RENAME → DROP COLUMN; final state matters

### Phase 5 — Classification (classification/)
- endpoint_AND_service_conflict — route-decorated function that also does db_access
- hook_calling_hook_chain — useFoo → useBar → useState
- component_HOC_wrapped — memo(forwardRef(({...}) => <div/>))
- pseudo_test_not_test — function named test_thing outside test path + no asserts
- orphan_model — class extends Base but no __tablename__
- model_without_schema — class with __tablename__ but no matching schema primitive
- util_deep_transitive — endpoint → util A → util B → util C; all must classify
- classification_conflict_logged — function satisfying two kinds; conflict recorded

### Kitchen sink (kitchen_sink/) — structurally distinct

Unlike the per-phase fixtures above (each focused on one pattern), the kitchen-sink is a single assembled mini-project covering all kinds. It has its own internal structure (`api/`, `web/`, `db/` subdirs) instead of the standard `src/` layout, and a single `expected.json` capturing the corpus-wide kind distribution + invariants.

- ~30 files across api/, web/, db/. Distribution: 5 endpoints, 4 services, 6 utils, 2 hooks, 3 components, 8 schemas, 5 models, 4 tests. End-to-end gate before Concorda regen.
